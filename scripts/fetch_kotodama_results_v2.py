#!/usr/bin/env python3
"""
fetch_kotodama_results_v2.py — 言霊神宮 全レース結果取得＆回収率計算（新買い方ルール）

新ルール:
  ⛩️ 単勝◎  1点(¥100) + 馬単マルチ◎軸→{○▲激} 6点(¥600) = 7点 ¥700/R
  🌕 単勝激  1点(¥100) + 馬単マルチ激軸→{◎○▲} 6点(¥600) = 7点 ¥700/R
  合計: 14点 ¥1,400/R

race_idは 2026-05-16.json の各 race.raceId (netkeiba形式) をそのまま使用。
"""

import urllib.request, re, json, argparse
from pathlib import Path
from datetime import datetime
from itertools import permutations

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
ROOT = Path(__file__).resolve().parent.parent
KT_DIR = ROOT / 'docs/data/kotodama-test'

MARK_ORDER = {'◎': 0, '○': 1, '▲': 2, '激': 3}


def fetch_html(race_id: str) -> str:
    url = f'https://race.netkeiba.com/race/result.html?race_id={race_id}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('euc-jp', errors='replace')


def _txt(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


def parse_horses(html: str) -> list:
    horses = []
    rows = re.findall(r'<tr\s+class="[^"]*HorseList[^"]*"[^>]*>(.*?)</tr>', html, re.S)
    for row in rows:
        rank  = re.search(r'class="Rank">([^<]+)</div>', row)
        num   = re.search(r'class="Num Txt_C">\s*<div>(\d+)</div>', row)
        name  = re.search(r'<span class="HorseNameSpan">\s*([^<\n]+?)\s*</span>', row)
        ninki = re.search(r'class="OddsPeople">\s*([^<]+?)\s*</span>', row)
        horses.append({
            'rank':       rank.group(1).strip()    if rank  else '',
            'num':        num.group(1)              if num   else '',
            'name':       name.group(1).strip()     if name  else '',
            'finalNinki': ninki.group(1).strip()    if ninki else '',
        })
    return horses


def parse_payouts(html: str) -> dict:
    PAYOUT_KEY_MAP = {'Tansho': 'tan', 'Fukusho': 'fuku', 'Umatan': 'umatan'}
    out = {}
    for tbl in re.findall(r'<table[^>]*class="Payout_Detail_Table"[^>]*>(.*?)</table>', html, re.S):
        for cls, body in re.findall(r'<tr class="(\w+)"[^>]*>(.*?)</tr>', tbl, re.S):
            key = PAYOUT_KEY_MAP.get(cls)
            if not key:
                continue
            result_m = re.search(r'<td class="Result"[^>]*>(.*?)</td>', body, re.S)
            payout_m = re.search(r'<td class="Payout"[^>]*>(.*?)</td>', body, re.S)
            if not (result_m and payout_m):
                continue
            r_html = result_m.group(1)
            ul_blocks = re.findall(r'<ul[^>]*>(.*?)</ul>', r_html, re.S)
            r_items = ul_blocks if ul_blocks else [r_html]
            amts = [int(a.replace(',', '')) for a in re.findall(r'([\d,]+)\s*円', _txt(payout_m.group(1)))]
            picks = []
            for idx, r in enumerate(r_items):
                nums = re.findall(r'<span[^>]*>(\d+)</span>', r)
                if not nums:
                    continue
                picks.append({
                    'combo':  nums,
                    'amount': amts[idx] if idx < len(amts) else None,
                })
            out[key] = picks
    return out


def normalize_num(n) -> str:
    """馬番を文字列整数化（"08" → "8"）"""
    try:
        return str(int(n))
    except Exception:
        return str(n)


def calc_new_betting(picks: list, payouts: dict) -> dict:
    """
    新ルール計算:
      ⛩️ 単勝◎(¥100) + 馬単マルチ◎軸6点(¥600)
      🌕 単勝激(¥100) + 馬単マルチ激軸6点(¥600)
    """
    sorted_picks = sorted(picks, key=lambda p: MARK_ORDER.get(p['mark'], 9))
    by_mark = {p['mark']: normalize_num(p['num']) for p in sorted_picks}

    honmei = by_mark.get('◎')
    aite   = [by_mark.get('○'), by_mark.get('▲'), by_mark.get('激')]
    aite   = [x for x in aite if x]

    ana    = by_mark.get('激')
    ana_aite = [by_mark.get('◎'), by_mark.get('○'), by_mark.get('▲')]
    ana_aite = [x for x in ana_aite if x]

    # ── 投資額 ──
    invest = {
        'honmei_tan':   100,
        'honmei_umatan': 600,   # ◎軸マルチ 3相手×2方向=6点
        'ana_tan':      100 if ana else 0,
        'ana_umatan':   600 if ana else 0,  # 激軸マルチ 3相手×2方向=6点
    }
    invest_total = sum(invest.values())

    # ── 払戻 ──
    payout = {k: 0 for k in invest}

    # 単勝◎
    for p in payouts.get('tan', []):
        if honmei and honmei in (p.get('combo') or []):
            payout['honmei_tan'] += p['amount'] or 0

    # 馬単マルチ◎軸
    for p in payouts.get('umatan', []):
        combo = p.get('combo') or []
        if len(combo) < 2:
            continue
        a, b = combo[0], combo[1]
        # ◎→相手 or 相手→◎
        if honmei and ((a == honmei and b in aite) or (b == honmei and a in aite)):
            payout['honmei_umatan'] += p['amount'] or 0

    # 単勝激
    if ana:
        for p in payouts.get('tan', []):
            if ana in (p.get('combo') or []):
                payout['ana_tan'] += p['amount'] or 0

        # 馬単マルチ激軸
        for p in payouts.get('umatan', []):
            combo = p.get('combo') or []
            if len(combo) < 2:
                continue
            a, b = combo[0], combo[1]
            if (a == ana and b in ana_aite) or (b == ana and a in ana_aite):
                payout['ana_umatan'] += p['amount'] or 0

    payout_total = sum(payout.values())
    return {
        'invest': invest,
        'payout': payout,
        'investTotal': invest_total,
        'payoutTotal': payout_total,
        'recovery': round(payout_total / invest_total * 100, 1) if invest_total else 0,
        'honmei': honmei,
        'ana': ana,
    }


def update_race(race: dict, force: bool = False) -> bool:
    race_id = race.get('raceId')
    if not race_id:
        print(f'  ⚠ raceId なし: {race["venue"]}{race["raceNum"]}')
        return False

    try:
        html = fetch_html(race_id)
    except Exception as e:
        print(f'  ✗ fetch失敗 {race_id}: {e}')
        return False

    horses = parse_horses(html)
    payouts = parse_payouts(html)

    if not horses:
        print(f'  ⚠ 着順データなし {race_id}（未確定の可能性）')
        return False

    # picks に人気・着順を付与
    name_to_h = {h['name']: h for h in horses}
    num_to_h  = {h['num']:  h for h in horses}
    for p in race.get('picks', []):
        h = name_to_h.get(p['name']) or num_to_h.get(normalize_num(p.get('num', '')))
        if h:
            p['finalRank']  = h['rank']
            p['finalNinki'] = h['finalNinki']

    bet = calc_new_betting(race['picks'], payouts)

    race['result'] = {
        'fetched':       datetime.now().isoformat(timespec='seconds'),
        'netkeibaRaceId': race_id,
        'horses':        horses[:5],
        'payouts':       payouts,
        'betting':       bet,
        'summary': (
            f"1着 {horses[0]['num']}番 {horses[0]['name']} "
            f"({horses[0]['finalNinki']}人気) | 回収率 {bet['recovery']}%"
        ),
    }

    win = horses[0]
    h_icon = '✓' if bet['payoutTotal'] > 0 else '✗'
    print(
        f"  {h_icon} {race['venue']}{race['raceNum']:>4}  "
        f"1着={win['num']:>2}番 {win['name']:<10} ({win['finalNinki']}人気)"
        f"  投資¥{bet['investTotal']:,} 払戻¥{bet['payoutTotal']:,}  回収率{bet['recovery']}%"
    )
    return True


def aggregate(races: list) -> dict:
    KINDS = ['honmei_tan', 'honmei_umatan', 'ana_tan', 'ana_umatan']
    per = {k: {'inv': 0, 'pay': 0, 'hit': 0, 'races': 0} for k in KINDS}
    tot_inv = tot_pay = 0
    race_hit = 0

    for r in races:
        b = r['result']['betting']
        tot_inv += b['investTotal']
        tot_pay += b['payoutTotal']
        if b['payoutTotal'] > 0:
            race_hit += 1
        for k in KINDS:
            inv = b['invest'].get(k, 0)
            pay = b['payout'].get(k, 0)
            per[k]['inv'] += inv
            per[k]['pay'] += pay
            if inv > 0:
                per[k]['races'] += 1
            if pay > 0:
                per[k]['hit'] += 1

    n = len(races)
    return {
        'racesWithResult': n,
        'racesHit': race_hit,
        'raceHitRate': round(race_hit / n * 100, 1) if n else 0,
        'totalInvest': tot_inv,
        'totalPayout': tot_pay,
        'totalRecovery': round(tot_pay / tot_inv * 100, 1) if tot_inv else 0,
        'byKind': {k: {
            'invest':  per[k]['inv'],
            'payout':  per[k]['pay'],
            'recovery': round(per[k]['pay'] / per[k]['inv'] * 100, 1) if per[k]['inv'] else 0,
            'hit':     per[k]['hit'],
            'races':   per[k]['races'],
            'hitRate': round(per[k]['hit'] / per[k]['races'] * 100, 1) if per[k]['races'] else 0,
        } for k in KINDS},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('date', help='例: 2026-05-16')
    ap.add_argument('--venue', help='場で絞る (例: 東京)')
    ap.add_argument('--race',  type=int, help='Rで絞る (例: 11)')
    ap.add_argument('--force', action='store_true', help='取得済みも上書き')
    args = ap.parse_args()

    path = KT_DIR / f'{args.date}.json'
    d = json.load(open(path, encoding='utf-8'))
    races = d['races']
    if args.venue:
        races = [r for r in races if r['venue'] == args.venue]
    if args.race:
        races = [r for r in races if str(r['raceNum']).rstrip('R') == str(args.race)]

    ok = 0
    for r in races:
        if update_race(r, args.force):
            ok += 1

    # 集計
    target = [r for r in d['races'] if r.get('result')]
    if target:
        all_s = aggregate(target)
        all_s['updated'] = datetime.now().isoformat(timespec='seconds')

        venues = {}
        for r in target:
            venues.setdefault(r['venue'], []).append(r)
        all_s['byVenue'] = {v: aggregate(rs) for v, rs in venues.items()}
        d['summaryV2'] = all_s

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f'\n完了: {ok}/{len(races)} 取得')
    if target:
        s = d['summaryV2']
        print(f"集計: {s['racesWithResult']}R  投資¥{s['totalInvest']:,}  払戻¥{s['totalPayout']:,}  回収率{s['totalRecovery']}%")
        LABEL = {
            'honmei_tan':    '⛩️ 単勝◎',
            'honmei_umatan': '⛩️ 馬単◎軸マルチ',
            'ana_tan':       '🌕 単勝激',
            'ana_umatan':    '🌕 馬単激軸マルチ',
        }
        for k, v in s['byKind'].items():
            lbl = LABEL.get(k, k)
            print(f"  {lbl:<18} 的中{v['hit']:>2}/{v['races']:>2}R ({v['hitRate']:>5.1f}%)  回収率{v['recovery']:>7.1f}%")


if __name__ == '__main__':
    main()
