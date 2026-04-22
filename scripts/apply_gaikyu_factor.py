#!/usr/bin/env python3
"""
外厩個体相性ファクター計算スクリプト
========================================
Input:
  - analysis/{race}/shutuba.json        (各馬の gaikyu 名)
  - analysis/{race}/extracted/*.json    (各馬の gaikyuRecord)
Output:
  - 各馬に gaikyuFactor: {grade, source, record, tries} を追加
  - race-notes/{race-notes}.json と analysis/{race}/shutuba.json を更新

Matching logic:
  shutuba.gaikyu の正規化 (ノーザンファーム→ノーザンF 等) と
  extracted.gaikyuRecord[].name で核キーワード (天栄/しがらき/空港/チャンピオン等) マッチ

Grade logic:
  試行(n) = 勝+連+3着+着外
  複勝率(p) = (勝+連+3着)/n
  - S: p=1.0 and n>=3
  - A: p>=0.66 or (n<=2 and 勝>=1 and 着外==0)
  - B: 0.33<=p<0.66
  - C: p<0.33 or (n==1 and 勝==0 and 着外==1)
  - D: n>=2 and 勝+連+3着==0

Fallback (no individual record for matched gaikyu):
  - ノーザンF系 / チャンピオン / しがらき / 天栄 → A
  - 山元 / 大山ヒルズ / キャニオン / 社台 → A
  - 在厩調整 → B
  - その他 → B
"""
import json
import re
import sys
from pathlib import Path


# 外厩名正規化マップ: 展開前 → 核キーワード
# matchに使う → shutubaのgaikyu名から核を抽出 / extractedの外厩名も核抽出
GAIKYU_CORE_KEYWORDS = [
    ('ノーザンF天栄',      ['天栄']),
    ('ノーザンFしがらき', ['しがらき']),
    ('ノーザンF空港',     ['空港']),
    ('ノーザンF',          ['ノーザンF', 'ノーザンファーム']),  # fallback
    ('チャンピオンヒルズ', ['チャンピオン']),
    ('山元TC',             ['山元']),
    ('大山ヒルズ',         ['大山']),
    ('キャニオンF土山',    ['キャニオン', '土山']),
    ('社台F',              ['社台']),
    ('ビッグレッドF鉾田',  ['鉾田']),
    ('ビッグレッドF泊津',  ['泊津']),
    ('ビッグレッドF',      ['ビッグレッド']),
    ('宇治田原優駿',       ['宇治田原']),
    ('エスティF',          ['エスティ']),
    ('グランデF',          ['グランデ']),
    ('グリーンウッド',     ['グリーンウッド']),
    ('阿見TC',             ['阿見']),
    ('追分F',              ['追分']),
    ('下河辺牧場',         ['下河辺']),
    ('信楽牧場',           ['信楽']),
    ('チェスナットF',      ['チェスナット']),
    ('在厩調整',           ['在厩']),
    ('ダーレー・ジャパン', ['ダーレー']),
    ('吉澤ステーブル',     ['吉澤']),
    ('カドワキ',           ['カドワキ']),
    ('アレジャ',           ['アレジャ']),
    ('山岡トレセン',       ['山岡']),
]

# フォールバックgrade (一般ラベル評価)
FALLBACK_GRADE = {
    'ノーザンF天栄':      'A',
    'ノーザンFしがらき':  'A',
    'ノーザンF空港':      'B',
    'ノーザンF':          'A',
    'チャンピオンヒルズ': 'A',
    '山元TC':             'A',
    '大山ヒルズ':         'A',
    'キャニオンF土山':    'B',
    '社台F':              'A',
    'ビッグレッドF鉾田':  'B',
    'ビッグレッドF泊津':  'B',
    'ビッグレッドF':      'B',
    '宇治田原優駿':       'B',
    'エスティF':          'B',
    'グランデF':          'B',
    'グリーンウッド':     'B',
    '阿見TC':             'B',
    '追分F':              'B',
    '下河辺牧場':         'B',
    '信楽牧場':           'B',
    'チェスナットF':      'B',
    '在厩調整':           'B',
    'ダーレー・ジャパン': 'B',
    '吉澤ステーブル':     'B',
    'カドワキ':           'B',
    'アレジャ':           'B',
    '山岡トレセン':       'B',
}


def normalize_gaikyu_name(name):
    """Return (canonical_key, matched_keyword) or (None, None)."""
    if not name:
        return None, None
    s = re.sub(r'[\s　]+', '', name)
    for canonical, keywords in GAIKYU_CORE_KEYWORDS:
        for kw in keywords:
            if kw in s:
                return canonical, kw
    return None, None


def compute_grade(record):
    """record = [勝, 連, 3着, 着外] → (grade, tries, win_place_show_rate)"""
    win, second, third, lose = record
    tries = sum(record)
    if tries == 0:
        return None, 0, 0.0
    win_place_show = win + second + third
    rate = win_place_show / tries

    # D: 2+ tries, all outside (no win/place/show)
    if tries >= 2 and win_place_show == 0:
        return 'D', tries, rate

    # C: 1 try only, and loss
    if tries == 1 and win_place_show == 0 and lose == 1:
        return 'C', tries, rate

    # S: 3+ tries, 100% win_place_show rate
    if tries >= 3 and rate == 1.0:
        return 'S', tries, rate

    # A: 66%+ rate, OR 2-tries-or-less with a win and no loss
    if rate >= 0.66 or (tries <= 2 and win >= 1 and lose == 0):
        return 'A', tries, rate

    # B: 33-66% rate
    if 0.33 <= rate < 0.66:
        return 'B', tries, rate

    # C: <33% rate (fallback)
    return 'C', tries, rate


def build_factor(shutuba_gaikyu, gaikyu_record):
    """Compute gaikyuFactor dict for a horse.

    shutuba_gaikyu: str e.g. "ノーザンファーム天栄"
    gaikyu_record: list of {name, record}
    """
    canonical, kw = normalize_gaikyu_name(shutuba_gaikyu)
    if canonical is None:
        return {
            'grade': 'B',
            'source': 'fallback-unknown',
            'shutubaGaikyu': shutuba_gaikyu,
        }

    # Try to find matching individual record
    best_match = None
    for rec in gaikyu_record:
        cname, _ = normalize_gaikyu_name(rec['name'])
        if cname == canonical:
            best_match = rec
            break

    if best_match is None:
        # No individual record → use fallback grade
        return {
            'grade': FALLBACK_GRADE.get(canonical, 'B'),
            'source': 'fallback',
            'canonical': canonical,
            'shutubaGaikyu': shutuba_gaikyu,
        }

    grade, tries, rate = compute_grade(best_match['record'])
    if grade is None:
        return {
            'grade': FALLBACK_GRADE.get(canonical, 'B'),
            'source': 'fallback-emptyrecord',
            'canonical': canonical,
            'shutubaGaikyu': shutuba_gaikyu,
        }

    return {
        'grade': grade,
        'source': 'individual',
        'canonical': canonical,
        'shutubaGaikyu': shutuba_gaikyu,
        'record': best_match['record'],
        'recordStr': '-'.join(str(x) for x in best_match['record']),
        'tries': tries,
        'winPlaceShowRate': round(rate, 3),
    }


def process_race(race_dir, race_notes_path):
    """Process one race: update shutuba.json and race-notes JSON."""
    shutuba_path = race_dir / 'shutuba.json'
    extracted_dir = race_dir / 'extracted'

    if not shutuba_path.exists() or not extracted_dir.exists():
        print(f'skip: {race_dir} (missing shutuba or extracted)', file=sys.stderr)
        return

    shutuba = json.loads(shutuba_path.read_text(encoding='utf-8'))

    # Process each horse
    for h in shutuba.get('horses', []):
        name = h['name']
        ext_path = extracted_dir / f'{name}.json'
        if not ext_path.exists():
            # fallback-only (no PDF)
            h['gaikyuFactor'] = build_factor(h.get('gaikyu'), [])
            continue
        ext = json.loads(ext_path.read_text(encoding='utf-8'))
        h['gaikyuFactor'] = build_factor(h.get('gaikyu'), ext.get('gaikyuRecord', []))

    # Write back
    shutuba_path.write_text(
        json.dumps(shutuba, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f'→ {shutuba_path} updated')

    # Update race-notes JSON too (minimal fields)
    if race_notes_path and race_notes_path.exists():
        rn = json.loads(race_notes_path.read_text(encoding='utf-8'))
        by_name = {h['name']: h.get('gaikyuFactor') for h in shutuba.get('horses', [])}
        for h in rn.get('horses', []):
            if h['name'] in by_name:
                h['gaikyuFactor'] = by_name[h['name']]
        # Use compact one-line format for each horse (match existing style)
        race_notes_path.write_text(
            json.dumps(rn, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'→ {race_notes_path} updated')


if __name__ == '__main__':
    base = Path('/Users/buntawakase/Desktop/ug-keiba')
    RACE_MAP = [
        (base / 'analysis/2026-04-25-aobasho',
         base / 'docs/data/race-notes/2026-04-25-tokyo-11r.json'),
        (base / 'analysis/2026-04-26-floras',
         base / 'docs/data/race-notes/2026-04-26-tokyo-11r.json'),
        (base / 'analysis/2026-04-26-milers-c',
         base / 'docs/data/race-notes/2026-04-26-kyoto-11r.json'),
    ]
    for rd, rn in RACE_MAP:
        process_race(rd, rn)
