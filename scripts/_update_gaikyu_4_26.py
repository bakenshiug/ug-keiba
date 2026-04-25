#!/usr/bin/env python3
"""
4/26 picks 外厩データ手動書込（JRDB取得済3レース分）
"""
import json
from pathlib import Path

RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'

# {race_key: {horse_name: gaikyu_string}}
GAIKYU = {
    '2026-04-26-kyoto-10r': {  # センテニアル・PS
        'レイニング':         'ノーザンF天栄',
        'ミスタージーティー': 'チャンピオンヒルズ',
        'ショウナンラピダス': 'KSトレーニングセンター',
        'レディーミコノス':   '社台F鈴鹿',
    },
    '2026-04-26-kyoto-11r': {  # マイラーズC
        'ベラジオボンド':     '在厩',
        'アドマイヤズーム':   '山元トレセン',
        'エルトンバローズ':   'チャンピオンヒルズ',
        'ショウナンアデイブ': 'ノーザンFしがらき',
    },
    '2026-04-26-tokyo-11r': {  # フローラS
        'エンネ':             'チャンピオンヒルズ',
        'ラフターラインズ':   'ノーザンF天栄',
        'ペイシャシス':       'チャンピオンヒルズ',
        'サムシングスイート': 'チャンピオンヒルズ',
    },
}


def update(race_key, mapping):
    p = RN_DIR / f'{race_key}.json'
    d = json.load(open(p))
    pres = d.get('presentation', {})
    for h in pres.get('horses', []):
        g = mapping.get(h.get('name'))
        if g:
            h['gaikyu'] = g
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'  ✓ {race_key}')
    for h in pres.get('horses', []):
        print(f'    {h["godEmoji"]} {h["name"]:<14} 外厩: {h.get("gaikyu","—")}')


for k, m in GAIKYU.items():
    update(k, m)
