#!/usr/bin/env python3
"""
🏇 4神+α 横断マトリクス（5鞍フル・致命除外後）
- 主要4: 青龍(言霊) / SP(スピード指数) / 究極(HC+ゴールデン) / コースデータ※手動
- 下支え1: 玄武(外厩) / ※朱雀(弥永ch)は未実装
- 白虎(lapFactors.grade)はSPの算出元なので参考表示

各レースで各ファクター1位を抽出し、重複と4頭ピック候補を可視化
"""
import json
import os

NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'
FILES = [
    ('WIN1 観月橋S',  '2026-04-25-kyoto-10r.json'),
    ('WIN2 鎌倉S',    '2026-04-25-tokyo-10r.json'),
    ('WIN3 福島TV',   '2026-04-25-fukushima-11r.json'),
    ('WIN4 天王山S',  '2026-04-25-kyoto-11r.json'),
    ('WIN5 青葉賞',   '2026-04-25-tokyo-11r.json'),
]

GR = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}


def is_fatal(h):
    d = h.get('danwaGrade', {})
    if d.get('fatal'):
        return True
    sei = h.get('seiryu', {})
    if sei.get('grade') == 'D':
        return True
    return False


def seiryu_score(h):
    if 'seiryu' in h:
        return GR.get(h['seiryu'].get('grade', 'B'), 3) * 10
    d = h.get('danwaGrade', {})
    return GR.get(d.get('grade', 'B'), 3) * 10 - (20 if d.get('fatal') else 0)


def byakko_score(h):
    lf = h.get('lapFactors', {})
    sp = [x for x in (lf.get('sp') or []) if x is not None]
    peak = max(sp) if sp else 0
    return GR.get(lf.get('grade', 'B'), 3) * 100 + peak


def sp_score(h):
    sp = [x for x in (h.get('lapFactors', {}).get('sp') or []) if x is not None]
    return max(sp) if sp else 0


def yugomi_score(h):
    yg = h.get('yugomiLapGrade', {})
    g = yg.get('grade', 'D')
    rc = yg.get('redCount', 0)
    r1 = 1 if yg.get('rank1') else 0
    return r1 * 1000 + GR.get(g, 1) * 10 + rc


def genbu_score(h):
    gg = h.get('genbuGrade', {})
    return GR.get(gg.get('grade', 'B'), 3) * 10 + gg.get('score', 0)


def top_clean(horses, fn, n=3):
    clean = [h for h in horses if not is_fatal(h)]
    scored = [(fn(h), h.get('name', ''), h.get('num', '-')) for h in clean]
    scored.sort(reverse=True)
    return scored[:n]


def format_horse(t, fn_name, h):
    """馬名+gradeの簡易フォーマット"""
    score, name, num = t
    if fn_name == 'seiryu':
        g = h.get('seiryu', {}).get('grade') or h.get('danwaGrade', {}).get('grade', '?')
        return f'{name}({g})'
    if fn_name == 'byakko':
        return f'{name}({h.get("lapFactors",{}).get("grade","?")})'
    if fn_name == 'sp':
        return f'{name}(peak{score:.1f})'
    if fn_name == 'yugomi':
        yg = h.get('yugomiLapGrade', {})
        red = yg.get('redCount', 0)
        g = yg.get('grade', '?')
        return f'{name}({g}/赤{red})'
    if fn_name == 'genbu':
        gg = h.get('genbuGrade', {})
        return f'{name}({gg.get("grade","?")}{"+" if gg.get("score",0)>0 else ""}{gg.get("score",0) or ""})'
    return name


def get_horse_by_name(horses, name):
    for h in horses:
        if h.get('name') == name:
            return h
    return None


def main():
    print('=' * 100)
    print('🏇 4神+α 横断マトリクス 5鞍フル (致命除外後) ― 2026-04-25 WIN5')
    print('=' * 100)

    race_top1 = {}

    for label, fname in FILES:
        path = os.path.join(NOTES_DIR, fname)
        with open(path) as f:
            d = json.load(f)
        horses = d.get('horses', [])

        # 各ファクター top3
        sei = top_clean(horses, seiryu_score)
        byk = top_clean(horses, byakko_score)
        sp_ = top_clean(horses, sp_score)
        yug = top_clean(horses, yugomi_score)
        gen = top_clean(horses, genbu_score)

        # top1 のみ馬名収集
        t1_names = {
            '青龍': sei[0][1] if sei else '',
            '白虎': byk[0][1] if byk else '',
            'SP ': sp_[0][1] if sp_ else '',
            '究極': yug[0][1] if yug else '',
            '玄武': gen[0][1] if gen else '',
        }

        print(f'\n■ {label}')
        print('  ┌──────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐')
        print('  │ 軸   │ 1位                     │ 2位                     │ 3位                     │')
        print('  ├──────┼─────────────────────────┼─────────────────────────┼─────────────────────────┤')

        def row(label, tops, fn_name):
            cells = []
            for t in tops + [(0, '', '')] * (3 - len(tops)):
                if t[1]:
                    h = get_horse_by_name(horses, t[1])
                    cells.append(format_horse(t, fn_name, h))
                else:
                    cells.append('')
            print(f'  │ {label} │ {cells[0]:<23s} │ {cells[1]:<23s} │ {cells[2]:<23s} │')

        row('青龍  ', sei, 'seiryu')
        row('白虎  ', byk, 'byakko')
        row('SP    ', sp_, 'sp')
        row('究極  ', yug, 'yugomi')
        row('玄武  ', gen, 'genbu')
        print('  └──────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘')

        # ユニーク馬数
        unique = list(set(t1_names.values()))
        print(f'  🎯 1位馬ユニーク: {len(unique)}頭 → {unique}')

        race_top1[label] = t1_names

    # 最終サマリー
    print('\n' + '=' * 100)
    print('📋 5鞍 1位馬 サマリー（コースデータ軸は別途手動判定）')
    print('=' * 100)
    print(f'\n{"レース":12s} {"青龍":16s} {"SP":20s} {"究極":18s} {"玄武":18s}')
    print('-' * 100)
    for label, t1 in race_top1.items():
        print(f'{label:12s} {t1["青龍"]:16s} {t1["SP "]:20s} {t1["究極"]:18s} {t1["玄武"]:18s}')


if __name__ == '__main__':
    main()
