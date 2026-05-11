#!/usr/bin/env python3
"""
🏇 コースデータGrade付与スクリプト（4軸採点）
- 軸1: 父×コース勝率
- 軸2: 騎手×コース勝率
- 軸3: 調教師×コース勝率
- 軸4: 単勝人気帯（予想オッズから推定）

採点基準（各軸）:
- S=20%+ / A=15-19% / B=10-14% / C=5-9% / D=<5% / None=B扱い

合計grade:
- S≥17pt(4軸中3軸以上A相当) / A≥13pt / B≥9pt / C≥5pt / D<5pt
- 各軸: S=5/A=4/B=3/C=2/D=1（最大20pt）
"""
import json
import os

NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'

# ─────────────────────────────────────────────
#  5鞍 コースデータ（競馬ブック /cyuou/data/[raceID] より手動投入）
#  各馬: (父勝率%, 騎手勝率%, 調教師勝率%)
#  None = データなし（-表示）→ B扱い
# ─────────────────────────────────────────────
DATA = {
    '2026-04-25-kyoto-10r.json': {
        'label': 'WIN1 観月橋S',
        'course': '京都ダ1800m',
        'races': 375,
        'horses': {
            'デルアヴァー':       (0.0,  10.1, 12.9),
            'マイノワール':       (7.8,  6.3,  3.3),
            'ペンナヴェローチェ': (14.3, 5.3,  6.7),
            'ピエマンソン':       (7.5,  8.0,  4.9),
            'ショウサンジョージ': (12.5, 9.0,  9.4),
            'ケイアイメキラ':     (11.0, 0.0,  4.5),
            'プルナチャンドラ':   (0.0,  2.9,  0.0),
            'プロミシングスター': (6.4,  4.9,  4.7),
            'タガノマカシヤ':     (5.0,  14.2, 8.7),
            'パシアンジャン':     (15.6, 18.9, 13.1),
            'アラレタバシル':     (0.0,  5.8,  None),
        },
    },
    '2026-04-25-tokyo-10r.json': {
        'label': 'WIN2 鎌倉S',
        'course': '東京ダ1400m',
        'races': 274,
        'horses': {
            'ピックアップライン': (4.8,  2.5,  6.7),
            'クインズデネブ':     (8.7,  0.0,  16.2),
            'ラストシャリナ':     (0.0,  13.7, 0.0),
            'メイショウハチロー': (12.5, 28.6, 14.3),
            'ベンヌ':             (9.7,  10.1, 13.3),
            'トクシーカイザー':   (5.9,  20.0, 16.2),
            'スプランドゥール':   (0.0,  0.0,  0.0),
            'カネショウレジェン': (9.9,  23.8, 6.8),
            'エンセリオ':         (9.1,  7.6,  7.3),
            'シャパリュ':         (5.0,  11.3, 6.3),
            'レーウィン':         (5.8,  0.0,  None),
            'フウセツ':           (11.3, 5.5,  7.1),
            'イノセントキャット': (18.8, 9.6,  13.3),
            'ワンダラー':         (1.7,  22.9, 6.7),
            'ペイシャケイプ':     (9.6,  5.6,  20.0),
        },
    },
    '2026-04-25-fukushima-11r.json': {
        'label': 'WIN3 福島中央TV杯',
        'course': '福島ダ1150m',
        'races': 107,
        'horses': {
            'ジェネラーレ':       (0.0,  8.3,  0.0),
            'イマージョン':       (6.5,  9.8,  33.3),
            'キタノソワレ':       (0.0,  10.6, 5.3),
            'スノーサイレンス':   (15.4, 15.4, 25.0),
            'ビルカール':         (6.9,  0.0,  3.6),
            'ワークソング':       (23.8, 12.5, 15.8),
            'ゴールドハンマー':   (0.0,  0.0,  7.7),
            'プレゼンティーア':   (5.3,  13.3, 25.0),
            'サザンエルフ':       (10.7, 8.6,  14.3),
            'シャカシャカシー':   (8.8,  0.0,  11.1),
            'ルージュアズライト': (7.9,  16.1, 22.2),
            'カウスリップ':       (6.5,  1.4,  14.3),
        },
    },
    '2026-04-25-kyoto-11r.json': {
        'label': 'WIN4 天王山S',
        'course': '京都ダ1200m',
        'races': 187,
        'horses': {
            'ケイアイアニラ':     (9.3,  3.4,  7.1),
            'ジュンウィンダム':   (4.2,  0.0,  8.1),
            'ペプチドヤマト':     (10.4, 4.8,  7.5),
            'オーブルクール':     (11.4, 0.0,  0.0),
            'メイショウホウレン': (6.7,  8.3,  5.5),
            'ヒルノドゴール':     (6.7,  5.8,  14.3),
            'ジョーローリット':   (18.4, 0.0,  11.4),
            'ケイアイシェルビー': (0.0,  6.5,  0.0),
            'カズゴルティス':     (0.0,  7.5,  0.0),
            'ゲッティヴィラ':     (50.0, 11.2, 12.8),
            'ドンアミティエ':     (11.5, 15.9, 20.8),
            'ファムエレガンテ':   (0.0,  11.1, 0.0),
        },
    },
    '2026-04-25-tokyo-11r.json': {
        'label': 'WIN5 青葉賞',
        'course': '東京芝2400m',
        'races': 86,
        'horses': {
            'トゥーナスタディ':   (0.0,  None, None),
            'カットソロ':         (0.0,  2.6,  4.8),
            'パラディオン':       (14.3, 6.3,  33.3),
            'ブラックオリンピア': (18.2, 22.2, 13.0),
            'ミッキーファルコン': (15.8, 12.1, 14.7),
            'テルヒコウ':         (0.0,  5.9,  4.8),
            'タイダルロック':     (4.5,  8.6,  0.0),
            'ラストスマイル':     (None, 0.0,  0.0),
            'ヒシアムルーズ':     (11.1, 23.5, 14.7),
            'アッカン':           (0.0,  0.0,  0.0),
            'ノチェセラーダ':     (20.0, 8.3,  None),
            'サガルマータ':       (0.0,  5.6,  0.0),
            'コスモギガンティア': (0.0,  None, None),
            'ヨカオウ':           (5.6,  0.0,  None),
            'ノーブルサヴェージ': (0.0,  12.5, 0.0),
            'ゴーイントゥスカイ': (0.0,  14.3, 16.7),
            'シャドウマスター':   (18.2, 11.1, 0.0),
            'ケントン':           (11.1, 0.0,  0.0),
        },
    },
}


def rate_to_grade(rate):
    """勝率%→grade (None=B扱い)"""
    if rate is None:
        return 'B'
    if rate >= 20.0: return 'S'
    if rate >= 15.0: return 'A'
    if rate >= 10.0: return 'B'
    if rate >= 5.0:  return 'C'
    return 'D'


def ninki_rank_to_grade(rank):
    """単勝人気順位→grade（予想オッズ順位から推定）
    1番人気≒33-42% → S
    2番人気≒17-20% → A
    3番人気≒11-14% → B
    4-5番人気≒7-9% → C
    6-9番人気≒2-4% → D
    10番人気-≒<1% → D
    """
    if rank == 1: return 'S'
    if rank == 2: return 'A'
    if rank == 3: return 'B'
    if rank <= 5: return 'C'
    return 'D'


GRADE_PT = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}


def total_to_grade(total):
    """合計pt→最終grade"""
    if total >= 17: return 'S'
    if total >= 13: return 'A'
    if total >= 9:  return 'B'
    if total >= 5:  return 'C'
    return 'D'


def assign_ninki_ranks(horses):
    """expectedOdds昇順ソート→人気順位を返す {name: rank}"""
    with_odds = [(h.get('name'), h.get('expectedOdds')) for h in horses if h.get('expectedOdds') is not None]
    with_odds.sort(key=lambda x: x[1])
    rank_map = {}
    for i, (name, _) in enumerate(with_odds, 1):
        rank_map[name] = i
    # オッズなしの馬はラスト扱い
    for h in horses:
        if h.get('name') not in rank_map:
            rank_map[h.get('name')] = len(with_odds) + 1
    return rank_map


def main():
    print('=' * 90)
    print('🏇 コースデータGrade付与（4軸採点：父×コース/騎手×コース/厩舎×コース/人気）')
    print('=' * 90)

    for fname, d in DATA.items():
        path = os.path.join(NOTES_DIR, fname)
        if not os.path.exists(path):
            print(f'\n⚠️  {fname} なし、スキップ')
            continue

        with open(path) as f:
            notes = json.load(f)

        horses = notes.get('horses', [])
        ninki_map = assign_ninki_ranks(horses)

        print(f'\n■ {d["label"]}  ({d["course"]} / {d["races"]}レース)')
        print(f'  {"馬名":<20s} {"父":5s} {"騎":5s} {"厩":5s} {"人":5s} {"Σ":4s} {"総"}')
        print('  ' + '-' * 70)

        hit = 0
        miss = []

        for h in horses:
            name = h.get('name')
            if name not in d['horses']:
                miss.append(name)
                continue

            sire_r, joc_r, tra_r = d['horses'][name]
            g_sire = rate_to_grade(sire_r)
            g_joc  = rate_to_grade(joc_r)
            g_tra  = rate_to_grade(tra_r)

            rank = ninki_map.get(name, 99)
            g_nin = ninki_rank_to_grade(rank)

            pt_sire = GRADE_PT[g_sire]
            pt_joc  = GRADE_PT[g_joc]
            pt_tra  = GRADE_PT[g_tra]
            pt_nin  = GRADE_PT[g_nin]
            total   = pt_sire + pt_joc + pt_tra + pt_nin
            grade   = total_to_grade(total)

            # 理由文字列
            reason = f'父{g_sire}({sire_r}%)/騎{g_joc}({joc_r}%)/厩{g_tra}({tra_r}%)/人{g_nin}({rank}人気)'

            h['courseDataGrade'] = {
                'grade': grade,
                'total': total,
                'sireRate': sire_r,
                'jockeyRate': joc_r,
                'trainerRate': tra_r,
                'ninkiRank': rank,
                'sireGrade': g_sire,
                'jockeyGrade': g_joc,
                'trainerGrade': g_tra,
                'ninkiGrade': g_nin,
                'reason': reason,
                'v': 'v1-4axis',
            }

            mark = '★' if grade == 'S' else ('◎' if grade == 'A' else '  ')
            sr = f'{sire_r:4.1f}' if sire_r is not None else '  - '
            jr = f'{joc_r:4.1f}' if joc_r is not None else '  - '
            trr = f'{tra_r:4.1f}' if tra_r is not None else '  - '
            print(f'  {mark}{name:<18s} {g_sire}{sr} {g_joc}{jr} {g_tra}{trr} {g_nin}[{rank}] {total:2d}pt  {grade}')
            hit += 1

        if miss:
            print(f'  ⚠️ 未マッチ: {miss}')

        # レース単位のlogicVersion更新
        v = notes.get('logicVersion', '')
        if 'coursedata' not in v:
            notes['logicVersion'] = (v + '+coursedata-v1') if v else 'coursedata-v1'

        with open(path, 'w') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        print(f'  ✅ {hit}頭に courseDataGrade 付与 → {fname}')

    print('\n' + '=' * 90)
    print('完了')
    print('=' * 90)


if __name__ == '__main__':
    main()
