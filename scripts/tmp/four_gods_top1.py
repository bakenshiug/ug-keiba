#!/usr/bin/env python3
"""
四神ファクター1位抽出（2026-04-25 WIN5対象5レース）
- 青龍: seiryu.grade > danwaGrade.grade (最高順位)
- 白虎: lapFactors.grade + sp配列max値比較
- 玄武: genbuGrade.grade/score (A>B>C>D, score降順)
- 朱雀: 究極分析は別途手動で付記（既存JSONには未反映）
"""
import json
import os

NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'
FILES = [
    ('WIN1 観月橋S', '2026-04-25-kyoto-10r.json'),
    ('WIN2 鎌倉S',   '2026-04-25-tokyo-10r.json'),
    ('WIN3 福島TV',  '2026-04-25-fukushima-11r.json'),
    ('WIN4 天王山S', '2026-04-25-kyoto-11r.json'),
    ('WIN5 青葉賞',  '2026-04-25-tokyo-11r.json'),
]

GRADE_RANK = {'S':5,'A':4,'B':3,'C':2,'D':1}

def get_seiryu_score(h):
    """青龍スコア = seiryuあればそれ、なければdanwaGrade。fatalは-2段階ペナ"""
    if 'seiryu' in h:
        g = h['seiryu'].get('grade', 'B')
        return GRADE_RANK.get(g, 3)
    d = h.get('danwaGrade', {})
    g = d.get('grade', 'B')
    fatal = d.get('fatal', False)
    s = GRADE_RANK.get(g, 3)
    if fatal: s -= 2
    return s

def get_byakko_score(h):
    """白虎スコア = lapFactors grade + peak(sp max)"""
    lf = h.get('lapFactors', {})
    g = lf.get('grade', 'B')
    sp = [x for x in lf.get('sp', []) if x is not None]
    peak = max(sp) if sp else 0
    # grade を主軸、peakはtie-break
    return GRADE_RANK.get(g, 3) * 100 + peak

def get_genbu_score(h):
    """玄武スコア = genbuGrade grade + score(±補正値)"""
    gg = h.get('genbuGrade', {})
    g = gg.get('grade', 'B')
    s = gg.get('score', 0)
    return GRADE_RANK.get(g, 3) * 10 + s

def top_n(horses, score_fn, n=3):
    """上位n頭を (score, name, num) で返す"""
    scored = [(score_fn(h), h.get('name',''), h.get('num','-')) for h in horses]
    scored.sort(reverse=True)
    return scored[:n]

def main():
    print('=' * 80)
    print('四神ファクター1位 × 5レース マトリクス')
    print('=' * 80)
    for label, fname in FILES:
        path = os.path.join(NOTES_DIR, fname)
        if not os.path.exists(path):
            print(f'\n{label}: {fname} なし')
            continue
        with open(path) as f:
            d = json.load(f)
        horses = d.get('horses', [])
        print(f'\n■ {label}  ({len(horses)}頭)')

        sei = top_n(horses, get_seiryu_score, 3)
        byakko = top_n(horses, get_byakko_score, 3)
        genbu = top_n(horses, get_genbu_score, 3)

        print(f'  🐉 青龍1位: {sei[0][1]:14s} ({sei[0][2]}) score={sei[0][0]}')
        for s in sei[1:]:
            print(f'     └ 2-3位: {s[1]:14s} ({s[2]}) score={s[0]}')
        print(f'  🐅 白虎1位: {byakko[0][1]:14s} ({byakko[0][2]}) score={byakko[0][0]:.1f}')
        for b in byakko[1:]:
            print(f'     └ 2-3位: {b[1]:14s} ({b[2]}) score={b[0]:.1f}')
        print(f'  🐢 玄武1位: {genbu[0][1]:14s} ({genbu[0][2]}) score={genbu[0][0]}')
        for g in genbu[1:]:
            print(f'     └ 2-3位: {g[1]:14s} ({g[2]}) score={g[0]}')

if __name__ == '__main__':
    main()
