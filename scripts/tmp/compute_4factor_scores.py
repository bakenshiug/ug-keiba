#!/usr/bin/env python3
"""
🎯 4ファクター合算スコア算出スクリプト（雛形 v1）

【4ファクター】
  🔵 青龍（relComment.grade）   ← keibabook前走インタビュー言霊解析
  ⚪ 白虎（lapTotal.grade）     ← ストライド＋究極分析ラップ解析
  🟢 玄武（gaikyuFactor.grade） ← JRDB外厩
  🟡 朱雀（shingan.grade）      ← 弥永チャンネル相馬眼

【配点】
                                 本命   穴
  🔵 青龍 relComment       35    40
  ⚪ 白虎 lapTotal         25    35
  🟢 玄武 gaikyuFactor     20    25
  🟡 朱雀 shingan          20    —  (穴は3ファクター運用)

  shingan fallback（4ファクター→3ファクターへ切替時の本命配点）:
  🔵 青龍 45 / ⚪ 白虎 30 / 🟢 玄武 25

【買い目】単勝1点 + 複勝1点 + ワイド4頭BOX6点 = 計8点 800円/R
  - 単勝軸: 本命1位 × relComment∈{S, A}  （B以下は単勝見送り）
  - 複勝軸: 本命1位（常に）
  - ワイドBOX: 本命上位3頭＋穴スコア1位  or  本命上位4頭（穴が本命上位に被った時）

【穴馬判定】穴スコア上位 × 人気7番人気以下

【実行モード】
  --dry   : 計算・表示のみ、JSON書き戻しなし（デフォルト）
  --write : race-notes JSON の finalBets に書き戻し
  --no-shingan : 朱雀データ未入力時の3ファクター運用（本命も3ファクター配点）

使い方:
  python3 compute_4factor_scores.py               # dry-run 全レース
  python3 compute_4factor_scores.py --write       # 書き戻しあり
  python3 compute_4factor_scores.py --no-shingan  # 朱雀なし
"""
import json
import sys
from pathlib import Path
from datetime import datetime

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")
RACE_NOTES_DIR = BASE / "docs/data/race-notes"

TARGETS = [
    RACE_NOTES_DIR / "2026-04-25-tokyo-11r.json",  # 青葉賞
    RACE_NOTES_DIR / "2026-04-26-tokyo-11r.json",  # フローラS
    RACE_NOTES_DIR / "2026-04-26-kyoto-11r.json",  # マイラーズC
]

# ===================================================================
# 配点定義
# ===================================================================
GRADE_SCORE = {"S": 100, "A": 85, "B": 70, "C": 55, "D": 40}

HOMMEI_W_4 = {"relComment": 0.35, "lapTotal": 0.25, "gaikyuFactor": 0.20, "shingan": 0.20}
HOMMEI_W_3 = {"relComment": 0.45, "lapTotal": 0.30, "gaikyuFactor": 0.25}  # shinganなし
ANA_W      = {"relComment": 0.40, "lapTotal": 0.35, "gaikyuFactor": 0.25}

ANA_POP_THRESHOLD = 7      # 人気7以下が穴候補
TAN_AXIS_GRADES   = {"S", "A"}  # relCommentがSかAなら単勝軸OK
DATA_MISSING_TAG  = "data-missing"  # このタグが付いた馬は買い目対象外

# ===================================================================
# ユーティリティ
# ===================================================================
def get_grade(horse, key):
    """horse[key] がdictなら grade、無ければ None"""
    v = horse.get(key)
    if isinstance(v, dict):
        return v.get("grade")
    return None

def g2s(grade):
    """grade→スコア、未入力はNone"""
    if grade is None:
        return None
    return GRADE_SCORE.get(grade, 0)

def compute_one_horse(h, use_shingan=True):
    """1頭のスコア算出"""
    grades = {
        "relComment":   get_grade(h, "relComment"),
        "lapTotal":     get_grade(h, "lapTotal"),
        "gaikyuFactor": get_grade(h, "gaikyuFactor"),
        "shingan":      get_grade(h, "shingan"),
    }
    scores = {k: g2s(v) for k, v in grades.items()}

    # 本命スコア
    if use_shingan:
        w = HOMMEI_W_4
        hommei_keys = ["relComment", "lapTotal", "gaikyuFactor", "shingan"]
    else:
        w = HOMMEI_W_3
        hommei_keys = ["relComment", "lapTotal", "gaikyuFactor"]

    hommei_missing = [k for k in hommei_keys if scores[k] is None]
    hommei_score = sum((scores[k] or 0) * w[k] for k in hommei_keys)

    # 穴スコア（常に3ファクター）
    ana_keys = ["relComment", "lapTotal", "gaikyuFactor"]
    ana_missing = [k for k in ana_keys if scores[k] is None]
    ana_score = sum((scores[k] or 0) * ANA_W[k] for k in ana_keys)

    return {
        "hommei": round(hommei_score, 1),
        "ana":    round(ana_score, 1),
        "grades": grades,
        "scores": scores,
        "missing": {
            "hommei": hommei_missing,
            "ana":    ana_missing,
        },
    }

def assign_popularity(horses):
    """expectedOddsの昇順で人気を自動付与（既に入ってるなら上書きしない）"""
    if all(h.get("popularity") for h in horses):
        return  # 手動入力済
    sortable = [(h.get("expectedOdds") or 9999, h) for h in horses]
    sortable.sort(key=lambda x: x[0])
    for i, (_, h) in enumerate(sortable, 1):
        h["popularity"] = i

def build_bets(horses, use_shingan=True):
    """買い目構築"""
    eligible = [h for h in horses if h.get("tag") != DATA_MISSING_TAG]

    by_hommei = sorted(eligible, key=lambda h: h["_score"]["hommei"], reverse=True)

    # 単勝軸
    tan_axis = None
    if by_hommei:
        top = by_hommei[0]
        rel = top["_score"]["grades"].get("relComment")
        if rel in TAN_AXIS_GRADES:
            tan_axis = top
            tan_reason = f"本命1位＋青龍{rel}"
        else:
            tan_reason = f"本命1位の青龍={rel or '未'} → 単勝見送り"
    else:
        tan_reason = "出走該当馬なし"

    # 複勝軸：本命1位（常に）
    fuku_axis = by_hommei[0] if by_hommei else None

    # 穴候補
    ana_candidates = [h for h in eligible if (h.get("popularity") or 999) >= ANA_POP_THRESHOLD]
    ana_candidates.sort(key=lambda h: h["_score"]["ana"], reverse=True)
    ana_1st = ana_candidates[0] if ana_candidates else None

    # ワイドBOX 4頭選定
    top3 = by_hommei[:3]
    top3_names = {h["name"] for h in top3}
    if ana_1st and ana_1st["name"] not in top3_names:
        wide_box = top3 + [ana_1st]
        wide_reason = f"本命上位3＋穴1位（{ana_1st['name']} 人気{ana_1st.get('popularity')}）"
    else:
        wide_box = by_hommei[:4]
        wide_reason = "本命上位4頭（穴が本命上位に重複or該当なし）"

    return {
        "tan": {
            "type": "単勝",
            "axis": tan_axis["name"] if tan_axis else None,
            "reason": tan_reason,
            "amount": 100 if tan_axis else 0,
        },
        "fuku": {
            "type": "複勝",
            "axis": fuku_axis["name"] if fuku_axis else None,
            "reason": "本命1位",
            "amount": 100 if fuku_axis else 0,
        },
        "wide": {
            "type": "ワイド4頭BOX",
            "horses": [h["name"] for h in wide_box],
            "points": 6,
            "reason": wide_reason,
            "amount": 600,
        },
        "total": {
            "points": (1 if tan_axis else 0) + (1 if fuku_axis else 0) + 6,
            "amount": (100 if tan_axis else 0) + (100 if fuku_axis else 0) + 600,
        }
    }

# ===================================================================
# メイン処理
# ===================================================================
def process(path, use_shingan=True, write=False):
    data = json.loads(path.read_text(encoding='utf-8'))
    race_name = data.get("race", {}).get("name", path.stem)
    print(f"\n━━━━━━━━━━━━ 🎯 {race_name} ━━━━━━━━━━━━")
    print(f"  モード: {'4ファクター' if use_shingan else '3ファクター(朱雀fallback)'}  /  書き戻し: {'ON' if write else 'OFF(dry-run)'}")

    horses = data.get("horses", [])
    if not horses:
        print("  ⚠ 馬データなし")
        return

    assign_popularity(horses)

    # スコア計算
    missing_total = {"hommei": 0, "ana": 0}
    for h in horses:
        h["_score"] = compute_one_horse(h, use_shingan)
        if h["_score"]["missing"]["hommei"]: missing_total["hommei"] += 1
        if h["_score"]["missing"]["ana"]:    missing_total["ana"] += 1

    # データ欠損レポート
    if missing_total["hommei"]:
        print(f"  ⚠ 本命スコア欠損: {missing_total['hommei']}頭（未入力ファクターあり）")
    if missing_total["ana"]:
        print(f"  ⚠ 穴スコア欠損:   {missing_total['ana']}頭")

    # 本命TOP5
    by_hommei = sorted(horses, key=lambda h: h["_score"]["hommei"], reverse=True)
    print(f"\n  [本命スコア TOP5]")
    print(f"    {'#':>2} {'馬名':<14s} {'本命':>6s} {'穴':>6s} {'人気':>4s} {'OD':>7s}  青龍/白虎/玄武/朱雀")
    for i, h in enumerate(by_hommei[:5], 1):
        sc = h["_score"]
        g = sc["grades"]
        od = h.get('expectedOdds')
        od_str = f"{od:.1f}" if od else "-"
        grade_str = f"{g.get('relComment') or '—'}/{g.get('lapTotal') or '—'}/{g.get('gaikyuFactor') or '—'}/{g.get('shingan') or '—'}"
        print(f"    {i:>2} {h['name']:<14s} {sc['hommei']:>6.1f} {sc['ana']:>6.1f} {h.get('popularity') or '?':>4} {od_str:>7s}  {grade_str}")

    # 穴TOP3
    ana_list = [h for h in horses if (h.get("popularity") or 999) >= ANA_POP_THRESHOLD]
    ana_list.sort(key=lambda h: h["_score"]["ana"], reverse=True)
    if ana_list:
        print(f"\n  [穴候補 TOP3 (人気{ANA_POP_THRESHOLD}以下)]")
        for i, h in enumerate(ana_list[:3], 1):
            sc = h["_score"]
            od = h.get('expectedOdds')
            od_str = f"{od:.1f}" if od else "-"
            print(f"    {i}. {h['name']:<14s} 穴{sc['ana']:>5.1f}  人気{h.get('popularity'):>3}  {od_str:>6s}倍")

    # 買い目
    bets = build_bets(horses, use_shingan)
    print(f"\n  [🎰 買い目 800円]")
    print(f"    単勝       : {bets['tan']['axis'] or '—'} ({bets['tan']['reason']}) → {bets['tan']['amount']}円")
    print(f"    複勝       : {bets['fuku']['axis'] or '—'} → {bets['fuku']['amount']}円")
    print(f"    ワイドBOX   : {', '.join(bets['wide']['horses'])}")
    print(f"                  ({bets['wide']['reason']}) → 6点{bets['wide']['amount']}円")
    print(f"    ─────────────────────────")
    print(f"    合計       : {bets['total']['points']}点 {bets['total']['amount']}円")

    # scoreboard 構築（entries.html finalBets 用）
    scoreboard = []
    for h in by_hommei:
        sc = h["_score"]
        breakdown = {}
        for key in ["relComment", "lapTotal", "gaikyuFactor", "shingan"]:
            gr = sc["grades"].get(key)
            breakdown[key] = {"grade": gr or "—", "score": sc["scores"].get(key)}
        scoreboard.append({
            "name": h["name"],
            "popularity": h.get("popularity"),
            "expectedOdds": h.get("expectedOdds"),
            "hommeiScore": sc["hommei"],
            "anaScore": sc["ana"],
            "breakdown": breakdown,
        })

    # 書き戻し
    if write:
        data["finalBets"] = {
            "logicVersion": "v3-4factor" if use_shingan else "v3-3factor-no-shingan",
            "generatedAt": datetime.now().isoformat(timespec='seconds'),
            "scoreboard": scoreboard,
            "bets": bets,
        }
        # 内部フィールド _score は書き戻さない
        for h in data["horses"]:
            h.pop("_score", None)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n  💾 {path.name} に finalBets を書き戻し完了")
    else:
        print(f"\n  💡 dry-run（--write で書き戻し実行）")

def main():
    use_shingan = "--no-shingan" not in sys.argv
    write       = "--write"      in sys.argv
    for t in TARGETS:
        if not t.exists():
            print(f"⚠ ファイルなし: {t.name}")
            continue
        process(t, use_shingan=use_shingan, write=write)

if __name__ == "__main__":
    main()
