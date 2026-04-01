#!/usr/bin/env python3
"""大阪杯 2026-04-06 阪神11R — SABC採点スクリプト（8ファクター）
ファクター: 調教師 / 父 / 前走脚質 / 前走上がり3F順位 / 前走PCI / 年齢 / 馬格 / 前走-3F差
最大合計: 8 × 4pt = 32pt
"""
import json, re

NOTES_PATH   = 'docs/data/race-notes/2026-04-06-hanshin-11r.json'
PREVRACE_PATH = 'docs/data/prevrace/zensou-2026-04-06-hanshin-11r.json'

# ── SABC評価閾値 ─────────────────────────────────────────────
def sabc_tan(w):
    if w is None: return 'C'
    return 'S' if w>=15 else 'A' if w>=10 else 'B' if w>=7 else 'C'

def sabc_fuku(p):
    if p is None: return 'C'
    return 'S' if p>=35 else 'A' if p>=25 else 'B' if p>=15 else 'C'

def grade_to_pt(g): return {'S':4,'A':3,'B':2,'C':1}.get(g,1)

# ── 調教師統計（大阪杯コース：阪神芝2000m）───────────────────
trainer_stats = {
    '(栗)上村洋行':  {'win':30.8,'place':73.1},  # S/S
    '(栗)須貝尚介':  {'win':16.0,'place':40.0},  # S/S
    '(栗)斉藤崇史':  {'win':10.0,'place':33.3},  # A/A
    '(栗)友道康夫':  {'win': 6.5,'place':41.9},  # C/S
    '(栗)宮本博':    {'win':16.7,'place':33.3},  # S/A
    '(栗)石橋守':    {'win':14.3,'place':42.9},  # A/S
    '(栗)宮徹':      {'win': 4.2,'place':33.3},  # C/A
    '(栗)橋口慎介':  {'win': 5.9,'place':35.3},  # C/S
    '(栗)昆貢':      {'win': 5.0,'place':30.0},  # C/A
    '(栗)安田翔伍':  {'win': 6.3,'place':18.8},  # C/B
    '(栗)大久保龍志':{'win':10.0,'place':30.0},  # A/A
    '(美)田中博康':  {'win': 0.0,'place':33.3},  # C/A
    '(美)小島茂之':  {'win': 0.0,'place': 0.0},  # C/C
    '(栗)牧浦充徳':  {'win': 0.0,'place': 0.0},  # C/C
    '(美)堀内岳志':  {'win': 0.0,'place': 0.0},  # C/C (データなし)
}

# ── 血統（父）統計 ───────────────────────────────────────────
sire_stats = {
    'エピファネイア':    {'win':11.4,'place':31.6},  # A/A
    'キタサンブラック':  {'win':17.0,'place':31.9},  # S/A
    'シルバーステート':  {'win':17.6,'place':26.5},  # S/A
    'ブラックタイド':    {'win':20.0,'place':50.0},  # S/S
    'ハーツクライ':      {'win': 6.4,'place':31.9},  # C/A
    'ロードカナロア':    {'win':10.0,'place':36.7},  # A/S
    'ディープインパクト':{'win': 8.1,'place':24.3},  # B/B
    'リアルスティール':  {'win':12.5,'place':41.7},  # A/S
    'ゴールドシップ':    {'win': 2.6,'place':13.2},  # C/C
    'ワールドエース':    {'win':20.0,'place':20.0},  # S/B
    'スクリーンヒーロー':{'win': 0.0,'place':16.7},  # C/B
    'ヤマカツエース':    {'win': 0.0,'place':16.7},  # C/B
    'サートゥルナーリア':{'win': 0.0,'place':13.3},  # C/C
    'モズアスコット':    {'win': 0.0,'place':33.3},  # C/A
    'エイシンフラッシュ':{'win': 0.0,'place': 0.0},  # C/C
}

# ── 前走脚質統計 ─────────────────────────────────────────────
style_stats = {
    '逃げ': {'win':13.8,'place':37.2},  # A/S
    '先行': {'win':12.7,'place':32.2},  # A/A
    '中団': {'win': 8.8,'place':27.9},  # B/A
    '後方': {'win': 3.6,'place':15.4},  # C/B
    '差し': {'win': 3.6,'place':15.4},  # C/B (差し→後方と同値)
    'マクリ':{'win': 9.1,'place':22.7},  # B/B
}

# ── 前走上がり3F順位統計 ─────────────────────────────────────
rank3f_stats = {
    '1':   {'win':13.1,'place':40.8},  # A/S
    '2':   {'win':13.7,'place':40.2},  # A/S
    '3':   {'win': 6.7,'place':25.0},  # C/A
    '4-5': {'win':12.8,'place':35.0},  # A/S
    '6+':  {'win': 5.8,'place':17.2},  # C/B
}

def rank3f_bucket(r):
    if r == 1: return '1'
    if r == 2: return '2'
    if r == 3: return '3'
    if r <= 5: return '4-5'
    return '6+'

# ── PCI統計（* = 平均以上） ──────────────────────────────────
pci_stats = {
    '~44*': {'win': 0.0,'place':33.3},  # C/A
    '~52*': {'win': 9.1,'place':31.4},  # B/A
    '~60*': {'win':11.6,'place':34.5},  # A/A
    '~68*': {'win':21.4,'place':41.7},  # S/S
    '~44':  {'win': 2.1,'place':12.5},  # C/C
    '~52':  {'win': 5.8,'place':21.0},  # C/B
    '~60':  {'win': 9.7,'place':29.0},  # B/A
    '~68':  {'win':18.9,'place':38.9},  # S/S
}

def pci_band(val, above):
    suffix = '*' if above else ''
    for thr in [44, 52, 60, 68]:
        if val <= thr:
            return f'~{thr}{suffix}'
    return f'~68{suffix}'

# ── 年齢統計（4-6月期） ──────────────────────────────────────
age_stats = {
    '4':  {'win':10.3,'place':33.3},  # A/A
    '5':  {'win':10.8,'place':26.2},  # A/A
    '6':  {'win': 2.9,'place':11.8},  # C/C
    '7+': {'win': 0.0,'place': 5.7},  # C/C
}

def age_bucket(age_int):
    if age_int <= 4: return '4'
    if age_int == 5: return '5'
    if age_int == 6: return '6'
    return '7+'

# ── 馬格（前走馬体重）統計 ───────────────────────────────────
weight_stats = {
    '~439': {'win': 6.3,'place':23.2},  # C/B  (420~439)
    '~459': {'win':10.9,'place':29.0},  # A/A  (440~459)
    '~479': {'win': 7.2,'place':24.1},  # B/B  (460~479) 24.1<25→B
    '~499': {'win': 8.0,'place':28.0},  # B/A  (480~499)
    '~519': {'win':15.2,'place':31.9},  # S/A  (500~519)
    '~539': {'win': 8.3,'place':31.3},  # B/A  (520~539)
    '540+': {'win':11.1,'place':11.1},  # A/C  (540~)
}

def weight_bucket(w):
    if w is None: return None
    if w <= 439: return '~439'
    if w <= 459: return '~459'
    if w <= 479: return '~479'
    if w <= 499: return '~499'
    if w <= 519: return '~519'
    if w <= 539: return '~539'
    return '540+'

# ── 前走上がり-3F差統計 ──────────────────────────────────────
diff3f_stats = {
    '0.0-0.1': {'win':12.3,'place':33.1},  # A/A
    '0.2-0.3': {'win':16.1,'place':33.5},  # S/A
    '0.4-0.5': {'win':13.0,'place':35.6},  # A/S
    '0.6-0.7': {'win': 3.8,'place':23.1},  # C/B
    '0.8-0.9': {'win': 7.0,'place':20.3},  # B/B
    '1.0-1.2': {'win': 5.4,'place':23.1},  # C/B
    '1.3-1.5': {'win': 4.1,'place':16.4},  # C/B
    '1.6-1.9': {'win': 2.6,'place':10.3},  # C/C
    '2.0+':    {'win': 4.2,'place':12.5},  # C/C
}

def diff3f_bucket(d):
    if d is None: return None
    if d < 0: d = 0.0
    if d <= 0.1: return '0.0-0.1'
    if d <= 0.3: return '0.2-0.3'
    if d <= 0.5: return '0.4-0.5'
    if d <= 0.7: return '0.6-0.7'
    if d <= 0.9: return '0.8-0.9'
    if d <= 1.2: return '1.0-1.2'
    if d <= 1.5: return '1.3-1.5'
    if d <= 1.9: return '1.6-1.9'
    return '2.0+'

# ── 馬番 → 調教師・父 マッピング（出走予定表CSVより確認済み）─
horse_trainer = {
    1: '(栗)大久保龍志',  # エコロディノス
    2: '(栗)牧浦充徳',   # エコロヴァルツ
    3: '(美)小島茂之',   # オニャンコポン
    4: '(栗)斉藤崇史',   # クロワデュノール
    5: '(美)堀内岳志',   # サンストックトン
    6: '(栗)友道康夫',   # ショウヘイ
    7: '(栗)橋口慎介',   # セイウンハーデス
    8: '(栗)宮徹',       # タガノデュード
    9: '(栗)安田翔伍',   # ダノンデサイル
   10: '(栗)上村洋行',   # デビットバローズ
   11: '(栗)須貝尚介',   # ファウストラーゼン
   12: '(栗)宮本博',     # ボルドグフーシュ
   13: '(栗)昆貢',       # マテンロウレオ
   14: '(栗)石橋守',     # メイショウタバル
   15: '(栗)友道康夫',   # ヨーホーレイク
   16: '(美)田中博康',   # レーベンスティール
}

horse_sire = {
    1: 'キタサンブラック',  # エコロディノス
    2: 'ブラックタイド',    # エコロヴァルツ
    3: 'エイシンフラッシュ',# オニャンコポン
    4: 'キタサンブラック',  # クロワデュノール
    5: 'ワールドエース',    # サンストックトン
    6: 'サートゥルナーリア',# ショウヘイ
    7: 'シルバーステート',  # セイウンハーデス
    8: 'ヤマカツエース',    # タガノデュード
    9: 'エピファネイア',    # ダノンデサイル
   10: 'ロードカナロア',    # デビットバローズ
   11: 'モズアスコット',    # ファウストラーゼン
   12: 'スクリーンヒーロー',# ボルドグフーシュ
   13: 'ハーツクライ',      # マテンロウレオ
   14: 'ゴールドシップ',    # メイショウタバル
   15: 'ディープインパクト', # ヨーホーレイク
   16: 'リアルスティール',  # レーベンスティール
}

# ── メイン処理 ───────────────────────────────────────────────
with open(NOTES_PATH)   as f: notes   = json.load(f)
with open(PREVRACE_PATH) as f: prevraw = json.load(f)

prevmap = {h['umaban']: h for h in prevraw['horses']}
results = {}

print("=== 大阪杯 SABC採点（8ファクター / 最大32pt）===\n")

for umaban, name in sorted([(h['umaban'], h['umaname']) for h in prevraw['horses']]):
    p = prevmap[umaban]
    t_key = horse_trainer.get(umaban, 'unknown')
    s_key = horse_sire.get(umaban, 'unknown')

    # 調教師
    tr = trainer_stats.get(t_key, {'win':None,'place':None})
    trn_tan  = sabc_tan(tr['win']);   trn_fuku = sabc_fuku(tr['place'])

    # 父
    sr = sire_stats.get(s_key, {'win':None,'place':None})
    sire_tan = sabc_tan(sr['win']);  sire_fuku = sabc_fuku(sr['place'])

    # 脚質
    style = p.get('runningStyle','')
    st = style_stats.get(style, {'win':None,'place':None})
    style_tan = sabc_tan(st['win']); style_fuku = sabc_fuku(st['place'])

    # 上がり3F順位
    r3f = p.get('last3FRank')
    if r3f is not None:
        bk = rank3f_bucket(int(r3f))
        rr = rank3f_stats.get(bk, {'win':None,'place':None})
    else:
        rr = {'win':None,'place':None}
    rank_tan  = sabc_tan(rr['win']); rank_fuku = sabc_fuku(rr['place'])

    # PCI
    pci_val   = p.get('pci')
    pci_above = p.get('pciAboveAvg', False)
    if pci_val is not None:
        band = pci_band(float(pci_val), pci_above)
        pt   = pci_stats.get(band, {'win':None,'place':None})
    else:
        pt = {'win':None,'place':None}
    pci_tan  = sabc_tan(pt['win']); pci_fuku = sabc_fuku(pt['place'])

    # 年齢
    sex_age = p.get('sexAge','')
    age_m = re.search(r'(\d+)', sex_age)
    if age_m:
        ab = age_bucket(int(age_m.group(1)))
        at = age_stats.get(ab, {'win':None,'place':None})
    else:
        at = {'win':None,'place':None}
    age_tan  = sabc_tan(at['win']); age_fuku = sabc_fuku(at['place'])

    # 馬格（前走馬体重）
    wt_val = p.get('weight')
    if wt_val is not None:
        wb  = weight_bucket(int(wt_val))
        wts = weight_stats.get(wb, {'win':None,'place':None}) if wb else {'win':None,'place':None}
    else:
        wts = {'win':None,'place':None}
    wt_tan  = sabc_tan(wts['win']); wt_fuku = sabc_fuku(wts['place'])

    # 前走-3F差
    diff_val = p.get('last3FDiff')
    if diff_val is not None:
        db  = diff3f_bucket(float(diff_val))
        dts = diff3f_stats.get(db, {'win':None,'place':None}) if db else {'win':None,'place':None}
    else:
        dts = {'win':None,'place':None}
    diff_tan  = sabc_tan(dts['win']); diff_fuku = sabc_fuku(dts['place'])

    # 合計
    tan_total  = sum(grade_to_pt(g) for g in [trn_tan,sire_tan,style_tan,rank_tan,pci_tan,age_tan,wt_tan,diff_tan])
    fuku_total = sum(grade_to_pt(g) for g in [trn_fuku,sire_fuku,style_fuku,rank_fuku,pci_fuku,age_fuku,wt_fuku,diff_fuku])

    results[name] = {
        'trainer': t_key, 'sire': s_key,
        'sabc': {
            'tan':  {'trainer':trn_tan, 'sire':sire_tan, 'style':style_tan, 'last3f':rank_tan,
                     'pci':pci_tan,  'age':age_tan,  'weight':wt_tan,  'diff3f':diff_tan,  'total':tan_total},
            'fuku': {'trainer':trn_fuku,'sire':sire_fuku,'style':style_fuku,'last3f':rank_fuku,
                     'pci':pci_fuku, 'age':age_fuku, 'weight':wt_fuku, 'diff3f':diff_fuku, 'total':fuku_total},
        }
    }

    print(f"{umaban:2d} {name:20s}  {t_key} / {s_key}")
    print(f"   単勝: {trn_tan}{sire_tan}{style_tan}{rank_tan}{pci_tan}{age_tan}{wt_tan}{diff_tan} = {tan_total}pt")
    print(f"   複勝: {trn_fuku}{sire_fuku}{style_fuku}{rank_fuku}{pci_fuku}{age_fuku}{wt_fuku}{diff_fuku} = {fuku_total}pt")

# ── JSON書き込み ─────────────────────────────────────────────
for name, r in results.items():
    if name not in notes['horses']:
        notes['horses'][name] = {}
    notes['horses'][name]['sabcTrainer'] = r['trainer']
    notes['horses'][name]['sabcSire']    = r['sire']
    notes['horses'][name]['sabc']        = r['sabc']

sorted_tan  = sorted(results.items(), key=lambda x: x[1]['sabc']['tan']['total'],  reverse=True)
sorted_fuku = sorted(results.items(), key=lambda x: x[1]['sabc']['fuku']['total'], reverse=True)

notes['sabcRankTan']  = [{'name':n,'total':v['sabc']['tan']['total']}  for n,v in sorted_tan]
notes['sabcRankFuku'] = [{'name':n,'total':v['sabc']['fuku']['total']} for n,v in sorted_fuku]

with open(NOTES_PATH, 'w', encoding='utf-8') as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)

print(f"\n✓ SABC data written to {NOTES_PATH}")
print("\n=== 単勝ポイント ランキング ===")
for i,(n,v) in enumerate(sorted_tan,1):
    t = v['sabc']['tan']
    print(f"{i:2d}位 {n:20s} {t['total']}pt  [{t['trainer']}{t['sire']}{t['style']}{t['last3f']}{t['pci']}{t['age']}{t['weight']}{t['diff3f']}]")

print("\n=== 複勝ポイント ランキング ===")
for i,(n,v) in enumerate(sorted_fuku,1):
    f_ = v['sabc']['fuku']
    print(f"{i:2d}位 {n:20s} {f_['total']}pt  [{f_['trainer']}{f_['sire']}{f_['style']}{f_['last3f']}{f_['pci']}{f_['age']}{f_['weight']}{f_['diff3f']}]")
