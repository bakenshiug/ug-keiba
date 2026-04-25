#!/usr/bin/env python3
"""
4/26 5レース picks のbadgesを最新horses[]から再構築
（horses[]に grade があれば反映、無ければ「—」）
"""
import json
from pathlib import Path

RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'
GOD_LABEL = {'seiryu': '青龍', 'suzaku': '朱雀', 'byakko': '白虎', 'genbu': '玄武'}
GOD_SUB   = {'seiryu': '言霊', 'suzaku': '速眼', 'byakko': 'ラップ', 'genbu': '地脈'}


def get_god_grade(horse, god):
    if god == 'seiryu':
        return (horse.get('relComment') or {}).get('grade')
    if god == 'suzaku':
        return (horse.get('suzakuGrade') or {}).get('grade')
    if god == 'byakko':
        return (horse.get('yugomiLapGrade') or {}).get('grade')
    if god == 'genbu':
        return (horse.get('courseDataGrade') or {}).get('grade')
    return None


def build_badges(horse, picked_god, picked_grade):
    badges = []
    for g in ('seiryu', 'suzaku', 'byakko', 'genbu'):
        b = {'t': g, 'label': f'{GOD_LABEL[g]}（{GOD_SUB[g]}）'}
        b['g'] = get_god_grade(horse, g) or '—'
        if g == 'suzaku':
            sg = horse.get('suzakuGrade') or {}
            b['soku'] = (sg.get('soku') or {}).get('grade') or '—'
            b['gan']  = (sg.get('gan')  or {}).get('grade') or '—'
        if g == picked_god:
            b['g'] = picked_grade
        badges.append(b)
    return badges


for k in ['2026-04-26-kyoto-10r','2026-04-26-tokyo-10r','2026-04-26-fukushima-11r','2026-04-26-kyoto-11r','2026-04-26-tokyo-11r']:
    p = RN_DIR / f'{k}.json'
    d = json.load(open(p))
    horses_top = {h.get('name'): h for h in d.get('horses', [])}
    pres = d.get('presentation', {})
    rebuilt = []
    for ph in pres.get('horses', []):
        name = ph.get('name')
        h = horses_top.get(name) or {}
        ph['badges'] = build_badges(h, ph.get('god'), ph.get('godGrade'))
        rebuilt.append((name, ph['badges']))
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    race_name = d.get('race', {}).get('name', '?')
    print(f'\n=== {race_name} ===')
    for name, bg in rebuilt:
        line = ' / '.join(f"{b['t'][:3]}={b['g']}" for b in bg)
        print(f"  {name:<14} {line}")
