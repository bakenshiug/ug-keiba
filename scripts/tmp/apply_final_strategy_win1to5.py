#!/usr/bin/env python3
"""
2026-04-25 WIN5 最終戦略（変動型）反映スクリプト
─────────────────────────────────────────
【戦略決定ロジック】外部総合指標の指数分布で3分岐:
  - 指数抜け1頭 → 1点突破確定（単勝）
  - 指数抜け2頭 → 2頭購入（単勝×2）
  - 混戦（接戦） → 4頭購入（ワイドBOX+単複）

ニック確定プラン（弥永ch動画未公開のため朱雀v2待たず確定）:
  - WIN1 観月橋S    : 指数抜け2頭 → 2頭購入   パシアンジャン/デルアヴァー
  - WIN2 鎌倉S      : 混戦     → 4頭BOX    (トクシーカイザー→クインズデネブ入替)
  - WIN3 福島TV杯   : 混戦     → 4頭BOX    (Plan A維持)
  - WIN4 天王山S    : 指数抜け1頭 → 1点突破    ゲッティヴィラ
  - WIN5 青葉賞     : 指数抜け1頭 → 1点突破    ブラックオリンピア

合計投資: 200 + 800 + 800 + 100 + 100 = 2,000円 / 5鞍

※ 出典秘匿ルール遵守：外部指標の名称はコード・コミットに出さない
"""
import json
import os
from datetime import datetime
from itertools import combinations

BASE = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'

# ─────────────────────────────────────────
# 各レースの最終買い目（変動型）
# ─────────────────────────────────────────
BETS = [
    # WIN1: 2頭購入（単勝×2）
    {
        'file': '2026-04-25-kyoto-10r.json',
        'label': 'WIN1 観月橋S',
        'strategy': '2horse-tan',
        'horses': ['パシアンジャン', 'デルアヴァー'],
        'reasons': {
            'パシアンジャン': '玄武1位×レース適性合致×妙味S',
            'デルアヴァー': '道悪注文＋陣営◎印・使った上積み',
        },
        'note': '外部総合指標で指数抜け2頭判定 → 2頭単勝勝負。弥永ch未公開のため朱雀v2統合せず確定。',
    },
    # WIN2: 4頭ワイドBOX（swap!）
    {
        'file': '2026-04-25-tokyo-10r.json',
        'label': 'WIN2 鎌倉S',
        'strategy': '4horse-box',
        'box4': ['メイショウハチロー', 'ワンダラー', 'ペイシャケイプ', 'クインズデネブ'],
        'tan_horse': 'メイショウハチロー',
        'fuku_horse': 'ワンダラー',
        'tan_reason': '4神+外部評価完全整合・キャラピッタリ',
        'fuku_reason': '外部評価2位(4人気)・妙味S・仕上66',
        'ana_idx': 1,
    },
    # WIN3: 4頭ワイドBOX（Plan A維持）
    {
        'file': '2026-04-25-fukushima-11r.json',
        'label': 'WIN3 福島TV杯',
        'strategy': '4horse-box',
        'box4': ['キタノソワレ', 'ビルカール', 'ルージュアズライト', 'スノーサイレンス'],
        'tan_horse': 'キタノソワレ',
        'fuku_horse': 'ビルカール',
        'tan_reason': '外部評価1位・仕上66・妙味A',
        'fuku_reason': '外部評価2位(7人気)・SAV69',
        'ana_idx': 1,
    },
    # WIN4: 1点突破確定（単勝）
    {
        'file': '2026-04-25-kyoto-11r.json',
        'label': 'WIN4 天王山S',
        'strategy': '1horse-tan',
        'horses': ['ゲッティヴィラ'],
        'reasons': {
            'ゲッティヴィラ': '1点突破確定・高妙味高確度',
        },
        'note': '外部総合指標で指数抜け1頭判定 → 1点突破確定。ゲッティヴィラ単勝勝負。',
    },
    # WIN5: 1点突破確定（単勝）
    {
        'file': '2026-04-25-tokyo-11r.json',
        'label': 'WIN5 青葉賞',
        'strategy': '1horse-tan',
        'horses': ['ブラックオリンピア'],
        'reasons': {
            'ブラックオリンピア': '青龍S×玄武1位×朱雀peak90の3冠整合・1番人気鉄板',
        },
        'note': '外部総合指標で指数抜け1頭判定 → 1点突破確定。1番人気の本命鉄板勝負。',
    },
]


def build_combos(names):
    """N頭から6通りのワイド組合せを生成"""
    return [
        {'pair': [None, None], 'names': list(pair)}
        for pair in combinations(names, 2)
    ]


def apply_2horse_tan(d, bet, horses_by_name):
    """WIN1型: 2頭単勝 × 100円 ずつ"""
    h1 = horses_by_name.get(bet['horses'][0], {})
    h2 = horses_by_name.get(bet['horses'][1], {})

    fb = d.setdefault('finalBets', {})
    fb['generatedAt'] = datetime.now().isoformat(timespec='seconds')
    fb['logicVersion'] = 'v4-final-variable-strategy-2026-04-25'
    fb['strategy'] = '2horse-tan'

    # 単勝1（主軸）
    fb['tan'] = {
        'rank': 1,
        'num': h1.get('num'),
        'name': bet['horses'][0],
        'amount': 100,
        'reason': bet['reasons'][bet['horses'][0]],
    }

    # 単勝2（対抗）を fuku 枠に格納（複勝ではなく単勝2頭目）
    fb['tan2'] = {
        'rank': 2,
        'num': h2.get('num'),
        'name': bet['horses'][1],
        'amount': 100,
        'reason': bet['reasons'][bet['horses'][1]],
        'type': 'tan',  # 複勝ではなく単勝
    }

    # wide4box は明示的に削除（2頭戦略では使用しない）
    fb.pop('wide4box', None)
    fb.pop('fuku', None)

    fb['totalSpend'] = 200
    fb['readiness'] = '2/2'
    fb['readinessPct'] = 100.0

    fb['presentation'] = {
        'headline': f"{bet['label']} 2頭単勝勝負",
        'tanLine': f"単勝 100円: {bet['horses'][0]}（{bet['reasons'][bet['horses'][0]]}）",
        'tan2Line': f"単勝 100円: {bet['horses'][1]}（{bet['reasons'][bet['horses'][1]]}）",
        'note': bet['note'],
    }


def apply_1horse_tan(d, bet, horses_by_name):
    """WIN4/WIN5型: 単勝1点 × 100円"""
    h = horses_by_name.get(bet['horses'][0], {})

    fb = d.setdefault('finalBets', {})
    fb['generatedAt'] = datetime.now().isoformat(timespec='seconds')
    fb['logicVersion'] = 'v4-final-variable-strategy-2026-04-25'
    fb['strategy'] = '1horse-tan'

    fb['tan'] = {
        'rank': 1,
        'num': h.get('num'),
        'name': bet['horses'][0],
        'amount': 100,
        'reason': bet['reasons'][bet['horses'][0]],
    }

    # 不要な枠は削除
    fb.pop('tan2', None)
    fb.pop('fuku', None)
    fb.pop('wide4box', None)

    fb['totalSpend'] = 100
    fb['readiness'] = '1/1'
    fb['readinessPct'] = 100.0

    fb['presentation'] = {
        'headline': f"{bet['label']} 1点突破確定",
        'tanLine': f"単勝 100円: {bet['horses'][0]}（{bet['reasons'][bet['horses'][0]]}）",
        'note': bet['note'],
    }


def apply_4horse_box(d, bet, horses_by_name):
    """WIN2/WIN3型: 4頭ワイドBOX + 単勝 + 複勝 = 800円"""
    # 該当馬チェック
    for name in bet['box4']:
        if name not in horses_by_name:
            print(f"  ✗ {name}: race-notesに存在しない！")
            return False

    tan_h = horses_by_name.get(bet['tan_horse'], {})
    fuku_h = horses_by_name.get(bet['fuku_horse'], {})

    fb = d.setdefault('finalBets', {})
    fb['generatedAt'] = datetime.now().isoformat(timespec='seconds')
    fb['logicVersion'] = 'v4-final-variable-strategy-2026-04-25'
    fb['strategy'] = '4horse-box'

    # 単勝
    fb['tan'] = {
        'rank': 1,
        'num': tan_h.get('num'),
        'name': bet['tan_horse'],
        'amount': 100,
        'reason': bet['tan_reason'],
    }

    # 複勝
    fb['fuku'] = {
        'rank': 1,
        'num': fuku_h.get('num'),
        'name': bet['fuku_horse'],
        'amount': 100,
        'reason': bet['fuku_reason'],
    }
    fb.pop('tan2', None)

    # ワイド4頭BOX（6点）
    box_horses = []
    for i, name in enumerate(bet['box4']):
        h = horses_by_name.get(name, {})
        box_horses.append({
            'rank': i + 1,
            'num': h.get('num'),
            'name': name,
            'score': None,
            'isAna': (i == bet['ana_idx']),
            'tag': 'ana' if i == bet['ana_idx'] else 'ninki',
        })

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
    fb['readiness'] = '4/4'
    fb['readinessPct'] = 100.0

    ana_name = bet['box4'][bet['ana_idx']]
    fb['presentation'] = {
        'headline': f"{bet['label']} 4頭ワイドBOX確定",
        'tanLine': f"単勝 100円: {bet['tan_horse']}（{bet['tan_reason']}）",
        'fukuLine': f"複勝 100円: {bet['fuku_horse']}（{bet['fuku_reason']}）",
        'wideLine': f"ワイドBOX 100円×6点: {' / '.join(bet['box4'])}",
    }
    return True


def update_race(bet):
    path = os.path.join(BASE, bet['file'])
    with open(path, 'r') as f:
        d = json.load(f)

    horses_by_name = {h['name']: h for h in d.get('horses', [])}

    # 該当馬存在チェック
    target_names = bet.get('box4') or bet.get('horses') or []
    for name in target_names:
        if name not in horses_by_name:
            print(f"  ✗ {name}: race-notesに存在しない！")
            return False

    strategy = bet['strategy']
    if strategy == '2horse-tan':
        apply_2horse_tan(d, bet, horses_by_name)
    elif strategy == '1horse-tan':
        apply_1horse_tan(d, bet, horses_by_name)
    elif strategy == '4horse-box':
        if not apply_4horse_box(d, bet, horses_by_name):
            return False
    else:
        print(f"  ✗ 未知の戦略: {strategy}")
        return False

    with open(path, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    return True


def main():
    print('━' * 72)
    print('🏇 2026-04-25 WIN5 最終変動戦略 一括反映')
    print('━' * 72)

    total_spend = 0
    success = 0
    for bet in BETS:
        print(f"\n▶ {bet['label']} ({bet['file']})")
        print(f"   戦略: {bet['strategy']}")

        if bet['strategy'] == '2horse-tan':
            print(f"   買い目: 単勝×2 ({' / '.join(bet['horses'])}) = 200円")
            spend = 200
        elif bet['strategy'] == '1horse-tan':
            print(f"   買い目: 単勝1点 ({bet['horses'][0]}) = 100円")
            spend = 100
        elif bet['strategy'] == '4horse-box':
            print(f"   BOX4: {' / '.join(bet['box4'])}")
            print(f"   単勝: {bet['tan_horse']} / 複勝: {bet['fuku_horse']}")
            spend = 800

        if update_race(bet):
            print(f'   ✅ 書き込み成功 ({spend}円)')
            success += 1
            total_spend += spend
        else:
            print(f'   ❌ 書き込み失敗')

    print(f'\n{"━" * 72}')
    print(f'📊 完了: {success}/{len(BETS)} 鞍')
    print(f'💰 合計投資: {total_spend}円')
    print(f'   WIN1:200 + WIN2:800 + WIN3:800 + WIN4:100 + WIN5:100')


if __name__ == '__main__':
    main()
