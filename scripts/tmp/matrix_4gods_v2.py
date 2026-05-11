#!/usr/bin/env python3
"""
🏇 4神1位マトリクス v2（新マッピング）
- 🐉 青龍 = 言霊（seiryu/danwaGrade）
- 🔥 朱雀 = SP（lapFactors.sp max）
- 🐅 白虎 = ラップ（yugomiLapGrade）
- 🐢 玄武 = コース（courseDataGrade）

各レースで4神1位を抽出 → 4頭BOX候補を可視化
"""
import json
import os

NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'
FILES = [
    ('WIN1 観月橋S',  '2026-04-25-kyoto-10r.json'),
    ('WIN2 鎌倉S',    '2026-04-25-tokyo-10r.json'),
    ('WIN3 福島TV杯', '2026-04-25-fukushima-11r.json'),
    ('WIN4 天王山S',  '2026-04-25-kyoto-11r.json'),
    ('WIN5 青葉賞',   '2026-04-25-tokyo-11r.json'),
]

GR = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}


def is_fatal(h):
    d = h.get('danwaGrade', {})
    if d.get('fatal'): return True
    sei = h.get('seiryu', {})
    if sei.get('grade') == 'D': return True
    return False


def seiryu_score(h):  # 🐉 青龍
    if 'seiryu' in h:
        return GR.get(h['seiryu'].get('grade', 'B'), 3)
    d = h.get('danwaGrade', {})
    return GR.get(d.get('grade', 'B'), 3) - (2 if d.get('fatal') else 0)


def suzaku_score(h):  # 🔥 朱雀 = SP peak
    sp = [x for x in (h.get('lapFactors', {}).get('sp') or []) if x is not None]
    return max(sp) if sp else 0


def byakko_score(h):  # 🐅 白虎 = 究極
    yg = h.get('yugomiLapGrade', {})
    g = yg.get('grade', 'D')
    rc = yg.get('redCount', 0)
    r1 = 1 if yg.get('rank1') else 0
    return r1 * 1000 + GR.get(g, 1) * 10 + rc


def genbu_score(h):  # 🐢 玄武 = コース
    cd = h.get('courseDataGrade', {})
    g = cd.get('grade', 'D')
    total = cd.get('total', 0)
    return GR.get(g, 1) * 100 + total


def top1_clean(horses, fn):
    clean = [h for h in horses if not is_fatal(h)]
    scored = [(fn(h), h.get('name', ''), h) for h in clean]
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else None


def top3_clean(horses, fn):
    clean = [h for h in horses if not is_fatal(h)]
    scored = [(fn(h), h.get('name', ''), h) for h in clean]
    scored.sort(key=lambda x: -x[0])
    return scored[:3]


def fmt_seiryu(h):
    g = h.get('seiryu', {}).get('grade') or h.get('danwaGrade', {}).get('grade', '?')
    return g


def fmt_suzaku(h):
    sp = [x for x in (h.get('lapFactors', {}).get('sp') or []) if x is not None]
    return f'peak{max(sp):.1f}' if sp else '-'


def fmt_byakko(h):
    yg = h.get('yugomiLapGrade', {})
    return f"{yg.get('grade','?')}/赤{yg.get('redCount',0)}"


def fmt_genbu(h):
    cd = h.get('courseDataGrade', {})
    return f"{cd.get('grade','?')}/{cd.get('total',0)}pt"


def main():
    print('=' * 95)
    print('🏇 4神1位マトリクス v2（致命除外後） ― 2026-04-25 WIN5')
    print('=' * 95)

    all_box = {}

    for label, fname in FILES:
        path = os.path.join(NOTES_DIR, fname)
        with open(path) as f:
            d = json.load(f)
        horses = d.get('horses', [])

        sei = top1_clean(horses, seiryu_score)
        suz = top1_clean(horses, suzaku_score)
        byk = top1_clean(horses, byakko_score)
        gen = top1_clean(horses, genbu_score)

        top1 = {
            '🐉青龍': (sei[1], fmt_seiryu(sei[2])) if sei else ('', ''),
            '🔥朱雀': (suz[1], fmt_suzaku(suz[2])) if suz else ('', ''),
            '🐅白虎': (byk[1], fmt_byakko(byk[2])) if byk else ('', ''),
            '🐢玄武': (gen[1], fmt_genbu(gen[2])) if gen else ('', ''),
        }

        print(f'\n■ {label}')
        for god, (name, info) in top1.items():
            print(f'  {god}  1位: {name:<16s} ({info})')

        # ユニーク頭数と重複カウント
        names = [v[0] for v in top1.values() if v[0]]
        unique = list(dict.fromkeys(names))  # 順序保持
        dup_count = {n: names.count(n) for n in unique}

        print(f'  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        print(f'  🎯 ユニーク {len(unique)}頭')

        # 重複馬
        dups = [n for n, c in dup_count.items() if c >= 2]
        if dups:
            for d_name in dups:
                cnt = dup_count[d_name]
                gods_held = [g for g, (n, _) in top1.items() if n == d_name]
                print(f'  ★ {d_name} が {cnt}冠！（{" + ".join(gods_held)}）')

        # 4頭BOX候補（ユニーク4頭あれば確定、足りなければ2位補充）
        if len(unique) == 4:
            box = unique
        else:
            # 2位補充
            need = 4 - len(unique)
            # 2-3位馬を4神から集める
            candidates = []
            for fn in [seiryu_score, suzaku_score, byakko_score, genbu_score]:
                top3 = top3_clean(horses, fn)
                for t in top3[1:]:  # 2-3位
                    if t[1] not in unique and t[1] not in [c[1] for c in candidates]:
                        candidates.append((t[0], t[1]))
            candidates.sort(key=lambda x: -x[0])
            additional = [c[1] for c in candidates[:need]]
            box = unique + additional

        print(f'  📦 4頭BOX候補: {box}')
        all_box[label] = box

    print('\n' + '=' * 95)
    print('📋 5鞍 4頭BOX候補 サマリー')
    print('=' * 95)
    for label, box in all_box.items():
        print(f'\n{label}')
        for i, name in enumerate(box, 1):
            print(f'  {i}. {name}')


if __name__ == '__main__':
    main()
