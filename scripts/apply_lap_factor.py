#!/usr/bin/env python3
"""
ラップファクター流し込みスクリプト
====================================
Usage: python3 scripts/apply_lap_factor.py

入力:
  scripts/laps/pace.tsv            - 各レースのペース予想 (紙から転記)
  scripts/laps/{race-dir}.tsv      - 各馬のラップキャラ (紙から転記)
  scripts/lap_grade_matrix.json    - pace × lapChar → grade マトリクス

出力:
  docs/data/race-notes/{race}.json の各馬に lapFactors 追加
  {
    "lapChar":       "疾風万能",      - UG訳 (表示用)
    "strideLapChar": "高速バランス",   - ストライド紙原文 (出典)
    "paceForecast":  "HH",           - 紙のペース予想
    "paperVerdict":  "カスリ",       - 紙の「ピッタリ/カスリ/V」(参考、gradeには使わない)
    "grade":         "S",            - UGマトリクス判定
    "source":        "stride+ug"
  }
  race.paceForecast にも paceForecast をセット

金曜20時: 青葉賞PDF届く → aobasho.tsv 埋める → 実行
土曜20時: フローラ/マイラーズPDF → floras.tsv + milers-c.tsv + pace.tsv → 実行
"""
import json
import sys
from pathlib import Path

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')

RACE_MAP = [
    ('2026-04-25-aobasho',  '2026-04-25-tokyo-11r'),
    ('2026-04-26-floras',   '2026-04-26-tokyo-11r'),
    ('2026-04-26-milers-c', '2026-04-26-kyoto-11r'),
]


def load_matrix():
    return json.loads((BASE / 'scripts/lap_grade_matrix.json').read_text(encoding='utf-8'))


def parse_pace_tsv():
    """pace.tsv → {race-dir: pace}"""
    path = BASE / 'scripts/laps/pace.tsv'
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        parts = s.split('\t')
        if len(parts) < 2:
            continue
        key = parts[0].strip()
        pace = parts[1].strip()
        if pace:
            out[key] = pace
    return out


def parse_lap_tsv(path):
    """lap tsv → [{name, lapChar, paperVerdict}]"""
    if not path.exists():
        return []
    rows = []
    header = None
    for line in path.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        parts = line.split('\t')
        if header is None:
            header = [p.strip() for p in parts]
            continue
        if len(parts) < 2:
            continue
        name = parts[0].strip()
        lap_char = parts[1].strip() if len(parts) > 1 else ''
        verdict = parts[2].strip() if len(parts) > 2 else ''
        if not name:
            continue
        rows.append({'name': name, 'lapChar': lap_char, 'paperVerdict': verdict})
    return rows


def to_ug(lap_char, matrix):
    """ストライド表記→UG表記に変換 (既にUG表記ならそのまま)"""
    if not lap_char:
        return '', ''
    s2u = matrix.get('strideToUg', {})
    if lap_char in s2u:
        return s2u[lap_char], lap_char  # (ug, stride)
    # 既にUG表記 / 未知
    if lap_char in matrix['matrix']:
        return lap_char, ''
    return lap_char, lap_char  # 未知: そのまま


def compute_grade(ug_char, pace, matrix):
    fb = matrix['fallback']
    if not ug_char and not pace:
        return fb['bothUnknown']
    if not ug_char:
        return fb['unknownLapChar']
    if not pace:
        return fb['unknownPace']
    row = matrix['matrix'].get(ug_char)
    if not row:
        return fb['unknownLapChar']
    return row.get(pace, fb['unknownPace'])


def update_race(rd_name, rn_name, pace_map, matrix):
    tsv = BASE / 'scripts/laps' / f'{rd_name}.tsv'
    notes = BASE / 'docs/data/race-notes' / f'{rn_name}.json'

    rows = parse_lap_tsv(tsv)
    pace = pace_map.get(rd_name) or pace_map.get(rn_name, '')

    by_name = {r['name']: r for r in rows if r['lapChar']}

    if not notes.exists():
        print(f'skip: {rn_name}.json not found')
        return

    n = json.loads(notes.read_text(encoding='utf-8'))

    # race メタに paceForecast セット
    if pace:
        n.setdefault('race', {})['paceForecast'] = pace

    hit, unmatched_paper = 0, 0
    for h in n.get('horses', []):
        r = by_name.get(h['name'])
        if not r:
            h['lapFactors'] = None  # まだ未入力
            continue
        ug_char, stride_char = to_ug(r['lapChar'], matrix)
        grade = compute_grade(ug_char, pace, matrix)
        h['lapFactors'] = {
            'lapChar':       ug_char,                         # UG訳 (表示用)
            'strideLapChar': stride_char or r['lapChar'],     # ストライド原文
            'paceForecast':  pace or None,
            'paperVerdict':  r['paperVerdict'] or None,
            'grade':         grade,
            'source':        'stride+ug'
        }
        hit += 1
        if r['paperVerdict'] in ('ピッタリ',) and grade not in ('S', 'A'):
            unmatched_paper += 1

    # dataStatus 更新
    if hit >= len(n.get('horses', [])) * 0.9 and n.get('dataStatus') in ('preparation', 'bracket-fixed'):
        n['dataStatus'] = 'lap-fixed' if n.get('dataStatus') == 'bracket-fixed' else 'lap-partial'

    notes.write_text(json.dumps(n, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  {rd_name}: {hit}/{len(n.get("horses", []))} 頭流し込み / pace={pace or "(未)"} / 紙ピッタリだが独自grade非S/A={unmatched_paper}')


def main():
    matrix = load_matrix()
    pace_map = parse_pace_tsv()
    if not pace_map:
        print('⚠ scripts/laps/pace.tsv が未入力 / 未作成。全レース pace なしで進行。')
    for rd, rn in RACE_MAP:
        update_race(rd, rn, pace_map, matrix)
    print('\n完了。')


if __name__ == '__main__':
    main()
