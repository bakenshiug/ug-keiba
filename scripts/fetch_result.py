#!/usr/bin/env python3
"""
fetch_result.py — netkeiba の結果ページから着順＆払戻を取得し、
race-notes.presentation.result に格納する。

Usage:
  python3 scripts/fetch_result.py 2026-04-25-tokyo-11r
  python3 scripts/fetch_result.py --day 2026-04-25
  python3 scripts/fetch_result.py --all
"""
import urllib.request, re, json, sys, argparse, os
from pathlib import Path
from datetime import datetime

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'

# 払戻テーブル class名 → 内部キー
PAYOUT_KEY_MAP = {
    'Tansho':     'tan',
    'Fukusho':    'fuku',
    'Wakuren':    'wakuren',
    'Umaren':     'umaren',
    'Wide':       'wide',
    'Umatan':     'umatan',
    'Fuku3':      'sanrenpuku',
    'Tan3':       'sanrentan',
}


def fetch_html(race_id):
    url = f'https://race.netkeiba.com/race/result.html?race_id={race_id}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('euc-jp', errors='replace')


def _txt(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


def parse_horses(html):
    """着順テーブルから全頭の結果を抽出"""
    horses = []
    rows = re.findall(r'<tr\s+class="[^"]*HorseList[^"]*"[^>]*>(.*?)</tr>', html, re.S)
    for row in rows:
        rank   = re.search(r'class="Rank">([^<]+)</div>', row)
        gate   = re.search(r'class="Num\s+Waku(\d+)"', row)
        num    = re.search(r'class="Num Txt_C">\s*<div>(\d+)</div>', row)
        name   = re.search(r'<span class="HorseNameSpan">\s*([^<\n]+?)\s*</span>', row)
        sexAge = re.search(r'class="Lgt_Txt[^"]*">\s*([^<\s]+)\s*</span>', row)
        kg     = re.search(r'class="JockeyWeight">\s*([^<]+?)\s*</span>', row)
        jockey = re.search(r'class="JockeyNameSpan">\s*([^<\n]+?)\s*</span>', row)
        time   = re.search(r'class="RaceTime">\s*([^<]*?)\s*</span>', row)
        ninki  = re.search(r'class="OddsPeople">\s*([^<]+?)\s*</span>', row)
        # 単勝オッズは <td class="Odds Txt_R"><span ...>X.Y</span></td>
        # 上位人気で class="Odds_Ninki" がつく馬と、つかない馬の両方に対応
        odds_td = re.search(r'<td class="Odds Txt_R"[^>]*>(.*?)</td>', row, re.S)
        odds = re.search(r'<span[^>]*>\s*([\d\.]+)\s*</span>', odds_td.group(1)) if odds_td else None
        last3F = re.search(r'class="Time BgOrange[^"]*">\s*([^<]+?)\s*</td>', row)
        trainer = re.search(r'class="TrainerNameSpan">\s*([^<\n]+?)\s*</span>', row)
        weight = re.search(r'class="Weight">\s*([^<]+?)\s*<small>([^<]+)</small>', row)
        horses.append({
            'rank':   (rank.group(1).strip()   if rank   else ''),
            'gate':   (gate.group(1)            if gate   else ''),
            'num':    (num.group(1)             if num    else ''),
            'name':   (name.group(1).strip()    if name   else ''),
            'sexAge': (sexAge.group(1).strip()  if sexAge else ''),
            'kinryo': (kg.group(1).strip()      if kg     else ''),
            'jockey': (jockey.group(1).strip()  if jockey else ''),
            'time':   (time.group(1).strip()    if time   else ''),
            'finalNinki': (ninki.group(1).strip() if ninki else ''),
            'finalOdds':  (odds.group(1).strip()  if odds  else ''),
            'last3F': (last3F.group(1).strip()  if last3F else ''),
            'trainer':(trainer.group(1).strip() if trainer else ''),
            'weight': (weight.group(1).strip() + weight.group(2) if weight else ''),
        })
    return horses


def parse_payouts(html):
    """払戻テーブルから全券種データを抽出"""
    out = {}
    for tbl in re.findall(r'<table[^>]*class="Payout_Detail_Table"[^>]*>(.*?)</table>', html, re.S):
        for cls, body in re.findall(r'<tr class="(\w+)"[^>]*>(.*?)</tr>', tbl, re.S):
            key = PAYOUT_KEY_MAP.get(cls)
            if not key:
                continue
            result_m = re.search(r'<td class="Result"[^>]*>(.*?)</td>', body, re.S)
            payout_m = re.search(r'<td class="Payout"[^>]*>(.*?)</td>', body, re.S)
            ninki_m  = re.search(r'<td class="Ninki"[^>]*>(.*?)</td>', body, re.S)
            if not (result_m and payout_m):
                continue

            # Result：netkeiba構造
            #   単勝/枠連/馬連等：<div><span>馬番</span></div> 1個
            #   複勝/ワイド等：複数組み合わせを <ul>...</ul> ごとに分け、
            #                  各 ul 内に <li><span>馬番</span></li> が並ぶ
            #   3連複/3連単：同様
            r_html = result_m.group(1)
            ul_blocks = re.findall(r'<ul[^>]*>(.*?)</ul>', r_html, re.S)
            if ul_blocks:
                r_items = ul_blocks
            else:
                r_items = [r_html]

            # 配当（円のついた数字）と人気
            amts = [int(a.replace(',','')) for a in re.findall(r'([\d,]+)\s*円', _txt(payout_m.group(1)))]
            pops = [int(x) for x in re.findall(r'(\d+)\s*人気', _txt(ninki_m.group(1)) if ninki_m else '')]

            picks = []
            for idx, r in enumerate(r_items):
                nums = re.findall(r'<span[^>]*>(\d+)</span>', r)
                if not nums:
                    continue
                picks.append({
                    'combo':  nums,
                    'amount': amts[idx] if idx < len(amts) else None,
                    'ninki':  pops[idx] if idx < len(pops) else None,
                })
            out[key] = picks
    return out


def update_race_notes(race_key):
    path = RN_DIR / f'{race_key}.json'
    if not path.exists():
        print(f"  ⚠ NOT FOUND: {path}")
        return False
    d = json.load(open(path))
    pres = d.get('presentation', {})
    race_id = pres.get('raceId')
    if not race_id:
        print(f"  ⚠ raceId 未設定: {race_key}")
        return False

    try:
        html = fetch_html(race_id)
    except Exception as e:
        print(f"  ✗ fetch失敗 {race_key}: {e}")
        return False

    horses  = parse_horses(html)
    payouts = parse_payouts(html)

    if not horses:
        print(f"  ⚠ 着順データなし {race_key}（未確定の可能性）")
        return False

    pres['result'] = {
        'fetched': datetime.now().isoformat(timespec='seconds'),
        'raceId':  race_id,
        'horses':  horses,
        'payouts': payouts,
    }
    d['presentation'] = pres
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    name = d.get('race', {}).get('name', '?')
    win  = horses[0] if horses else {}
    print(f"  ✓ {race_key:<32} {name:<22} 1着={win.get('name','?')}({win.get('finalOdds','?')}倍/{win.get('finalNinki','?')}人気) wide={len(payouts.get('wide',[]))}点")
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('race_key', nargs='?')
    ap.add_argument('--day',  help='例: 2026-04-25')
    ap.add_argument('--all',  action='store_true')
    args = ap.parse_args()

    if args.all:
        keys = [p.stem for p in sorted(RN_DIR.glob('*.json'))
                if not any(p.name.endswith(s) for s in ['.bak','.bak2','.bak3','.bak4'])]
    elif args.day:
        keys = [p.stem for p in sorted(RN_DIR.glob(f'{args.day}-*.json'))
                if not any(p.name.endswith(s) for s in ['.bak','.bak2','.bak3','.bak4'])]
    elif args.race_key:
        keys = [args.race_key]
    else:
        ap.print_help()
        sys.exit(0)

    ok = 0
    for k in keys:
        if update_race_notes(k):
            ok += 1
    print(f"\n完了: {ok}/{len(keys)} レース")
