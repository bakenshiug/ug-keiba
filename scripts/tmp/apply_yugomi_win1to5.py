#!/usr/bin/env python3
"""
🔮 究極分析ラップ（HC指数×ゴールデン比率）を race-notes JSON に反映
- ソース: 競馬ブックデンマラボ /cyuou/denmalab/[raceID]
- HC赤 = 1着基準との絶対値差が小さいベスト3
- ゴールデン赤 = 出走馬の中で前半/後半/前+後半タイム最速ベスト3

各馬タプル: (hc, hcRed, fRed, bRed, tRed, hvRed)
"""
import json
import os

NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'

# ─────────────────────────────────────────────
#  WIN1-5 究極分析データ（画像から手動投入・2026-04-25）
# ─────────────────────────────────────────────
DATA = {
    '2026-04-25-kyoto-10r.json': {
        'label': 'WIN1 観月橋S',
        'hc1st': 3.2,
        'rank1': 'タガノマカシヤ',
        'horses': {
            # name: (hc, hcRed, fRed, bRed, tRed, hvRed)
            'デルアヴァー':       (10.7, False, False, True,  True,  False),
            'マイノワール':       (9.5,  False, False, False, False, False),
            'ペンナヴェローチェ': (4.4,  True,  True,  False, False, False),
            'ピエマンソン':       (5.3,  False, False, False, False, False),
            'ショウサンジョージ': (4.9,  True,  False, False, False, False),
            'ケイアイメキラ':     (7.7,  False, False, False, False, False),
            'プルナチャンドラ':   (6.4,  False, False, True,  True,  False),
            'プロミシングスター': (5.7,  False, False, False, False, False),
            'タガノマカシヤ':     (2.9,  True,  False, False, True,  False),
            'パシアンジャン':     (6.0,  False, True,  False, True,  False),
            'アラレタバシル':     (7.3,  False, False, False, False, False),
        },
    },
    '2026-04-25-tokyo-10r.json': {
        'label': 'WIN2 鎌倉S',
        'hc1st': 4.6,
        'rank1': 'トクシーカイザー',
        'horses': {
            'ピックアップライン': (3.7,  False, True,  False, False, False),
            'クインズデネブ':     (10.0, False, False, True,  False, False),
            'ラストシャリナ':     (4.9,  True,  False, False, False, False),
            'メイショウハチロー': (7.9,  False, False, True,  True,  False),
            'ベンヌ':             (3.7,  False, False, False, False, False),  # 画像表記は「ペンヌ」だがJRA正式=ベンヌ
            'トクシーカイザー':   (4.7,  True,  False, False, False, False),
            'スプランドゥール':   (10.7, False, False, True,  False, False),
            'カネショウレジェン': (6.7,  False, False, False, False, False),
            'エンセリオ':         (11.9, False, False, False, False, False),
            'シャパリュ':         (5.3,  False, True,  False, True,  False),
            'レーウィン':         (9.0,  False, False, False, False, False),
            'フウセツ':           (2.6,  False, True,  False, True,  False),
            'イノセントキャット': (5.0,  True,  False, False, False, False),
            'ワンダラー':         (5.6,  False, False, False, False, False),
            'ペイシャケイプ':     (12.0, False, False, True,  False, False),
        },
    },
    '2026-04-25-fukushima-11r.json': {
        'label': 'WIN3 福島中央TV杯',
        'hc1st': 3.9,
        'rank1': 'サザンエルフ',
        'horses': {
            'ジェネラーレ':       (1.7,  False, True,  False, False, False),
            'イマージョン':       (2.9,  False, True,  False, False, False),
            'キタノソワレ':       (11.0, False, False, False, False, False),
            'スノーサイレンス':   (2.1,  False, False, False, False, False),
            'ビルカール':         (3.6,  True,  False, False, False, False),
            'ワークソング':       (8.3,  False, False, False, False, False),
            'ゴールドハンマー':   (5.6,  False, True,  False, True,  False),
            'プレゼンティーア':   (2.0,  False, True,  False, False, False),
            'サザンエルフ':       (4.0,  True,  False, True,  True,  False),
            'シャカシャカシー':   (3.3,  True,  False, False, False, False),
            'ルージュアズライト': (5.3,  False, False, False, True,  False),
            'カウスリップ':       (2.0,  False, False, False, False, False),
        },
    },
    '2026-04-25-kyoto-11r.json': {
        'label': 'WIN4 天王山S',
        'hc1st': 6.0,
        'rank1': 'ヒルノドゴール',
        'horses': {
            'ケイアイアニラ':     (3.9,  False, False, False, False, False),
            'ジュンウィンダム':   (8.1,  False, False, False, False, False),
            'ペプチドヤマト':     (7.9,  True,  False, True,  False, False),
            'オーブルクール':     (3.0,  False, False, False, False, False),
            'メイショウホウレン': (3.7,  False, True,  False, True,  False),
            'ヒルノドゴール':     (7.9,  True,  False, True,  True,  False),
            'ジョーローリット':   (3.6,  False, False, False, False, False),
            'ケイアイシェルビー': (11.9, False, False, False, False, False),
            'カズゴルティス':     (3.1,  False, False, True,  True,  False),
            'ゲッティヴィラ':     (7.1,  True,  False, False, True,  True),
            'ドンアミティエ':     (4.3,  True,  True,  False, True,  False),
            'ファムエレガンテ':   (2.1,  False, False, False, False, False),
        },
    },
    '2026-04-25-tokyo-11r.json': {
        'label': 'WIN5 青葉賞',
        'hc1st': 5.4,
        'rank1': 'ゴーイントゥスカイ',
        'horses': {
            'トゥーナスタディ':    (3.8, False, False, False, False, False),
            'カットソロ':          (5.5, True,  False, False, False, False),
            'パラディオン':        (9.0, False, False, False, False, False),
            'ブラックオリンピア':  (2.8, False, False, False, False, False),
            'ミッキーファルコン':  (7.5, False, False, False, False, False),
            'テルヒコウ':          (2.0, False, False, False, False, False),
            'タイダルロック':      (6.5, False, False, False, False, False),
            'ラストスマイル':      (3.0, False, False, False, False, False),
            'ヒシアムルーズ':      (2.7, False, False, False, False, False),
            'アッカン':            (3.7, False, False, False, False, False),
            'ノチェセラーダ':      (4.8, True,  False, False, False, False),
            'サガルマータ':        (3.5, False, False, False, False, False),
            'コスモギガンティア':  (6.0, True,  False, False, False, False),
            'ヨカオウ':            (4.4, False, False, False, False, False),
            'ノーブルサヴェージ':  (2.5, False, False, False, False, False),
            'ゴーイントゥスカイ':  (5.0, True,  False, False, False, False),
            'シャドウマスター':    (4.3, False, False, False, False, False),
            'ケントン':            (2.0, False, False, False, False, False),
        },
    },
}


def grade_from_reds(red_count, is_rank1):
    """赤背景数＋rank1フラグからgrade判定"""
    if is_rank1:
        return 'S'
    if red_count >= 3: return 'A'
    if red_count == 2: return 'B'
    if red_count == 1: return 'C'
    return 'D'


def build_reason(hc, hc_diff, hcR, fR, bR, tR, hvR, is_rank1):
    parts = []
    if hcR: parts.append(f'HC赤({hc}/差{hc_diff:.1f})')
    if fR:  parts.append('前半赤')
    if bR:  parts.append('後半赤')
    if tR:  parts.append('前+後半赤')
    if hvR: parts.append('重後半赤')
    if is_rank1: parts.append('★究極1位')
    return '/'.join(parts) if parts else '赤なし'


def main():
    print('=' * 80)
    print('🔮 究極分析ラップ v1 反映（HC指数×ゴールデン比率）')
    print('=' * 80)

    for fname, d in DATA.items():
        path = os.path.join(NOTES_DIR, fname)
        if not os.path.exists(path):
            print(f'\n⚠️  {fname} なし、スキップ')
            continue

        with open(path) as f:
            notes = json.load(f)

        print(f'\n■ {d["label"]}  (1着基準HC={d["hc1st"]}・rank1={d["rank1"]})')
        hit = 0
        miss = []

        for h in notes['horses']:
            name = h.get('name')
            if name not in d['horses']:
                miss.append(name)
                continue

            hc, hcR, fR, bR, tR, hvR = d['horses'][name]
            red_count = int(hcR) + int(fR) + int(bR) + int(tR) + int(hvR)
            is_rank1 = (name == d['rank1'])
            grade = grade_from_reds(red_count, is_rank1)
            hc_diff = abs(hc - d['hc1st'])
            reason = build_reason(hc, hc_diff, hcR, fR, bR, tR, hvR, is_rank1)

            h['yugomiLapGrade'] = {
                'grade': grade,
                'redCount': red_count,
                'hcRed': hcR,
                'fRed': fR,
                'bRed': bR,
                'tRed': tR,
                'hvRed': hvR,
                'hc': hc,
                'hcDiff': round(hc_diff, 2),
                'rank1': is_rank1,
                'reason': reason,
                'v': 'v1-hc-golden',
            }

            mark = '★' if is_rank1 else '  '
            print(f'  {mark} {name:<18s} grade={grade} red={red_count} HC={hc:4.1f}(差{hc_diff:.1f}) {reason}')
            hit += 1

        if miss:
            print(f'  ⚠️ 未マッチ（画像にない馬）: {miss}')

        notes['logicVersion'] = 'v4-yugomi-v1'
        with open(path, 'w') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        print(f'  ✅ {hit}頭に yugomiLapGrade 付与 → {fname}')

    print('\n' + '=' * 80)
    print('完了')
    print('=' * 80)


if __name__ == '__main__':
    main()
