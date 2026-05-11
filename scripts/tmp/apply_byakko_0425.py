#!/usr/bin/env python3
"""
白虎gradeを race-notes JSON に反映するスクリプト (2026-04-25 土曜5鞍)
- 青葉賞 (2026-04-25-tokyo-11r.json) は既存JSON update
- WIN1-4 の 4鞍は JSON新規作成
"""
import json
import os

RACE_NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'

# race_key → JSON file name のマッピング
RACE_MAP = {
    'kyoto-10r-mitsugihashi-s': '2026-04-25-kyoto-10r.json',
    'tokyo-10r-kamakura-s': '2026-04-25-tokyo-10r.json',
    'fukushima-11r-fct-cup': '2026-04-25-fukushima-11r.json',
    'kyoto-11r-tenouzan-s': '2026-04-25-kyoto-11r.json',
    'tokyo-11r-aobasho': '2026-04-25-tokyo-11r.json',
}

RACE_META = {
    'kyoto-10r-mitsugihashi-s': {
        'name': '観月橋S', 'grade': '3勝', 'date': '2026-04-25',
        'venue': '京都', 'surface': 'ダ', 'distance': 1800, 'course': '右',
        'startTime': '14:50', 'headCount': 11
    },
    'tokyo-10r-kamakura-s': {
        'name': '鎌倉S', 'grade': '3勝', 'date': '2026-04-25',
        'venue': '東京', 'surface': 'ダ', 'distance': 1400, 'course': '左',
        'startTime': '15:00', 'headCount': 15
    },
    'fukushima-11r-fct-cup': {
        'name': '福島中央テレビ杯', 'grade': '3勝', 'date': '2026-04-25',
        'venue': '福島', 'surface': 'ダ', 'distance': 1150, 'course': '右',
        'startTime': '15:15', 'headCount': 12
    },
    'kyoto-11r-tenouzan-s': {
        'name': '天王山S', 'grade': 'L', 'date': '2026-04-25',
        'venue': '京都', 'surface': 'ダ', 'distance': 1200, 'course': '右',
        'startTime': '15:35', 'headCount': 12
    },
}

def make_horses_from_byakko(horses_byakko):
    """白虎gradeのみ持ったhorses配列を作成（lapFactorsに入れる）"""
    out = []
    for h in horses_byakko:
        out.append({
            'listOrder': h['uma'],
            'num': h['uma'],
            'gate': None,
            'name': h['name'],
            'lapFactors': {
                'grade': h['byakkoGrade'],
                'reason': h['byakkoReason'],
                'sp': h['sp'],
                'source': 'byakko_v1_sp'
            }
        })
    return out

def apply_to_aobasho():
    """青葉賞 JSON に lapFactors を追加（既存18頭マージ）"""
    with open('/Users/buntawakase/Desktop/ug-keiba/scripts/tmp/byakko_grades_0425.json') as f:
        grades = json.load(f)

    aobasho_path = os.path.join(RACE_NOTES_DIR, '2026-04-25-tokyo-11r.json')
    with open(aobasho_path) as f:
        d = json.load(f)

    # name lookup
    byakko_horses = {h['name']: h for h in grades['races']['tokyo-11r-aobasho']['horses']}

    for h in d['horses']:
        name = h['name']
        if name in byakko_horses:
            b = byakko_horses[name]
            h['lapFactors'] = {
                'grade': b['byakkoGrade'],
                'reason': b['byakkoReason'],
                'sp': b['sp'],
                'source': 'byakko_v1_sp'
            }
        else:
            print(f'  警告: {name} → 白虎grade無し')

    d['logicVersion'] = 'v2-rel-lap'
    with open(aobasho_path, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'✅ 青葉賞 {aobasho_path} 更新')

def make_new_race_notes():
    """WIN1-4 の JSON新規作成"""
    with open('/Users/buntawakase/Desktop/ug-keiba/scripts/tmp/byakko_grades_0425.json') as f:
        grades = json.load(f)

    for race_key, file_name in RACE_MAP.items():
        if race_key == 'tokyo-11r-aobasho':
            continue
        meta = RACE_META[race_key]
        horses_byakko = grades['races'][race_key]['horses']
        path = os.path.join(RACE_NOTES_DIR, file_name)

        json_data = {
            'race': meta,
            'raceTitle': {
                'main': meta['name'],
                'sub': 'WIN5対象・白虎ドラフト',
                'desc': '─ 御神託は木曜以降、枠順確定を待って降ろされます ─'
            },
            'dataStatus': 'preparation',
            'logicVersion': 'v2-rel-lap',
            'horses': make_horses_from_byakko(horses_byakko)
        }

        with open(path, 'w') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f'✅ {meta["name"]} → {path} 作成')

if __name__ == '__main__':
    apply_to_aobasho()
    make_new_race_notes()
