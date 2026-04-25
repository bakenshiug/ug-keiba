#!/usr/bin/env python3
"""
show_picks.py — race-notes.presentation の picks/win5Picks/bets を一発で表示

18時の最終予想時に、各レースの現状を確認するためのヘルパー。
書き換え自体はギーニョ側で直接 Edit するため、本スクリプトは「読み取り専用」。

Usage:
  python3 scripts/show_picks.py 2026-04-26-tokyo-11r
  python3 scripts/show_picks.py --all       # 全レース一覧
  python3 scripts/show_picks.py --day 2026-04-26  # 1日分
"""
import json, argparse, sys, glob
from pathlib import Path

RN_DIR = Path('/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes')

def show_one(race_key):
    p = RN_DIR / f'{race_key}.json'
    if not p.exists():
        print(f"  ⚠ NOT FOUND: {p}")
        return
    d = json.load(open(p))
    race = d.get('race', {})
    pres = d.get('presentation', {})
    horses = pres.get('horses', [])
    win5  = pres.get('win5Picks', [])
    bets  = pres.get('bets', {})

    print(f"\n{'='*60}")
    print(f"  {race.get('name','?')} ({race_key})")
    print(f"  {race.get('venue','?')} {race.get('distance','?')}m {race.get('surface','?')} / {race.get('grade','—')} / 発走 {pres.get('startTime','?')}")
    print(f"{'='*60}")

    print(f"\n  ▼ final-display picks (4頭・ワイドBOX)")
    if not horses:
        print("    （未設定）")
    for h in horses:
        mark    = h.get('mark','?')
        name    = h.get('name','?')
        num     = h.get('num','?')
        ninki   = h.get('ninki','?')
        odds    = h.get('odds','?')
        # suzakuGrade soku/gan も併記
        sb = next((b for b in (h.get('badges') or []) if b.get('t')=='suzaku'), {})
        soku = sb.get('soku','—'); gan = sb.get('gan','—')
        print(f"    {mark} {name:<16} #{num:>2}  {ninki:>3}人気 {odds:>5}倍  / 速{soku}・眼{gan}")

    print(f"\n  ▼ win5Picks ({len(win5)}頭・WIN5用)")
    if not win5:
        print("    （未設定）")
    for h in win5:
        mark = h.get('mark','?')
        name = h.get('name','?')
        num  = h.get('num','?')
        note = h.get('note','')[:40]
        print(f"    {mark} #{num:>2} {name:<16} {note}")

    print(f"\n  ▼ bets")
    strat = bets.get('strategy','?')
    print(f"    strategy: {strat}")
    if strat == 'wide-only':
        wide = bets.get('wide',{})
        horses_w = wide.get('horses', [])
        per = wide.get('perPoint', 100)
        n = len(horses_w)
        pts = n*(n-1)//2
        print(f"    wide:     {' / '.join(horses_w)} ({pts}点 × ¥{per} = ¥{pts*per})")
    elif strat == '4horse-box':
        print(f"    tan:      {bets.get('tan',{}).get('name','?')} ¥{bets.get('tan',{}).get('amount','?')}")
        print(f"    fuku:     {bets.get('fuku',{}).get('name','?')} ¥{bets.get('fuku',{}).get('amount','?')}")
        wide = bets.get('wide',{})
        print(f"    wide:     {' / '.join(wide.get('horses',[]))} (×¥{wide.get('perPoint','?')})")
    elif strat == '1horse-tan':
        print(f"    tan:      {bets.get('tan',{}).get('name','?')} ¥{bets.get('tan',{}).get('amount','?')}")

    note = pres.get('note','')
    if note:
        print(f"\n  ▼ note")
        print(f"    {note[:160]}{'...' if len(note)>160 else ''}")
    print()

def show_all_summary():
    """全レースの picks 充足状況を1行サマリー"""
    files = sorted(RN_DIR.glob('*.json'))
    print(f"\n{'='*70}")
    print(f"  全 race-notes 充足状況サマリー")
    print(f"{'='*70}")
    print(f"  {'date':<12} {'レース':<22} {'picks':>5} {'win5':>5} {'bets':<14}")
    print(f"  {'-'*60}")
    for p in files:
        if p.name.endswith('.bak') or p.name.endswith('.bak2') or p.name.endswith('.bak3') or p.name.endswith('.bak4'):
            continue
        try:
            d = json.load(open(p))
            race = d.get('race', {})
            pres = d.get('presentation', {})
            n_picks = len(pres.get('horses', []))
            n_win5  = len(pres.get('win5Picks', []))
            strat = pres.get('bets',{}).get('strategy','—')
            date = race.get('date','?')
            name = race.get('name','?')
            mark_picks = '✓' if n_picks==4 else ('○' if n_picks>0 else '✗')
            mark_win5  = '✓' if n_win5>0 else '✗'
            print(f"  {date:<12} {name:<22} {mark_picks}{n_picks:>3}  {mark_win5}{n_win5:>3}  {strat}")
        except Exception as e:
            print(f"  {p.name}: ERROR {e}")
    print()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('race_key', nargs='?', help='例: 2026-04-26-tokyo-11r')
    ap.add_argument('--all', action='store_true', help='全レースのサマリー')
    ap.add_argument('--day', help='1日分（例: 2026-04-26）')
    args = ap.parse_args()

    if args.all or (not args.race_key and not args.day):
        show_all_summary()
    elif args.day:
        for p in sorted(RN_DIR.glob(f'{args.day}-*.json')):
            if any(p.name.endswith(suf) for suf in ['.bak','.bak2','.bak3','.bak4']): continue
            show_one(p.stem)
    else:
        show_one(args.race_key)
