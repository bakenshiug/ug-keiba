#!/usr/bin/env python3
"""
WIN1-4 玄武v2 外厩スコア付与スクリプト（PoC）
- Nick Doctrine: 非社台×CH → +2ブースト（コア）
- ニック印象「地方馬×CH激アツ」対応: 地方所属×CH → +1追加
- NF生産×中1週連闘 → +1 (「1戦必勝」哲学)
- 長欠/高齢ペナルティ
- 自厩舎◎×ピンポイント外厩 → +1
"""
import json
import os

RACE_NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'

FILES = {
    '2026-04-25-kyoto-10r.json':     'kangetsu',
    '2026-04-25-tokyo-10r.json':     'kamakura',
    '2026-04-25-fukushima-11r.json': 'fukushima',
    '2026-04-25-kyoto-11r.json':     'tenouzan',
}

# 外厩DB: (外厩名, 中N週, 生産, 所属, 自厩舎◎, 年齢, 備考)
GAIKYU_DB = {
    'kangetsu': {
        'デルアヴァー':       {'g':'—',                  'w':2,  'prod':'North Hills Co.', 'align':'栗東', 'age':4, 'honmei':True,  'note':''},
        'マイノワール':       {'g':'—',                  'w':3,  'prod':'フジワラファーム','align':'栗東', 'age':5, 'honmei':False, 'note':''},
        'ペンナヴェローチェ': {'g':'—',                  'w':1,  'prod':'千代田牧場',      'align':'栗東', 'age':5, 'honmei':False, 'note':'連闘気味'},
        'ピエマンソン':       {'g':'キャニオンファーム土山','w':4, 'prod':'高昭牧場',        'align':'栗東', 'age':4, 'honmei':False, 'note':''},
        'ショウサンジョージ': {'g':'宇治田原優駿S',       'w':12, 'prod':'モリナガF',       'align':'栗東', 'age':4, 'honmei':False, 'note':''},
        'ケイアイメキラ':     {'g':'チャンピオンヒルズ',   'w':5,  'prod':'佐竹学',          'align':'栗東', 'age':6, 'honmei':False, 'note':'セ6歳'},
        'プルナチャンドラ':   {'g':'シンボリ牧場',        'w':12, 'prod':'信田牧場',        'align':'美浦', 'age':5, 'honmei':False, 'note':''},
        'プロミシングスター': {'g':'宇治田原優駿S',       'w':17, 'prod':'富田牧場',        'align':'栗東', 'age':5, 'honmei':False, 'note':''},
        'タガノマカシヤ':     {'g':'宇治田原優駿S',       'w':7,  'prod':'八木牧場',        'align':'栗東', 'age':4, 'honmei':False, 'note':''},
        'パシアンジャン':     {'g':'山岡トレセン',        'w':14, 'prod':'前谷武志',        'align':'栗東', 'age':5, 'honmei':False, 'note':''},
        'アラレタバシル':     {'g':'—',                  'w':3,  'prod':'トラストスリーF', 'align':'美浦', 'age':5, 'honmei':False, 'note':''},
    },
    'kamakura': {
        'ピックアップライン': {'g':'山元トレセン',        'w':7,  'prod':'社台F',           'align':'美浦', 'age':6, 'honmei':False, 'note':'社台F生産'},
        'クインズデネブ':     {'g':'阿見トレセン',        'w':4,  'prod':'隆栄牧場',        'align':'美浦', 'age':5, 'honmei':False, 'note':''},
        'ラストシャリナ':     {'g':'—',                  'w':3,  'prod':'藤春修二',        'align':'美浦', 'age':4, 'honmei':False, 'note':''},
        'メイショウハチロー': {'g':'キャニオンファーム土山','w':9, 'prod':'三嶋牧場',        'align':'栗東', 'age':4, 'honmei':False, 'note':'川田騎乗'},
        'ベンヌ':             {'g':'ミッドウェイF',       'w':9,  'prod':'ダーレージャパンF','align':'美浦', 'age':4, 'honmei':False, 'note':'ゴドルフィン'},
        'トクシーカイザー':   {'g':'阿見トレセン',        'w':9,  'prod':'前田F',           'align':'美浦', 'age':6, 'honmei':True,  'note':'自厩舎◎・武豊'},
        'スプランドゥール':   {'g':'—',                  'w':1,  'prod':'荻伏服部牧場',    'align':'美浦', 'age':5, 'honmei':False, 'note':'連闘'},
        'カネショウレジェン': {'g':'KSトレーニングC',     'w':4,  'prod':'斉藤英牧場',      'align':'美浦', 'age':4, 'honmei':False, 'note':'ルメール'},
        'エンセリオ':         {'g':'阿見トレセン',        'w':37, 'prod':'土居牧場',        'align':'美浦', 'age':5, 'honmei':False, 'note':'超長欠'},
        'シャパリュ':         {'g':'山元トレセン',        'w':20, 'prod':'追分F',           'align':'美浦', 'age':5, 'honmei':False, 'note':'長欠'},
        'レーウィン':         {'g':'チャンピオンヒルズ',   'w':9,  'prod':'高昭牧場',        'align':'大井', 'age':5, 'honmei':False, 'note':'🔥地方×CH'},
        'フウセツ':           {'g':'ミッドウェイF',       'w':12, 'prod':'ダーレージャパンF','align':'美浦', 'age':4, 'honmei':False, 'note':'ゴドルフィン'},
        'イノセントキャット': {'g':'山元トレセン',        'w':26, 'prod':'追分F',           'align':'美浦', 'age':5, 'honmei':False, 'note':'超長欠'},
        'ワンダラー':         {'g':'—',                  'w':1,  'prod':'大島牧場',        'align':'豪州', 'age':4, 'honmei':False, 'note':'連闘レーン'},
        'ペイシャケイプ':     {'g':'ドラゴンファーム',    'w':8,  'prod':'友田牧場',        'align':'栗東', 'age':4, 'honmei':False, 'note':'横山典'},
    },
    'fukushima': {
        'ジェネラーレ':       {'g':'フォレストヒル',      'w':7,  'prod':"Hill 'N' Dale",  'align':'栗東', 'age':5, 'honmei':False, 'note':'米生産'},
        'イマージョン':       {'g':'—',                  'w':1,  'prod':'ノーザンF',       'align':'栗東', 'age':4, 'honmei':False, 'note':'NF×連闘'},
        'キタノソワレ':       {'g':'—',                  'w':1,  'prod':'対馬正',          'align':'美浦', 'age':5, 'honmei':False, 'note':'連闘'},
        'スノーサイレンス':   {'g':'ダーレー・ジャパン岡山','w':11,'prod':'ダーレージャパンF','align':'栗東', 'age':4, 'honmei':False, 'note':'ゴドルフィン'},
        'ビルカール':         {'g':'KSトレーニングC',     'w':6,  'prod':'サンローゼン',    'align':'美浦', 'age':6, 'honmei':False, 'note':''},
        'ワークソング':       {'g':'チャンピオンヒルズ',   'w':16, 'prod':'雅牧場',          'align':'栗東', 'age':5, 'honmei':False, 'note':'CH×長欠'},
        'ゴールドハンマー':   {'g':'高橋トレーニングC',   'w':13, 'prod':'グランド牧場',    'align':'美浦', 'age':4, 'honmei':False, 'note':''},
        'プレゼンティーア':   {'g':'島上牧場',            'w':1,  'prod':'モリナガF',       'align':'栗東', 'age':5, 'honmei':False, 'note':'連闘'},
        'サザンエルフ':       {'g':'KSトレーニングC',     'w':7,  'prod':'日西牧場',        'align':'美浦', 'age':7, 'honmei':False, 'note':'7歳牝'},
        'シャカシャカシー':   {'g':'チャンピオンヒルズ',   'w':10, 'prod':'木村牧場',        'align':'栗東', 'age':5, 'honmei':False, 'note':'CH'},
        'ルージュアズライト': {'g':'エスティF小見川',     'w':7,  'prod':'下河辺牧場',      'align':'美浦', 'age':6, 'honmei':True,  'note':'自厩舎◎・照準'},
        'カウスリップ':       {'g':'シンボリ牧場',        'w':16, 'prod':'ケイアイF',       'align':'美浦', 'age':4, 'honmei':False, 'note':'長欠'},
    },
    'tenouzan': {
        'ケイアイアニラ':     {'g':'チャンピオンヒルズ',   'w':65, 'prod':'佐竹学',          'align':'栗東', 'age':6, 'honmei':False, 'note':'CH×超長欠1年3ヶ月'},
        'ジュンウィンダム':   {'g':'—',                  'w':0,  'prod':'芳住鉄兵',        'align':'栗東', 'age':6, 'honmei':False, 'note':'連闘'},
        'ペプチドヤマト':     {'g':'チャンピオンヒルズ',   'w':10, 'prod':'杵臼牧場',        'align':'栗東', 'age':7, 'honmei':False, 'note':'CH×7歳'},
        'オーブルクール':     {'g':'松風馬事センター',    'w':13, 'prod':'中島牧場',        'align':'美浦', 'age':5, 'honmei':True,  'note':'自厩舎◎'},
        'メイショウホウレン': {'g':'—',                  'w':4,  'prod':'グランド牧場',    'align':'栗東', 'age':5, 'honmei':False, 'note':'浜中騎乗'},
        'ヒルノドゴール':     {'g':'キャニオンファーム土山','w':5, 'prod':'サカイF',         'align':'栗東', 'age':5, 'honmei':False, 'note':''},
        'ジョーローリット':   {'g':'大山ヒルズ',          'w':8,  'prod':'斉藤政志',        'align':'栗東', 'age':5, 'honmei':False, 'note':'ブリンカー外'},
        'ケイアイシェルビー': {'g':'吉澤S-WEST',          'w':8,  'prod':'隆栄牧場',        'align':'栗東', 'age':8, 'honmei':False, 'note':'8歳'},
        'カズゴルティス':     {'g':'—',                  'w':0,  'prod':'ノーザンF',       'align':'栗東', 'age':5, 'honmei':False, 'note':'NF×連闘'},
        'ゲッティヴィラ':     {'g':'大山ヒルズ',          'w':8,  'prod':'Zachary Walker', 'align':'栗東', 'age':4, 'honmei':False, 'note':'米生産'},
        'ドンアミティエ':     {'g':'宇治田原優駿S',       'w':9,  'prod':'村田牧場',        'align':'栗東', 'age':6, 'honmei':False, 'note':'60kg海外帰り'},
        'ファムエレガンテ':   {'g':'宇治田原優駿S',       'w':10, 'prod':'W.S.Farish',     'align':'栗東', 'age':4, 'honmei':False, 'note':'米生産'},
    },
}

CH = 'チャンピオンヒルズ'
NF_PRODS = {'ノーザンF'}
SHADAI_PRODS = {'社台F', '追分F', 'グランド牧場', 'グランドF'}  # 追分F=社台系

def is_non_shadai(prod):
    """非社台判定: NF/社台Fなど社台グループでない生産牧場"""
    return prod not in NF_PRODS and prod not in SHADAI_PRODS

def is_local_alignment(align):
    """地方所属判定"""
    return align in {'大井', '川崎', '船橋', '浦和', '門別', '金沢', '名古屋', '高知', '園田', '笠松', '佐賀', '盛岡', '水沢'}

def score_genbu(info):
    """外厩スコア算出 → (score, reasons[])"""
    score = 0
    reasons = []
    g = info['g']
    w = info['w']
    prod = info['prod']
    align = info['align']
    age = info['age']
    honmei = info['honmei']

    # === 加点 ===
    # Nick Doctrine コア: 非社台×CH → +2
    if g == CH and is_non_shadai(prod) and prod not in NF_PRODS:
        score += 2
        reasons.append('🔥非社台×CH(+2)')
    elif g == CH:
        score += 1
        reasons.append('CH預託(+1)')

    # 地方馬×CH → +1追加 (Nick「激アツ」)
    if g == CH and is_local_alignment(align):
        score += 1
        reasons.append('🔥地方×CH(+1)')

    # NF生産×中1週以内連闘 → +1 (NF哲学「1戦必勝」)
    if prod in NF_PRODS and w <= 1:
        score += 1
        reasons.append('NF×連闘(+1)')

    # 社台F生産×CH以外外厩 → +1
    if prod == '社台F' and g not in {'—', CH}:
        score += 1
        reasons.append('社台F外厩(+1)')

    # 自厩舎◎×ピンポイント外厩 → +1
    if honmei and g != '—':
        score += 1
        reasons.append('自厩舎◎×外厩(+1)')

    # === 減点 ===
    # 長欠
    if w >= 52:
        score -= 3
        reasons.append(f'超長欠{w}週(-3)')
    elif w >= 26:
        score -= 2
        reasons.append(f'長欠{w}週(-2)')
    elif w >= 16:
        score -= 1
        reasons.append(f'休養{w}週(-1)')

    # 高齢
    if age >= 8:
        score -= 1
        reasons.append(f'{age}歳(-1)')
    elif age >= 7:
        score -= 1
        reasons.append(f'{age}歳(-1)')

    return score, reasons

def score_to_grade(score):
    """スコア→グレード変換"""
    if score >= 3: return 'S'
    if score == 2: return 'A'
    if score in (0, 1): return 'B'
    if score == -1: return 'C'
    return 'D'

def main():
    print('='*80)
    print('玄武v2 外厩スコア算出 (WIN1-4 / 50頭)')
    print('='*80)

    grand_total = {'S':0,'A':0,'B':0,'C':0,'D':0}

    for file_name, race_key in FILES.items():
        path = os.path.join(RACE_NOTES_DIR, file_name)
        with open(path) as f:
            d = json.load(f)

        table = GAIKYU_DB[race_key]
        print(f"\n=== {race_key.upper()} ({file_name}) ===")
        print(f"{'馬名':20s} | {'外厩':20s}{'週':>5s}  | 生産{'':14s} | 所属 | {'スコア':>6s} | Grade | 理由")
        print('-'*120)

        for h in d['horses']:
            name = h['name']
            if name not in table:
                print(f"  {name:20s} | 未登録")
                continue
            info = table[name]
            score, reasons = score_genbu(info)
            grade = score_to_grade(score)
            grand_total[grade] += 1

            # JSON反映
            h['gaikyu'] = info['g']
            h['gaikyuWeeks'] = info['w']
            h['genbuGrade'] = {
                'grade': grade,
                'score': score,
                'reason': ' / '.join(reasons) if reasons else '標準',
                'gaikyu': info['g'],
                'weeks': info['w'],
                'producer': info['prod'],
                'align': info['align'],
                'v': 'v2-poc',
            }

            g_disp = info['g'][:18] if len(info['g']) > 18 else info['g']
            prod_disp = info['prod'][:16] if len(info['prod']) > 16 else info['prod']
            print(f"  {name:20s} | {g_disp:20s}{info['w']:>3d}週 | {prod_disp:16s} | {info['align']:4s} | {score:>+3d}    | {grade}     | {' / '.join(reasons)}")

        d['logicVersion'] = 'v4-genbu-v2-poc'
        with open(path, 'w') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"✅ {path} 更新完了")

    print('\n' + '='*80)
    print('🐢 玄武v2 WIN1-4 グレード分布')
    print('='*80)
    for g in 'SABCD':
        bar = '█' * grand_total[g]
        print(f"  {g}: {grand_total[g]:2d}頭 {bar}")

    print('\n🔥 Nick Doctrine「非社台×CH」+2ブースト馬:')
    for race_key, table in GAIKYU_DB.items():
        for name, info in table.items():
            if info['g'] == CH and is_non_shadai(info['prod']) and info['prod'] not in NF_PRODS:
                local_mark = '🔥地方' if is_local_alignment(info['align']) else ''
                print(f"  [{race_key:10s}] {name:20s} {info['prod']:12s} {info['w']:>3d}週 {local_mark}")

if __name__ == '__main__':
    main()
