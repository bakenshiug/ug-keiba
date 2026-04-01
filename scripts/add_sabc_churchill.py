#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
チャーチルダウンズカップ SABC分析スクリプト
8ファクター: ZI値・調教師・父・脚質・上がり3F・PCI・馬格・3F差
"""

import json

# ─── SABC グレード変換 ────────────────────────────────────────
def grade_to_pt(g):
    return {'S': 4, 'A': 3, 'B': 2, 'C': 1}.get(g, 1)

def rate_to_grade(win, place):
    """(勝率, 複勝率) → (単勝グレード, 複勝グレード)"""
    # 単勝: S≥15%, A≥10%, B≥7%, C<7%
    tan = 'S' if win >= 15 else 'A' if win >= 10 else 'B' if win >= 7 else 'C'
    # 複勝: S≥35%, A≥25%, B≥15%, C<15%
    fuku = 'S' if place >= 35 else 'A' if place >= 25 else 'B' if place >= 15 else 'C'
    return tan, fuku

def zi_to_grade(zi):
    """ZI値 → グレード（単複共通）"""
    if zi >= 120:
        return 'S'
    elif zi >= 110:
        return 'A'
    elif zi >= 100:
        return 'B'
    else:
        return 'C'

# ─── 統計データ ────────────────────────────────────────────────
trainer_stats = {
    '(栗)藤原英昭': {'win': 10.6, 'place': 23.4},
    '(栗)上村洋行': {'win': 17.9, 'place': 39.3},
    '(栗)松下武士': {'win': 16.7, 'place': 38.9},
    '(栗)中内田充': {'win':  6.5, 'place': 41.9},
    '(栗)寺島良':   {'win': 16.7, 'place': 16.7},
    '(栗)吉村圭司': {'win':  5.6, 'place': 11.1},
    '(栗)宮地貴稔': {'win':  7.7, 'place': 15.4},
    '(美)木村哲也': {'win':  0.0, 'place': 30.0},
    '(栗)角田晃一': {'win':  0.0, 'place': 30.0},
    '(栗)武英智':   {'win':  0.0, 'place':  0.0},
    '(栗)安達昭夫': {'win':  0.0, 'place':  0.0},
    '(栗)森秀行':   {'win':  0.0, 'place':  0.0},
    '(美)斎藤誠':   {'win':  0.0, 'place':  0.0},
    '(美)上原佑紀': {'win':  0.0, 'place':  0.0},
}

sire_stats = {
    'ロードカナロア':       {'win': 10.0, 'place': 30.0},
    'キズナ':             {'win': 11.0, 'place': 27.0},
    'レイデオロ':          {'win': 14.8, 'place': 18.5},
    'オルフェーヴル':       {'win': 15.4, 'place': 15.4},
    'サートゥルナーリア':   {'win': 12.0, 'place': 24.0},
    'Kingman':           {'win': 40.0, 'place': 40.0},
    'ダノンプレミアム':     {'win': 12.5, 'place': 37.5},
    'モズアスコット':       {'win':  6.7, 'place':  6.7},
    'イスラボニータ':       {'win':  0.0, 'place': 30.2},
    'シスキン':            {'win':  0.0, 'place': 33.3},
    'American Pharoah':  {'win':  0.0, 'place': 50.0},
    'フォーウィールドライブ': {'win': 0.0, 'place':  0.0},
    'アルアイン':          {'win':  0.0, 'place':  0.0},
    'ヘンリーバローズ':     {'win':  0.0, 'place':  0.0},
}

style_stats = {
    '逃げ': {'win': 4.8,  'place': 19.0},
    '先行': {'win': 9.9,  'place': 27.7},
    '中団': {'win': 6.9,  'place': 23.6},
    '後方': {'win': 6.4,  'place': 16.8},
    '差し': {'win': 6.4,  'place': 16.8},
}

rank3f_stats = {
    '1':   {'win': 10.3, 'place': 31.3},
    '2':   {'win': 12.0, 'place': 30.4},
    '3':   {'win': 13.3, 'place': 29.3},
    '4-5': {'win':  9.2, 'place': 26.4},
    '6+':  {'win':  4.5, 'place': 17.0},
}

# PCI: aboveAvg=True → * バージョンを使用
pci_stats = {
    '~44_above':  {'win':  8.3, 'place': 16.7},
    '~52_above':  {'win':  8.4, 'place': 26.1},
    '~60_above':  {'win':  8.8, 'place': 27.2},
    '~68_above':  {'win': 18.1, 'place': 30.6},
    '~44_below':  {'win':  5.0, 'place': 11.9},
    '~52_below':  {'win':  6.2, 'place': 20.6},
    '~60_below':  {'win':  8.1, 'place': 25.6},
    '~68_below':  {'win': 16.3, 'place': 27.5},
}

weight_stats = {
    '~399': {'win':  7.1, 'place':  7.1},
    '~419': {'win':  7.1, 'place':  7.1},
    '~439': {'win':  4.4, 'place': 16.9},
    '~459': {'win':  6.2, 'place': 20.3},
    '~479': {'win':  7.1, 'place': 24.8},
    '~499': {'win': 10.2, 'place': 26.2},
    '~519': {'win':  9.3, 'place': 26.7},
    '~539': {'win':  9.6, 'place': 23.1},
    '540+': {'win': 12.5, 'place': 37.5},
}

diff3f_stats = {
    '0.0-0.1': {'win': 6.5,  'place': 20.5},
    '0.2-0.3': {'win': 9.0,  'place': 28.9},
    '0.4-0.5': {'win': 11.4, 'place': 32.1},
    '0.6-0.7': {'win': 7.8,  'place': 22.0},
    '0.8-0.9': {'win': 8.6,  'place': 21.0},
    '1.0-1.2': {'win': 4.3,  'place': 16.8},
    '1.3-1.5': {'win': 5.5,  'place': 18.1},
    '1.6-1.9': {'win': 3.4,  'place': 11.5},
    '2.0+':    {'win': 2.7,  'place': 21.6},
}

# ─── 各馬データ ────────────────────────────────────────────────
horse_trainer = {
     1: '(栗)藤原英昭',
     2: '(栗)中内田充',
     3: '(栗)吉村圭司',
     4: '(栗)宮地貴稔',
     5: '(栗)武英智',
     6: '(栗)上村洋行',
     7: '(美)木村哲也',
     8: '(栗)寺島良',
     9: '(栗)安達昭夫',
    10: '(栗)松下武士',
    11: '(美)斎藤誠',
    12: '(栗)角田晃一',
    13: '(栗)森秀行',
    14: '(美)上原佑紀',
    15: '(栗)松下武士',
}

horse_sire = {
     1: 'ロードカナロア',
     2: 'サートゥルナーリア',
     3: 'モズアスコット',
     4: 'フォーウィールドライブ',
     5: 'レイデオロ',
     6: 'Kingman',
     7: 'ロードカナロア',
     8: 'オルフェーヴル',
     9: 'ヘンリーバローズ',
    10: 'キズナ',
    11: 'アルアイン',
    12: 'シスキン',
    13: 'American Pharoah',
    14: 'イスラボニータ',
    15: 'ダノンプレミアム',
}

horse_zi = {
     1: 107,
     2: 127,
     3:  97,
     4: 102,
     5:  93,
     6:  87,
     7: 123,
     8: 100,
     9:  98,
    10: 108,
    11: 100,
    12:  96,
    13:  80,
    14: 119,
    15: 114,
}

# ─── ヘルパー関数 ────────────────────────────────────────────────
def get_pci_key(pci, above_avg):
    suffix = '_above' if above_avg else '_below'
    if pci <= 44:
        return '~44' + suffix
    elif pci <= 52:
        return '~52' + suffix
    elif pci <= 60:
        return '~60' + suffix
    else:
        return '~68' + suffix

def get_weight_key(weight):
    if weight <= 399:
        return '~399'
    elif weight <= 419:
        return '~419'
    elif weight <= 439:
        return '~439'
    elif weight <= 459:
        return '~459'
    elif weight <= 479:
        return '~479'
    elif weight <= 499:
        return '~499'
    elif weight <= 519:
        return '~519'
    elif weight <= 539:
        return '~539'
    else:
        return '540+'

def get_rank3f_key(rank):
    if rank == 1:
        return '1'
    elif rank == 2:
        return '2'
    elif rank == 3:
        return '3'
    elif rank <= 5:
        return '4-5'
    else:
        return '6+'

def get_diff3f_key(diff):
    if diff <= 0.1:
        return '0.0-0.1'
    elif diff <= 0.3:
        return '0.2-0.3'
    elif diff <= 0.5:
        return '0.4-0.5'
    elif diff <= 0.7:
        return '0.6-0.7'
    elif diff <= 0.9:
        return '0.8-0.9'
    elif diff <= 1.2:
        return '1.0-1.2'
    elif diff <= 1.5:
        return '1.3-1.5'
    elif diff <= 1.9:
        return '1.6-1.9'
    else:
        return '2.0+'

# ─── prevrace JSONを読み込み ─────────────────────────────────────
import os, sys

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

prevrace_path = os.path.join(base_dir, 'docs', 'data', 'prevrace', 'zensou-2026-04-05-hanshin-11r.json')
notes_path    = os.path.join(base_dir, 'docs', 'data', 'race-notes', '2026-04-05-hanshin-11r.json')

with open(prevrace_path, 'r', encoding='utf-8') as f:
    prevrace = json.load(f)

with open(notes_path, 'r', encoding='utf-8') as f:
    notes = json.load(f)

# ─── SABC 計算 ──────────────────────────────────────────────────
results_tan  = []
results_fuku = []

for horse in prevrace['horses']:
    n = horse['umaban']
    name = horse['umaname']

    trainer = horse_trainer[n]
    sire    = horse_sire[n]
    zi_val  = horse_zi[n]
    style   = horse['runningStyle']
    rank3f  = horse['last3FRank']
    pci     = horse['pci']
    above   = horse['pciAboveAvg']
    weight  = horse['weight']
    diff3f  = horse['last3FDiff']

    # ZI値グレード（単複共通）
    zi_g = zi_to_grade(zi_val)

    # 調教師
    ts = trainer_stats.get(trainer, {'win': 0.0, 'place': 0.0})
    trn_tan, trn_fuku = rate_to_grade(ts['win'], ts['place'])

    # 父
    ss = sire_stats.get(sire, {'win': 0.0, 'place': 0.0})
    sire_tan, sire_fuku = rate_to_grade(ss['win'], ss['place'])

    # 脚質
    st = style_stats.get(style, {'win': 0.0, 'place': 0.0})
    style_tan, style_fuku = rate_to_grade(st['win'], st['place'])

    # 上がり3F順位
    r3k = get_rank3f_key(rank3f)
    rs = rank3f_stats[r3k]
    rank_tan, rank_fuku = rate_to_grade(rs['win'], rs['place'])

    # PCI
    pci_key = get_pci_key(pci, above)
    ps = pci_stats[pci_key]
    pci_tan, pci_fuku = rate_to_grade(ps['win'], ps['place'])

    # 馬格（前走体重）
    wt_key = get_weight_key(weight)
    ws = weight_stats[wt_key]
    wt_tan, wt_fuku = rate_to_grade(ws['win'], ws['place'])

    # 3F差
    dk = get_diff3f_key(diff3f)
    ds = diff3f_stats[dk]
    diff_tan, diff_fuku = rate_to_grade(ds['win'], ds['place'])

    # 合計
    tan_grades  = [zi_g, trn_tan,  sire_tan,  style_tan,  rank_tan,  pci_tan,  wt_tan,  diff_tan]
    fuku_grades = [zi_g, trn_fuku, sire_fuku, style_fuku, rank_fuku, pci_fuku, wt_fuku, diff_fuku]

    tan_total  = sum(grade_to_pt(g) for g in tan_grades)
    fuku_total = sum(grade_to_pt(g) for g in fuku_grades)

    sabc = {
        'tan': {
            'zi':      zi_g,
            'trainer': trn_tan,
            'sire':    sire_tan,
            'style':   style_tan,
            'last3f':  rank_tan,
            'pci':     pci_tan,
            'weight':  wt_tan,
            'diff3f':  diff_tan,
            'total':   tan_total,
        },
        'fuku': {
            'zi':      zi_g,
            'trainer': trn_fuku,
            'sire':    sire_fuku,
            'style':   style_fuku,
            'last3f':  rank_fuku,
            'pci':     pci_fuku,
            'weight':  wt_fuku,
            'diff3f':  diff_fuku,
            'total':   fuku_total,
        }
    }

    # notes.horses に書き込み
    if name not in notes['horses']:
        notes['horses'][name] = {}
    notes['horses'][name]['sabc'] = sabc
    notes['horses'][name]['sabcTrainer'] = trainer
    notes['horses'][name]['sabcSire'] = sire
    notes['horses'][name]['sabcZI'] = zi_val

    results_tan.append({'name': name, 'total': tan_total, 'sabc': sabc})
    results_fuku.append({'name': name, 'total': fuku_total, 'sabc': sabc})

    print(f"{n:2d} {name:12s}  ZI={zi_val:3d}({zi_g})  単{tan_total:2d}pt  複{fuku_total:2d}pt")

# ─── ランキング ──────────────────────────────────────────────────
results_tan.sort(key=lambda x: -x['total'])
results_fuku.sort(key=lambda x: -x['total'])

notes['sabcRankTan']  = [{'name': r['name'], 'total': r['total']} for r in results_tan]
notes['sabcRankFuku'] = [{'name': r['name'], 'total': r['total']} for r in results_fuku]

print("\n--- 単勝ランキング ---")
for i, r in enumerate(results_tan[:5]):
    print(f"  {i+1}. {r['name']}: {r['total']}pt")

print("\n--- 複勝ランキング ---")
for i, r in enumerate(results_fuku[:5]):
    print(f"  {i+1}. {r['name']}: {r['total']}pt")

# ─── JSON保存 ────────────────────────────────────────────────────
with open(notes_path, 'w', encoding='utf-8') as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)

print(f"\n✅ {notes_path} を更新しました")
