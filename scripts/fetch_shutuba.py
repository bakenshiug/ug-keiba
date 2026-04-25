#!/usr/bin/env python3
"""
fetch_shutuba.py — netkeiba 出馬表(shutuba_past.html) から 馬番/枠番/性齢/騎手/父/母/母父/厩舎 を取得し、
race-notes.horses[] と presentation.horses[] にマージする。

Usage:
  python3 scripts/fetch_shutuba.py 2026-04-26-tokyo-11r        # 単一
  python3 scripts/fetch_shutuba.py --day 2026-04-26            # 1日まとめ
  python3 scripts/fetch_shutuba.py --all                       # 全レース
  python3 scripts/fetch_shutuba.py 2026-04-26-tokyo-11r --picks-only  # pres.horsesに含まれる馬のみ
"""
import urllib.request, re, json, sys, argparse
from pathlib import Path

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'


def fetch_html(race_id):
    url = f'https://race.netkeiba.com/race/shutuba_past.html?race_id={race_id}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('euc-jp', errors='replace')


def _strip(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def parse_shutuba(html):
    """全頭の {gate, num, name, sire, dam, bms, trainer, jockey, sexAge, kinryo, prevName, prevFinish, prevDate, prevDist, prevTime} dictを返す。馬名で検索可能"""
    out = []
    # HorseList行抽出
    for row in re.findall(r'<tr[^>]*class="HorseList"[^>]*>(.*?)</tr>', html, re.S):
        gate = re.search(r'<td class="Waku\d+"[^>]*>(\d+)</td>', row)
        num  = re.search(r'<td class="Waku"[^>]*>(\d+)</td>', row)
        sire = re.search(r'<div class="Horse01[^"]*">([^<]+)</div>', row)
        # 馬名 Horse02
        name_m = re.search(r'<div class="Horse02">\s*<a[^>]*>\s*([^<]+?)\s*</a>', row)
        dam = re.search(r'<div class="Horse03">([^<]+)</div>', row)
        bms = re.search(r'<div class="Horse04">\(([^)]+)\)</div>', row)
        trainer_m = re.search(r'<div class="Horse05[^"]*">\s*<a[^>]*>([^<]+)</a>', row)
        # 騎手 Jockey td
        jockey = None
        jt = re.search(r'<td class="Jockey">(.*?)</td>', row, re.S)
        if jt:
            j = re.search(r'<a[^>]*jockey[^>]*>([^<]+)</a>', jt.group(1))
            jockey = j.group(1).strip() if j else None
        # 性齢 Barei
        barei = re.search(r'<span class="Barei"[^>]*>([^<]+)</span>', row)
        # 斤量
        kinryo = None
        if jt:
            kg = re.search(r'<span>(\d+(?:\.\d+)?)</span>', jt.group(1))
            kinryo = kg.group(1) if kg else None

        # 前走 (最初のPast td)
        prev_name, prev_finish, prev_date, prev_dist, prev_time = '', '', '', '', ''
        past_m = re.search(r'<td[^>]*class="Past[^"]*"[^>]*>(.*?)</td>', row, re.S)
        if past_m:
            past = past_m.group(1)
            d01 = re.search(r'<div class="Data01">(.*?)</div>', past, re.S)
            if d01:
                ds = re.search(r'<span>([^<]+?)</span>', d01.group(1))
                if ds:
                    prev_date = ds.group(1).replace('&nbsp;', ' ').strip()
                fn = re.search(r'<span class="Num">([^<]+)</span>', d01.group(1))
                if fn:
                    prev_finish = fn.group(1).strip()
            d02 = re.search(r'<div class="Data02">(.*?)</div>', past, re.S)
            if d02:
                # <a href...>レース名<span>grade</span></a> から レース名のみ
                a = re.search(r'<a[^>]*>([^<]+?)(?:<span|</a>)', d02.group(1), re.S)
                if a:
                    prev_name = a.group(1).strip()
            d05 = re.search(r'<div class="Data05">([^<]+)', past)
            if d05:
                # "ダ1400 1:24.2 " → 距離 + タイム
                txt = re.sub(r'\s+', ' ', d05.group(1)).strip()
                parts = txt.split(' ', 1)
                if parts:
                    prev_dist = parts[0]
                    if len(parts) > 1:
                        prev_time = parts[1].strip()

        if not name_m:
            continue
        out.append({
            'gate':       gate.group(1) if gate else '',
            'num':        num.group(1)  if num  else '',
            'name':       name_m.group(1).strip(),
            'sire':       sire.group(1).strip() if sire else '',
            'dam':        dam.group(1).strip()  if dam  else '',
            'bms':        bms.group(1).strip()  if bms  else '',
            'trainer':    trainer_m.group(1).strip().split('・')[-1] if trainer_m else '',
            'jockey':     jockey or '',
            'sexAge':     barei.group(1).strip() if barei else '',
            'kinryo':     kinryo or '',
            'prevName':   prev_name,
            'prevFinish': prev_finish,
            'prevDate':   prev_date,
            'prevDist':   prev_dist,
            'prevTime':   prev_time,
        })
    return out


def merge_to_horses(horses_top, shutuba_list):
    """既存の horses[] に shutuba_list を馬名マッチでマージ（既存値があれば優先）"""
    by_name = {h['name']: h for h in shutuba_list}
    for h in horses_top:
        s = by_name.get(h.get('name'))
        if not s:
            continue
        # 空欄/Noneのみ埋める
        for src_key, dst_key in [
            ('num',     'num'),
            ('gate',    'gate'),
            ('sire',    'sire'),
            ('bms',     'broodmareSire'),
            ('trainer', 'trainer'),
            ('jockey',  'jockey'),
            ('sexAge',  'sexAge'),
            ('kinryo',  'kinryo'),
            ('dam',     'dam'),
        ]:
            if not h.get(dst_key) and s.get(src_key):
                h[dst_key] = s[src_key]
    return horses_top


def merge_to_presentation(pres_horses, shutuba_list):
    """presentation.horses[] にも num/gate/jockey/prevName/prevFinish 等を反映（"—" を上書き）"""
    by_name = {h['name']: h for h in shutuba_list}
    for p in pres_horses:
        s = by_name.get(p.get('name'))
        if not s:
            continue
        # presentation 側は "—" placeholder を上書き
        if p.get('num') in ('—', '', None):     p['num']     = s.get('num')     or '—'
        if p.get('gate') in ('—', '', None):    p['gate']    = s.get('gate')    or '—'
        if p.get('sire') in ('—', '', None):    p['sire']    = s.get('sire')    or '—'
        if p.get('bms')  in ('—', '', None):    p['bms']     = s.get('bms')     or '—'
        if p.get('jockey') in ('—', '', None):  p['jockey']  = s.get('jockey')  or '—'
        if p.get('trainer') in ('—', '', None): p['trainer'] = s.get('trainer') or '—'
        # 前走: 既存値あっても上書き（フォーマット最新化のため）
        if s.get('prevName'):   p['prevName']   = s['prevName']
        if s.get('prevFinish'): p['prevFinish'] = s['prevFinish']
        if s.get('prevDist'):   p['prevDist']   = s['prevDist']
        # 前走場: prevDate "2026.02.01 東京" の後ろを取る
        pd = s.get('prevDate') or ''
        parts = pd.split()
        if len(parts) >= 2:
            p['prevTrack'] = parts[-1]
    return pres_horses


def add_missing_horses(horses_top, shutuba_list):
    """horses_top に居ない出走馬を追加（採点未済馬）"""
    existing = {h.get('name') for h in horses_top}
    for s in shutuba_list:
        if s['name'] in existing:
            continue
        horses_top.append({
            'name':           s['name'],
            'num':            s['num'],
            'gate':           s['gate'],
            'sire':           s['sire'],
            'dam':            s['dam'],
            'broodmareSire':  s['bms'],
            'jockey':         s['jockey'],
            'trainer':        s['trainer'],
            'sexAge':         s['sexAge'],
            'kinryo':         s['kinryo'],
            'relComment':     {'grade': None, 'keyword': '', 'prevRace': ''},
            'suzakuGrade':    {'grade': None, 'soku': None, 'gan': None, 'v': 'v2-soku-gan'},
            'yugomiLapGrade': None,
            'courseDataGrade':None,
        })
    return horses_top


def update(race_key, picks_only=False):
    path = RN_DIR / f'{race_key}.json'
    if not path.exists():
        print(f'  ⚠ NOT FOUND: {race_key}')
        return
    d = json.load(open(path))
    pres = d.get('presentation', {})
    rid = pres.get('raceId')
    if not rid:
        print(f'  ⚠ raceId 未設定: {race_key}')
        return
    try:
        html = fetch_html(rid)
    except Exception as e:
        print(f'  ✗ fetch失敗 {race_key}: {e}')
        return
    sh = parse_shutuba(html)
    if not sh:
        print(f'  ⚠ 出馬表parse失敗: {race_key} (raceId={rid})')
        return

    # picks-only モード: presentation.horses にある馬名のみ shutuba_list を絞る
    if picks_only:
        picks = {p['name'] for p in pres.get('horses', [])}
        sh_filtered = [s for s in sh if s['name'] in picks]
        merge_to_presentation(pres.get('horses', []), sh_filtered)
    else:
        # フル: horses[] にもマージ＋未存在馬は追加、pres.horses[] も上書き
        horses_top = d.get('horses') or []
        d['horses'] = merge_to_horses(horses_top, sh)
        d['horses'] = add_missing_horses(d['horses'], sh)
        merge_to_presentation(pres.get('horses', []), sh)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    name = d.get('race', {}).get('name', '?')
    pn = len(pres.get('horses', []))
    hn = len(d.get('horses', []))
    print(f'  ✓ {race_key:<32} {name:<22} 出馬{len(sh)}頭 picks={pn} horses[]={hn}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('race_key', nargs='?')
    ap.add_argument('--day',   help='例: 2026-04-26')
    ap.add_argument('--all',   action='store_true')
    ap.add_argument('--picks-only', action='store_true', help='pres.horses内の馬のみ更新（horses[]ノータッチ）')
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

    for k in keys:
        update(k, picks_only=args.picks_only)
