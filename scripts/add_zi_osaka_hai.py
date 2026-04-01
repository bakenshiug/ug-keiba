#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大阪杯 ZI値をSABCに追加するスクリプト
既存の8ファクターの先頭に 'zi' を挿入し、totalを再計算する
"""

import json
import os

def zi_to_grade(zi):
    if zi >= 120:
        return 'S'
    elif zi >= 110:
        return 'A'
    elif zi >= 100:
        return 'B'
    else:
        return 'C'

def grade_to_pt(g):
    return {'S': 4, 'A': 3, 'B': 2, 'C': 1}.get(g, 1)

# ZI値データ（CSV由来）
zi_data = {
    'エコロディノス':   115,
    'エコロヴァルツ':   116,
    'オニャンコポン':    77,
    'クロワデュノール': 125,
    'サンストックトン':  88,
    'ショウヘイ':       123,
    'セイウンハーデス': 104,
    'タガノデュード':   114,
    'ダノンデサイル':   123,
    'デビットバローズ': 121,
    'ファウストラーゼン': 90,
    'ボルドグフーシュ': 111,
    'マテンロウレオ':   106,
    'メイショウタバル': 107,
    'ヨーホーレイク':   102,
    'レーベンスティール': 126,
}

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.dirname(script_dir)
notes_path = os.path.join(base_dir, 'docs', 'data', 'race-notes', '2026-04-06-hanshin-11r.json')

with open(notes_path, 'r', encoding='utf-8') as f:
    notes = json.load(f)

results_tan  = []
results_fuku = []

for name, hn in notes['horses'].items():
    zi_val = zi_data.get(name)
    if zi_val is None:
        print(f"⚠️  ZI値なし: {name}")
        continue
    if 'sabc' not in hn:
        print(f"⚠️  SABC未設定: {name}")
        continue

    zi_grade = zi_to_grade(zi_val)
    hn['sabcZI'] = zi_val

    for dim in ('tan', 'fuku'):
        old = hn['sabc'][dim]
        # totalを除いた既存ファクターをそのまま保持し、先頭にziを追加
        new = {'zi': zi_grade}
        for k, v in old.items():
            if k != 'total':
                new[k] = v
        new['total'] = sum(grade_to_pt(v) for k, v in new.items() if k != 'total')
        hn['sabc'][dim] = new

    tan_total  = hn['sabc']['tan']['total']
    fuku_total = hn['sabc']['fuku']['total']
    print(f"{name:14s}  ZI={zi_val:3d}({zi_grade})  単{tan_total:2d}pt  複{fuku_total:2d}pt")
    results_tan.append({'name': name, 'total': tan_total})
    results_fuku.append({'name': name, 'total': fuku_total})

results_tan.sort(key=lambda x: -x['total'])
results_fuku.sort(key=lambda x: -x['total'])

notes['sabcRankTan']  = results_tan
notes['sabcRankFuku'] = results_fuku

print("\n--- 単勝ランキング（ZI値込み）---")
for i, r in enumerate(results_tan[:5]):
    print(f"  {i+1}. {r['name']}: {r['total']}pt")

print("\n--- 複勝ランキング（ZI値込み）---")
for i, r in enumerate(results_fuku[:5]):
    print(f"  {i+1}. {r['name']}: {r['total']}pt")

with open(notes_path, 'w', encoding='utf-8') as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)

print(f"\n✅ {notes_path} を更新しました")
