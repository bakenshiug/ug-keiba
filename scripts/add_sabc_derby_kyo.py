#!/usr/bin/env python3
"""
Derby Kyo CT 2026 SABC Analysis Script
5 factors x 2 dimensions (tan/fuku) -> SABC grade -> update race-notes JSON
"""

import csv, json, re
from pathlib import Path

RACE_NOTES  = Path('docs/data/race-notes/2026-04-05-nakayama-11r.json')
PREVRACE    = Path('docs/data/prevrace/zensou-2026-04-05-nakayama-11r.json')
TRAINER_CSV = Path('/Users/buntawakase/Downloads/derbykyo_trainer.csv')
SIRE_CSV    = Path('/Users/buntawakase/Downloads/derbykyo_sire.csv')

# SABC thresholds
def sabc_tan(rate):
    if rate is None: return 'C'
    if rate >= 15.0: return 'S'
    if rate >= 10.0: return 'A'
    if rate >=  7.0: return 'B'
    return 'C'

def sabc_fuku(rate):
    if rate is None: return 'C'
    if rate >= 35.0: return 'S'
    if rate >= 25.0: return 'A'
    if rate >= 15.0: return 'B'
    return 'C'

def grade_to_pt(g):
    return {'S': 4, 'A': 3, 'B': 2, 'C': 1}.get(g, 1)

def pct(s):
    try: return float(str(s).strip('%'))
    except: return None

# ── Trainer stats (hardcoded from CSV) ─────────────────────────
trainer_stats = {
    '(美)堀宣行':   {'win': 26.7, 'place': 63.3},
    '(美)辻哲英':   {'win': 20.7, 'place': 41.4},
    '(栗)池江泰寿': {'win': 18.8, 'place': 31.3},
    '(栗)高橋義忠': {'win': 12.5, 'place': 25.0},
    '(栗)杉山佳明': {'win': 12.5, 'place': 12.5},
    '(栗)友道康夫': {'win': 11.1, 'place': 33.3},
    '(美)斎藤誠':   {'win':  9.6, 'place': 38.5},
    '(美)戸田博文': {'win':  8.3, 'place': 25.0},
    '(栗)須貝尚介': {'win':  8.3, 'place': 33.3},
    '(美)伊藤大士': {'win':  7.4, 'place': 25.9},
    '(美)栗田徹':   {'win':  7.0, 'place': 25.6},
    '(美)中川公成': {'win':  6.9, 'place': 24.1},
    '(美)高木登':   {'win':  6.1, 'place': 18.2},
    '(美)堀内岳志': {'win':  4.2, 'place': 20.8},
    '(美)田中勝春': {'win':  0.0, 'place': 27.3},
    '(栗)牧田和弥': {'win':  0.0, 'place': 57.1},
    '(栗)千田輝彦': {'win':  0.0, 'place': 14.3},
    '(栗)藤原英昭': {'win':  0.0, 'place': 16.7},
    '(栗)昆貢':     {'win':  0.0, 'place':  0.0},
    '(栗)平田修':   {'win':  0.0, 'place':  0.0},
}

# ── Sire stats (hardcoded from CSV) ────────────────────────────
sire_stats = {
    'ディープインパクト': {'win': 17.5, 'place': 27.5},
    'ファインニードル':   {'win': 16.7, 'place': 26.7},
    'シルバーステート':   {'win': 13.7, 'place': 34.7},
    'キズナ':             {'win': 13.3, 'place': 33.7},
    'マクフィ':           {'win': 12.5, 'place': 16.7},
    'ロードカナロア':     {'win': 12.3, 'place': 33.5},
    'リオンディーズ':     {'win': 11.9, 'place': 13.6},
    'ドレフォン':         {'win': 10.2, 'place': 24.5},
    'ラブリーデイ':       {'win':  9.1, 'place': 15.2},
    'ブラックタイド':     {'win':  8.0, 'place': 24.0},
    'エピファネイア':     {'win':  7.4, 'place': 24.8},
    'ダイワメジャー':     {'win':  7.1, 'place': 16.1},
    'サトノダイヤモンド': {'win':  2.3, 'place':  9.3},
    'ハーツクライ':       {'win':  0.0, 'place': 16.7},
    'ゴールドシップ':     {'win':  0.0, 'place':  3.7},
    'ワールドエース':     {'win':  0.0, 'place':  6.3},
}

# ── Running style stats ─────────────────────────────────────────
style_stats = {
    '先行': {'win': 11.6, 'place': 30.2},
    '逃げ': {'win':  9.9, 'place': 24.0},
    'マクリ': {'win': 6.7, 'place': 26.7},
    '中団': {'win':  5.7, 'place': 21.3},
    '後方': {'win':  4.0, 'place': 13.8},
    '差し': {'win':  4.0, 'place': 13.8},  # 後方と同等
}

# ── 3F rank stats ───────────────────────────────────────────────
rank3f_stats = {
    '1':   {'win': 15.5, 'place': 42.2},
    '2':   {'win': 10.3, 'place': 30.0},
    '3':   {'win':  7.7, 'place': 27.9},
    '4-5': {'win': 10.4, 'place': 27.0},
    '6+':  {'win':  4.8, 'place': 15.9},
}

# ── Age stats (4-6月 period = April race) ──────────────────────
# Source: ダービー卿年齢.csv 4歳・4-6月 / 5歳・4-6月 / 6歳・4-6月 / 7歳以上
age_stats = {
    '4':  {'win': 13.2, 'place': 28.9},  # A / A
    '5':  {'win':  3.3, 'place': 23.3},  # C / B
    '6':  {'win':  0.0, 'place': 14.3},  # C / C
    '7+': {'win':  1.4, 'place':  5.5},  # C / C
}

def age_bucket(age_int):
    if age_int <= 4: return '4'
    if age_int == 5: return '5'
    if age_int == 6: return '6'
    return '7+'

# ── PCI band stats (with * = above avg) ─────────────────────────
# Bands: ~44*, ~52*, ~60*, ~68*, ~44, ~52, ~60, ~68
pci_stats = {
    '~44*': {'win':  0.0, 'place': 30.8},
    '~52*': {'win':  8.2, 'place': 25.3},
    '~60*': {'win': 10.2, 'place': 29.0},
    '~68*': {'win': 13.5, 'place': 38.3},
    '~44':  {'win':  3.8, 'place': 16.0},
    '~52':  {'win':  5.8, 'place': 18.8},
    '~60':  {'win':  8.9, 'place': 25.3},
    '~68':  {'win': 12.2, 'place': 35.4},
}

def pci_band(pci_val, above_avg):
    suffix = '*' if above_avg else ''
    for upper in [44, 52, 60, 68]:
        if pci_val <= upper:
            k = f'~{upper}{suffix}'
            if k in pci_stats:
                return k
    return f'~68{suffix}'

def rank3f_bucket(rank):
    if rank == 1: return '1'
    if rank == 2: return '2'
    if rank == 3: return '3'
    if rank <= 5: return '4-5'
    return '6+'

# ── Horse -> Trainer/Sire mapping ──────────────────────────────
horse_trainer = {
     1: '(美)辻哲英',
     2: '(美)伊藤大士',
     3: '(美)高木登',
     4: '(栗)高橋義忠',
     5: '(栗)平田修',
     6: '(美)堀宣行',
     7: '(美)堀内岳志',
     8: '(美)田中勝春',
     9: '(栗)友道康夫',
    10: '(栗)牧田和弥',
    11: '(栗)池江泰寿',
    12: '(美)戸田博文',
    13: '(美)中川公成',
    14: '(栗)千田輝彦',
    15: '(栗)藤原英昭',
    16: '(栗)須貝尚介',
    17: '(栗)昆貢',
    18: '(美)高木登',
    19: '(栗)杉山佳明',
    20: '(美)斎藤誠',
    21: '(美)栗田徹',
}

horse_sire = {
     1: 'マクフィ',
     2: 'シルバーステート',
     3: 'ドレフォン',
     4: 'ファインニードル',
     5: 'ディープインパクト',
     6: 'ディープインパクト',
     7: 'ワールドエース',
     8: 'マクフィ',
     9: 'ワールドエース',
    10: 'サトノダイヤモンド',
    11: 'ラブリーデイ',
    12: 'ロードカナロア',
    13: 'ブラックタイド',
    14: 'キズナ',
    15: 'ハーツクライ',
    16: 'リオンディーズ',
    17: 'ダイワメジャー',
    18: 'ゴールドシップ',
    19: 'エピファネイア',
    20: 'シルバーステート',
    21: 'ロードカナロア',
}

# ── Load JSONs ─────────────────────────────────────────────────
with open(PREVRACE) as f:
    prevraw = json.load(f)
prevmap = {h['umaban']: h for h in prevraw['horses']}
umaban_to_name = {h['umaban']: h['umaname'] for h in prevraw['horses']}

with open(RACE_NOTES) as f:
    notes = json.load(f)

# ── Score each horse ───────────────────────────────────────────
results = {}

for umaban in range(1, 22):
    name = umaban_to_name.get(umaban)
    if not name:
        continue
    p = prevmap.get(umaban, {})

    t_key  = horse_trainer.get(umaban, '')
    s_key  = horse_sire.get(umaban, '')

    # Trainer
    t = trainer_stats.get(t_key, {'win': None, 'place': None})
    trn_tan  = sabc_tan(t['win'])
    trn_fuku = sabc_fuku(t['place'])

    # Sire
    s = sire_stats.get(s_key, {'win': None, 'place': None})
    sire_tan  = sabc_tan(s['win'])
    sire_fuku = sabc_fuku(s['place'])

    # Style
    style = p.get('runningStyle', '')
    st = style_stats.get(style, {'win': 4.0, 'place': 13.8})
    style_tan  = sabc_tan(st['win'])
    style_fuku = sabc_fuku(st['place'])

    # 3F rank
    rank3f = p.get('last3FRank')
    if rank3f:
        bucket = rank3f_bucket(rank3f)
        rt = rank3f_stats.get(bucket, {'win': None, 'place': None})
    else:
        rt = {'win': None, 'place': None}
    rank_tan  = sabc_tan(rt['win'])
    rank_fuku = sabc_fuku(rt['place'])

    # PCI
    pci_val   = p.get('pci')
    pci_above = p.get('pciAboveAvg', False)
    if pci_val is not None:
        band = pci_band(pci_val, pci_above)
        pt = pci_stats.get(band, {'win': None, 'place': None})
    else:
        pt = {'win': None, 'place': None}
    pci_tan  = sabc_tan(pt['win'])
    pci_fuku = sabc_fuku(pt['place'])

    # Age
    sex_age = p.get('sexAge', '')
    age_m = re.search(r'(\d+)', sex_age)
    if age_m:
        age_int = int(age_m.group(1))
        bucket_a = age_bucket(age_int)
        at = age_stats.get(bucket_a, {'win': None, 'place': None})
    else:
        at = {'win': None, 'place': None}
    age_tan  = sabc_tan(at['win'])
    age_fuku = sabc_fuku(at['place'])

    tan_total  = sum(grade_to_pt(g) for g in [trn_tan, sire_tan, style_tan, rank_tan, pci_tan, age_tan])
    fuku_total = sum(grade_to_pt(g) for g in [trn_fuku, sire_fuku, style_fuku, rank_fuku, pci_fuku, age_fuku])

    results[name] = {
        'trainer': t_key,
        'sire': s_key,
        'sabc': {
            'tan':  {'trainer': trn_tan,  'sire': sire_tan,  'style': style_tan,  'last3f': rank_tan,  'pci': pci_tan,  'age': age_tan,  'total': tan_total},
            'fuku': {'trainer': trn_fuku, 'sire': sire_fuku, 'style': style_fuku, 'last3f': rank_fuku, 'pci': pci_fuku, 'age': age_fuku, 'total': fuku_total},
        }
    }

    print(f"{umaban:2d} {name:20s}  {t_key} / {s_key}")
    print(f"   単勝: {trn_tan}{sire_tan}{style_tan}{rank_tan}{pci_tan}{age_tan} = {tan_total}pt")
    print(f"   複勝: {trn_fuku}{sire_fuku}{style_fuku}{rank_fuku}{pci_fuku}{age_fuku} = {fuku_total}pt")

# ── Write to race-notes JSON ───────────────────────────────────
for name, r in results.items():
    if name in notes['horses']:
        notes['horses'][name]['sabcTrainer'] = r['trainer']
        notes['horses'][name]['sabcSire']    = r['sire']
        notes['horses'][name]['sabc']        = r['sabc']

sorted_tan  = sorted(results.items(), key=lambda x: -x[1]['sabc']['tan']['total'])
sorted_fuku = sorted(results.items(), key=lambda x: -x[1]['sabc']['fuku']['total'])
notes['sabcRankTan']  = [{'name': n, 'total': v['sabc']['tan']['total']}  for n, v in sorted_tan]
notes['sabcRankFuku'] = [{'name': n, 'total': v['sabc']['fuku']['total']} for n, v in sorted_fuku]

with open(RACE_NOTES, 'w', encoding='utf-8') as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)

print(f"\n✓ SABC data written to {RACE_NOTES}")
print("\n=== 単勝ポイント ランキング ===")
for i, (n, v) in enumerate(sorted_tan, 1):
    print(f"{i:2d}位 {n:20s} {v['sabc']['tan']['total']}pt  [{v['sabc']['tan']['trainer']}{v['sabc']['tan']['sire']}{v['sabc']['tan']['style']}{v['sabc']['tan']['last3f']}{v['sabc']['tan']['pci']}{v['sabc']['tan']['age']}]")
print("\n=== 複勝ポイント ランキング ===")
for i, (n, v) in enumerate(sorted_fuku, 1):
    print(f"{i:2d}位 {n:20s} {v['sabc']['fuku']['total']}pt  [{v['sabc']['fuku']['trainer']}{v['sabc']['fuku']['sire']}{v['sabc']['fuku']['style']}{v['sabc']['fuku']['last3f']}{v['sabc']['fuku']['pci']}{v['sabc']['fuku']['age']}]")
