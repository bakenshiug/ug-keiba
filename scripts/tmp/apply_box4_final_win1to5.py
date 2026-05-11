#!/usr/bin/env python3
"""
2026-04-25 WIN5 最終4頭ワイドBOX + 単勝/複勝 反映スクリプト
─────────────────────────────────────────
A案（4神統合 + 外部総合指標クロスチェック済み）で5鞍の
`finalBets.wide4box` / `finalBets.tan` / `finalBets.fuku` を一括書き換え。

買い目構成（各レース）:
  - 単勝: 100円 × 1頭（4神整合本命）
  - 複勝: 100円 × 1頭（穴 or 堅軸）
  - ワイドBOX4頭: 100円 × 6点 = 600円
  - 合計: 800円/レース × 5鞍 = 4,000円

※ 出典秘匿ルール遵守：外部指標の名称はコード・コミットに出さない
"""
import json
import os
from datetime import datetime
from itertools import combinations

BASE = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'

# 各レースの買い目設計（A案）
BETS = [
    {
        'file': '2026-04-25-kyoto-10r.json',
        'label': 'WIN1 観月橋S',
        'box4': ['パシアンジャン', 'マイノワール', 'タガノマカシヤ', 'デルアヴァー'],
        'tan_horse': 'パシアンジャン',    # 玄武1位・レース適性合致・妙味高
        'fuku_horse': 'マイノワール',      # 5人気・総合評価1位・仕上最上位
        'tan_reason': '玄武1位×レース適性合致×妙味S',
        'fuku_reason': '総合評価1位(5人気)・仕上69最強',
        'ana_idx': 1,  # マイノワールが穴
    },
    {
        'file': '2026-04-25-tokyo-10r.json',
        'label': 'WIN2 鎌倉S',
        'box4': ['メイショウハチロー', 'ワンダラー', 'ペイシャケイプ', 'トクシーカイザー'],
        'tan_horse': 'メイショウハチロー',  # 青龍+玄武+外部1位・キャラピッタリ
        'fuku_horse': 'ワンダラー',          # 4人気・外部2位・妙味S
        'tan_reason': '4神+外部評価完全整合・キャラピッタリ',
        'fuku_reason': '外部評価2位(4人気)・妙味S・仕上66',
        'ana_idx': 1,
    },
    {
        'file': '2026-04-25-fukushima-11r.json',
        'label': 'WIN3 福島TV杯',
        'box4': ['キタノソワレ', 'ビルカール', 'ルージュアズライト', 'スノーサイレンス'],
        'tan_horse': 'キタノソワレ',         # 外部1位・仕上66・妙味A
        'fuku_horse': 'ビルカール',           # 7人気・外部2位・SAV69
        'tan_reason': '外部評価1位・仕上66・妙味A',
        'fuku_reason': '外部評価2位(7人気)・SAV69',
        'ana_idx': 1,
    },
    {
        'file': '2026-04-25-kyoto-11r.json',
        'label': 'WIN4 天王山S',
        'box4': ['ジョーローリット', 'ヒルノドゴール', 'ドンアミティエ', 'ゲッティヴィラ'],
        'tan_horse': 'ヒルノドゴール',        # 白虎1位・仕上82最強・外部2位
        'fuku_horse': 'ジョーローリット',      # 6人気・外部1位・仕上81・大穴
        'tan_reason': '白虎1位×仕上82最強×外部評価2位',
        'fuku_reason': '外部評価1位(6人気)・仕上81・大穴',
        'ana_idx': 0,  # ジョーローリットが穴
    },
    {
        'file': '2026-04-25-tokyo-11r.json',
        'label': 'WIN5 青葉賞',
        'box4': ['ブラックオリンピア', 'ラストスマイル', 'ゴーイントゥスカイ', 'タイダルロック'],
        'tan_horse': 'ブラックオリンピア',    # 青龍S+玄武1位+SAV90・1人気鉄板
        'fuku_horse': 'ラストスマイル',        # 10人気・外部1位・妙味S・朱雀1位
        'tan_reason': '青龍S×玄武1位×SAV90の3冠整合',
        'fuku_reason': '外部評価1位(10人気)・妙味S・朱雀1位',
        'ana_idx': 1,  # ラストスマイルが穴
    },
]


def build_combos(names):
    """4頭から6通りのワイド組合せを生成"""
    return [
        {'pair': [None, None], 'names': list(pair)}
        for pair in combinations(names, 2)
    ]


def build_box4(box_names, horses_by_name, ana_idx):
    """wide4box.horses を組み立てる"""
    horses_arr = []
    for i, name in enumerate(box_names):
        h = horses_by_name.get(name, {})
        horses_arr.append({
            'rank': i + 1,
            'num': h.get('num'),
            'name': name,
            'score': None,  # 外部統合の後は単一スコアで表現できないためNone
            'isAna': (i == ana_idx),
            'tag': 'ana' if i == ana_idx else 'ninki',
        })
    return horses_arr


def update_race(bet):
    path = os.path.join(BASE, bet['file'])
    with open(path, 'r') as f:
        d = json.load(f)

    horses_by_name = {h['name']: h for h in d.get('horses', [])}

    # 該当馬が全員存在するかチェック
    for name in bet['box4']:
        if name not in horses_by_name:
            print(f"  ✗ {name}: race-notesに存在しない！")
            return False

    tan_h = horses_by_name.get(bet['tan_horse'], {})
    fuku_h = horses_by_name.get(bet['fuku_horse'], {})

    # finalBets全体を新構造で上書き（scoreboardは既存維持）
    fb = d.setdefault('finalBets', {})
    fb['generatedAt'] = datetime.now().isoformat(timespec='seconds')
    fb['logicVersion'] = 'v3-shijin-external-cross-2026-04-25'

    # 単勝
    fb['tan'] = {
        'rank': 1,
        'num': tan_h.get('num'),
        'name': bet['tan_horse'],
        'amount': 100,
        'reason': bet['tan_reason'],
    }

    # 複勝（穴 or 堅軸1頭）
    fb['fuku'] = {
        'rank': 1,
        'num': fuku_h.get('num'),
        'name': bet['fuku_horse'],
        'amount': 100,
        'reason': bet['fuku_reason'],
    }

    # ワイド4頭BOX（6点）
    box_horses = build_box4(bet['box4'], horses_by_name, bet['ana_idx'])
    combos = build_combos(bet['box4'])
    fb['wide4box'] = {
        'horses': box_horses,
        'combos': combos,
        'comboCount': 6,
        'amount': 600,
        'composition': '4shijin-external',
        'fallback': False,
        'meta': {
            'composition': '4shijin-external-cross',
            'ninkiCount': 3,
            'anaCount': 1,
            'note': '4神(青龍/朱雀/白虎/玄武)整合+外部総合指標クロスチェック済み',
        }
    }

    fb['totalSpend'] = 800
    fb['readiness'] = f"{len(bet['box4'])}/{len(bet['box4'])}"
    fb['readinessPct'] = 100.0

    # presentation（表示用テキスト）
    ana_name = bet['box4'][bet['ana_idx']]
    fb['presentation'] = {
        'headline': f"{bet['label']} 4頭ワイドBOX確定",
        'tanLine': f"単勝 100円: {bet['tan_horse']}（{bet['tan_reason']}）",
        'fukuLine': f"複勝 100円: {bet['fuku_horse']}（{bet['fuku_reason']}）",
        'wideLine': f"ワイドBOX 100円×6点: {' / '.join(bet['box4'])}",
    }

    with open(path, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    return True


def main():
    print('━' * 70)
    print('🏇 2026-04-25 WIN5 最終4頭ワイドBOX 一括反映')
    print('━' * 70)

    success = 0
    for bet in BETS:
        print(f"\n▶ {bet['label']} ({bet['file']})")
        print(f"   BOX4: {' / '.join(bet['box4'])}")
        print(f"   単勝: {bet['tan_horse']}")
        print(f"   複勝: {bet['fuku_horse']} [穴]")
        if update_race(bet):
            print(f'   ✅ 書き込み成功')
            success += 1
        else:
            print(f'   ❌ 書き込み失敗')

    print(f'\n{"━" * 70}')
    print(f'📊 完了: {success}/{len(BETS)} 鞍')
    print(f'💰 合計投資: {success * 800}円（100×2単複 + 100×6ワイド × {success}鞍）')


if __name__ == '__main__':
    main()
