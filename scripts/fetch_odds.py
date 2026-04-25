#!/usr/bin/env python3
"""
fetch_odds.py — netkeiba JRA odds API から単勝オッズ＋人気を取得し、
race-notes.presentation.horses[].odds / .ninki に書込

API: https://race.netkeiba.com/api/api_get_jra_odds.html?type=1&action=init&race_id=...
レスポンス: {data: {odds: {"1": {"01": ["3.2", "前", "1"], ...}}}}

Usage:
  python3 scripts/fetch_odds.py 2026-04-26-tokyo-11r
  python3 scripts/fetch_odds.py --day 2026-04-26
"""
import urllib.request, json, sys, argparse
from pathlib import Path

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'


def fetch_odds(race_id):
    url = f'https://race.netkeiba.com/api/api_get_jra_odds.html?type=1&action=init&race_id={race_id}'
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Referer': f'https://race.netkeiba.com/race/shutuba.html?race_id={race_id}',
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8', errors='replace'))


def update(race_key):
    p = RN_DIR / f'{race_key}.json'
    if not p.exists():
        print(f'  ⚠ NOT FOUND: {race_key}')
        return
    d = json.load(open(p))
    pres = d.get('presentation', {})
    rid = pres.get('raceId')
    if not rid:
        print(f'  ⚠ raceId 未設定: {race_key}')
        return
    try:
        api = fetch_odds(rid)
    except Exception as e:
        print(f'  ✗ API失敗 {race_key}: {e}')
        return

    odds_block = (api.get('data') or {}).get('odds') or {}
    tan = odds_block.get('1') or {}  # 単勝
    if not tan:
        print(f'  ⚠ 単勝オッズなし {race_key}')
        return

    # 馬番→ {odds, ninki}
    by_num = {}
    for k, v in tan.items():
        # k = "01"〜"18"
        num = str(int(k))  # "01" → "1"
        if isinstance(v, list) and len(v) >= 3:
            by_num[num] = {'odds': v[0], 'ninki': v[2]}

    # presentation.horses[] に書込
    updated = []
    for h in pres.get('horses', []):
        n = str(h.get('num') or '').strip()
        info = by_num.get(n)
        if info:
            h['odds']  = info['odds']
            h['ninki'] = info['ninki']
            updated.append(f"{h['name']}({h['num']}番)={info['odds']}倍/{info['ninki']}人気")

    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    name = d.get('race', {}).get('name', '?')
    dt = (api.get('data') or {}).get('official_datetime', '?')
    print(f'  ✓ {race_key:<32} {name:<20} 取得時刻={dt}')
    for u in updated:
        print(f'      {u}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('race_key', nargs='?')
    ap.add_argument('--day', help='例: 2026-04-26')
    ap.add_argument('--all', action='store_true')
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
        update(k)
