#!/usr/bin/env python3
"""
青葉賞 race-notes JSON に青龍v2「真実×意志」統合gradeを反映
- 既存 relComment.grade（前走=真実）を主軸
- 厩舎談話grade（今回採点）を ±1 補正
- 致命ワードあれば B以下強制
"""
import json

AOBASHO_PATH = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes/2026-04-25-tokyo-11r.json'

# 青葉賞18頭・厩舎の話grade（ギーニョ国語力ロジック判定）
DANWA_GRADES = {
    'サガルマータ':       {'grade':'S','reason':'動き反映／距離適性示した／帰厩毎に良化／身のこなし向上／実戦型','fatal':False},
    'ノーブルサヴェージ': {'grade':'S','reason':'一段階上の仕上がり／距離コース合う／好勝負に','fatal':False},
    'ゴーイントゥスカイ': {'grade':'S','reason':'1週前負荷で良化／動きスムーズ／東京適性高い','fatal':False},
    'ブラックオリンピア': {'grade':'A','reason':'チーク着用で前向きさ／東京2400合う','fatal':False},
    'ラストスマイル':     {'grade':'A','reason':'ここ目標／血統的に距離／トビ大きく東京／良馬場で走らせたい','fatal':False},
    'アッカン':           {'grade':'A','reason':'ハミ換え／左回り対応／距離延長心配なし／態勢整った','fatal':False},
    'ヨカオウ':           {'grade':'A','reason':'前走ゲート不利具体／坂路で自己ベスト／距離延長対応','fatal':False},
    'コスモギガンティア': {'grade':'A','reason':'これまでにない負荷／比べものにならない動き','fatal':True,'fatalTag':'権利狙い'},
    'テルヒコウ':         {'grade':'B','reason':'メニュー消化／走り方向上／現状の力は出せる仕上がり','fatal':False},
    'タイダルロック':     {'grade':'B','reason':'大幅な上積みこそない／使ってみたかった条件／結果が欲しい（中身なし）','fatal':False},
    'ノチェセラーダ':     {'grade':'B','reason':'状態良さそう／舞台設定いい','fatal':True,'fatalTag':'権利狙い'},
    'シャドウマスター':   {'grade':'B','reason':'順調／折り合い問題なし／まだ緩さ／どこまで','fatal':False},
    'ケントン':           {'grade':'B','reason':'短期放牧で対応／疲れダメージなし／時計対応が鍵','fatal':False},
    'パラディオン':       {'grade':'C','reason':'徐々に大人に／どれだけやれますか','fatal':False},
    'トゥーナスタディ':   {'grade':'D','reason':'ダートは得意ではなさそう／頑張ってくれる','fatal':True,'fatalTag':'得意ではなさそう'},
    'カットソロ':         {'grade':'D','reason':'トモに力がない今はともかく／将来性／先々につながる','fatal':True,'fatalTag':'今はともかく・将来性・先々'},
    'ミッキーファルコン': {'grade':'D','reason':'晩生の傾向／将来は走ってくる／自分のリズム優先でどれだけ','fatal':True,'fatalTag':'自分のリズム優先・将来は・晩生'},
    'ヒシアムルーズ':     {'grade':'D','reason':'晩生／コントロール難しい／競馬を教えていきたい','fatal':True,'fatalTag':'教えていきたい・晩生'},
}

GRADE_RANK = {'S':5,'A':4,'B':3,'C':2,'D':1}
RANK_GRADE = {v:k for k,v in GRADE_RANK.items()}

def integrate(prev_grade, danwa_grade, fatal):
    """真実×意志統合ロジック"""
    p = GRADE_RANK.get(prev_grade, 3)
    d = GRADE_RANK.get(danwa_grade, 3)

    # 致命ワード→B以下強制天井
    if fatal:
        capped = min(p, 3)  # B以下
        # さらに厩舎がD級なら-1段階
        if d <= 1:
            capped = max(capped - 1, 1)
        return RANK_GRADE[capped], '致命ワード天井強制'

    diff = d - p
    # 低grade（D=1）は陣営強気でも覆せない
    if p == 1:
        return prev_grade, 'D実力は陣営意志で覆せず'

    # ±1段階補正（それ以上はいじらない）
    if diff >= 1:
        new = min(p + 1, 5)
        return RANK_GRADE[new], '陣営意志+1'
    elif diff <= -1:
        new = max(p - 1, 1)
        return RANK_GRADE[new], '陣営意志-1'
    else:
        return prev_grade, '同格維持'

def main():
    with open(AOBASHO_PATH) as f:
        d = json.load(f)

    print('=== 青葉賞 青龍v2 統合判定 ===')
    print(f"{'馬名':18s} | 前走v1 | 厩舎 | 致命 | 青龍v2 | 理由")
    print('-' * 80)

    for h in d['horses']:
        name = h['name']
        prev = (h.get('relComment') or {}).get('grade', 'B')
        danwa = DANWA_GRADES.get(name)
        if not danwa:
            print(f"  {name:18s} | 厩舎grade無し")
            continue

        final, reason = integrate(prev, danwa['grade'], danwa['fatal'])
        fatal_mark = '🔴' if danwa['fatal'] else '—'
        print(f"  {name:18s} | {prev}    | {danwa['grade']}  | {fatal_mark}  | {final}     | {reason}")

        h['danwaGrade'] = {
            'grade': danwa['grade'],
            'reason': danwa['reason'],
            'fatal': danwa['fatal']
        }
        if danwa['fatal']:
            h['danwaGrade']['fatalTag'] = danwa.get('fatalTag', '')

        h['seiryu'] = {
            'grade': final,
            'v': 2,
            'reason': reason,
            'prev': prev,
            'danwa': danwa['grade']
        }

    d['logicVersion'] = 'v3-seiryu-v2'
    with open(AOBASHO_PATH, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'\n✅ {AOBASHO_PATH} 更新完了')

if __name__ == '__main__':
    main()
