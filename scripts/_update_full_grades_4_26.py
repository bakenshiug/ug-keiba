#!/usr/bin/env python3
"""
4/26 5レース picks の **全4神grade** を horses[] と pres.horses badges に書込

エージェントの結果 or Route A スクレイプ結果を GRADES dict に入れて実行。

データ形式:
GRADES = {
    'race_key': {
        '馬名': {
            'seiryu':  'S',                      # 青龍
            'suzaku':  {'g': 'S', 'soku': 'A', 'gan': 'S'},  # 朱雀（合議+sub）
            'byakko':  'A',                      # 白虎
            'genbu':   'B',                      # 玄武
        },
        ...
    },
    ...
}
"""
import json
from pathlib import Path

RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'
GOD_LABEL = {'seiryu': '青龍', 'suzaku': '朱雀', 'byakko': '白虎', 'genbu': '玄武'}
GOD_SUB   = {'seiryu': '言霊', 'suzaku': '速眼', 'byakko': 'ラップ', 'genbu': '地脈'}

# === ここをエージェント or 手動で埋める ===
GRADES = {
    '2026-04-26-kyoto-10r': {  # センテニアル・PS
        # 'レイニング':         {'seiryu': 'S', 'suzaku': {'g':'?','soku':'?','gan':'?'}, 'byakko': '?', 'genbu': '?'},
        # 'ミスタージーティー': {...},
        # 'ショウナンラピダス': {...},
        # 'レディーミコノス':   {...},
    },
    '2026-04-26-tokyo-10r': {     # オアシスS
    },
    '2026-04-26-fukushima-11r': { # モルガナイトS
    },
    '2026-04-26-kyoto-11r': {     # マイラーズC
    },
    '2026-04-26-tokyo-11r': {     # フローラS
    },
}


def update_horse_top(horses_top, name, grades):
    """horses[]の指定馬を更新"""
    for h in horses_top:
        if h.get('name') != name:
            continue
        # 青龍
        rc = h.setdefault('relComment', {})
        if grades.get('seiryu'):
            rc['grade'] = grades['seiryu']
        # 朱雀
        suz = grades.get('suzaku') or {}
        if suz:
            sg = h.setdefault('suzakuGrade', {})
            if suz.get('g'):    sg['grade'] = suz['g']
            if suz.get('soku'):
                sg.setdefault('soku', {})['grade'] = suz['soku']
            if suz.get('gan'):
                sg.setdefault('gan', {})['grade'] = suz['gan']
            sg.setdefault('v', 'v2-soku-gan')
        # 白虎
        if grades.get('byakko'):
            h.setdefault('yugomiLapGrade', {})['grade'] = grades['byakko']
        # 玄武
        if grades.get('genbu'):
            h.setdefault('courseDataGrade', {})['grade'] = grades['genbu']
        return True
    # 既存に無ければ新規追加
    new_h = {'name': name}
    update_horse_top([new_h], name, grades)
    horses_top.append(new_h)
    return False


def rebuild_badge(horse_top, picked_god, picked_grade):
    badges = []
    for g in ('seiryu', 'suzaku', 'byakko', 'genbu'):
        b = {'t': g, 'label': f'{GOD_LABEL[g]}（{GOD_SUB[g]}）'}
        if g == 'seiryu':
            b['g'] = (horse_top.get('relComment') or {}).get('grade') or '—'
        elif g == 'suzaku':
            sg = horse_top.get('suzakuGrade') or {}
            b['g'] = sg.get('grade') or '—'
            b['soku'] = (sg.get('soku') or {}).get('grade') or '—'
            b['gan']  = (sg.get('gan')  or {}).get('grade') or '—'
        elif g == 'byakko':
            b['g'] = (horse_top.get('yugomiLapGrade') or {}).get('grade') or '—'
        elif g == 'genbu':
            b['g'] = (horse_top.get('courseDataGrade') or {}).get('grade') or '—'
        if g == picked_god and picked_grade:
            b['g'] = picked_grade
        badges.append(b)
    return badges


def update(race_key, mapping):
    p = RN_DIR / f'{race_key}.json'
    d = json.load(open(p))
    horses_top = d.setdefault('horses', [])
    pres = d.get('presentation', {})

    # horses[] update
    for name, grades in mapping.items():
        update_horse_top(horses_top, name, grades)

    # pres.horses badges rebuild
    horses_by_name = {h.get('name'): h for h in horses_top}
    for ph in pres.get('horses', []):
        ht = horses_by_name.get(ph.get('name')) or {}
        ph['badges'] = rebuild_badge(ht, ph.get('god'), ph.get('godGrade'))

    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    name = d.get('race', {}).get('name', '?')
    print(f'\n=== {name} ===')
    for ph in pres.get('horses', []):
        line = ' '.join(f"{b['t'][:3]}={b['g']}" for b in ph['badges'])
        print(f"  {ph['godEmoji']} {ph['name']:<14} {line}")


if __name__ == '__main__':
    for k, m in GRADES.items():
        if m:
            update(k, m)
        else:
            print(f'  (skip {k}: GRADES空)')
