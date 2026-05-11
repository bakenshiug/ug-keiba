#!/usr/bin/env python3
"""
白虎grade判定スクリプト (2026-04-25 土曜5鞍)
スピード指数の [5走前, 4走前, 3走前, 2走前, 前走] からgrade(S/A/B/C/D)を判定

判定ロジック:
  peak = max(直近3走のSP)  ← ピーク値
  prev = 前走SP
  avg3 = 直近3走平均

  grade:
    S = peak >= 90 (超一流の走り経験あり)
    A = peak >= 87 or (prev >= 85 and avg3 >= 82)
    B = peak >= 83 or (prev >= 80)
    C = peak >= 78 or (prev >= 75)
    D = それ未満

  補正:
    前走が極端に低い（<70）& 理由コメントなし → -1段階
    前走が自己ベスト更新 → +1段階（勢い）
"""
import json

def judge_grade(sp_arr, notes=None):
    # 有効SP値のみ取り出し
    valid_sp = [s for s in sp_arr if s is not None and s > 30]  # 30以下は異常値(障害/芝大敗等)除外
    if len(valid_sp) == 0:
        return ('D', 'SPデータ不足')

    prev = sp_arr[-1] if sp_arr[-1] is not None else None
    recent3 = [s for s in sp_arr[-3:] if s is not None and s > 30]
    peak = max(valid_sp) if valid_sp else 0
    peak3 = max(recent3) if recent3 else 0
    avg3 = sum(recent3)/len(recent3) if recent3 else 0

    reason = []

    # ベースgrade判定
    if peak >= 90:
        grade = 'S'
        reason.append(f'peak{peak}')
    elif peak >= 87 or (prev and prev >= 85 and avg3 >= 82):
        grade = 'A'
        reason.append(f'peak{peak}' if peak >= 87 else f'前{prev}avg{avg3:.1f}')
    elif peak >= 83 or (prev and prev >= 80):
        grade = 'B'
        reason.append(f'peak{peak}' if peak >= 83 else f'前{prev}')
    elif peak >= 78 or (prev and prev >= 75):
        grade = 'C'
        reason.append(f'peak{peak:.1f}')
    else:
        grade = 'D'
        reason.append(f'peak{peak:.1f}')

    # 補正: 前走と直近3走ピークの乖離
    if prev is not None and peak3 is not None and prev < peak3 - 10:
        # 前走が大幅に落ちた -1段階
        order = ['S','A','B','C','D']
        idx = order.index(grade)
        if idx < len(order) - 1:
            grade = order[idx+1]
            reason.append(f'前走落ち-1')

    # 補正: 前走がピーク（自己ベスト更新 or タイ）で85+
    if prev is not None and prev == peak and prev >= 83:
        order = ['S','A','B','C','D']
        idx = order.index(grade)
        if idx > 0:
            grade = order[idx-1]
            reason.append(f'前走ピーク+1')

    return (grade, '/'.join(reason))


def main():
    with open('/Users/buntawakase/Desktop/ug-keiba/scripts/tmp/byakko_raw_0425.json') as f:
        data = json.load(f)

    out = {'races': {}}

    for race_key, race in data['races'].items():
        print(f"\n=== {race['name']} ({race['race']} {race['course']}) ===")
        out_race = {'name': race['name'], 'horses': []}
        for h in race['horses']:
            grade, reason = judge_grade(h['sp'], h.get('notes'))
            sp_str = '/'.join([f"{s:.1f}" if s is not None else '-' for s in h['sp']])
            print(f"  {h['waku']}-{h['uma']:2d} {h['name']:15s} SP[{sp_str}] → {grade} ({reason})")
            out_race['horses'].append({
                'uma': h['uma'],
                'name': h['name'],
                'byakkoGrade': grade,
                'byakkoReason': reason,
                'sp': h['sp']
            })
        out['races'][race_key] = out_race

    with open('/Users/buntawakase/Desktop/ug-keiba/scripts/tmp/byakko_grades_0425.json', 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n✅ /Users/buntawakase/Desktop/ug-keiba/scripts/tmp/byakko_grades_0425.json に保存")

if __name__ == '__main__':
    main()
