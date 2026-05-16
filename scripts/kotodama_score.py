#!/usr/bin/env python3
"""
言霊スコアリング v1.0
danwaComment + syoinComment を解析し kotodamaGrade / kotodamaScore / kotodamaRank を付与。
既存フィールド（danwaComment, syoinComment 等）は保持したまま追記。
"""

import json
import re
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# キーワード辞書
# ──────────────────────────────────────────────

# 🔴 真致命（grade を B に強制天井）
FATAL_B_CEILING = [
    "胸を借りる", "アテにはならない", "決してベストの距離ではない",
    "自分のリズム優先", "自分の競馬を",
]

# 🟡 準致命（-1.0）
QUASI_FATAL = [
    "将来は", "いずれは", "権利を", "賞金を稼ぐ",
    "教えていきたい", "経験を積む", "晩生", "成長待ち",
    "得意ではなさそう",
]

# 🟢 強気ワード（+1.0）
POSITIVE_HIGH = [
    "楽しみ", "期待", "鉄板", "完璧", "圧勝", "素晴らしい",
    "メドが立", "順番が回って", "すぐに勝て",
    "去勢効果", "ブリンカー効果", "ブリンカーを外した",
    "ノド手術", "左回り合う", "コース得意", "ここを目標",
    "勝ったコース", "ここ勝っている",
]

# 🔵 中程度プラス（+0.5）
POSITIVE_MID = [
    "上積みがあれ", "上積みを", "上積みは",
    "チャンスが近", "チャンスはある", "チャンスを",
    "一変してもおかしく", "変わり身が",
    "次につながる", "次はもっと",
    "スムーズなら", "条件はいい", "条件がいい",
    "能力は十分", "能力は足りる", "能力は通用",
    "叩いて", "使った上積み",
]

# ⬇ 消極ワード（-0.5）
NEGATIVE_MID = [
    "どこまで", "厳しいかも", "どうかですが", "どうかだが",
    "現状は厳しい", "ひと息", "使いつつ", "まずはどこまで",
    "大きく変わった感じはしません",
]

# 陣営印プラス
DANWA_MARKS = {
    "◎": 2.0,
    "○": 1.0,
    "▲": 0.5,
    "△": -0.5,
}

# 前走着順ボーナス（syoinに出現する「（X着）」パターン）
RESULT_BONUS = {
    "１着": 2.5,
    "２着": 1.5,
    "３着": 0.8,
    "４着": 0.2,
    "５着": 0.0,
    "６着": -0.3,
    "７着": -0.5,
    "８着": -0.7,
    "９着": -0.8,
    "１０着": -1.0,
    "１１着": -1.0,
    "１２着": -1.0,
    "１３着": -1.0,
    "１４着": -1.0,
    "１５着": -1.0,
    "１６着": -1.0,
    "１７着": -1.0,
    "１８着": -1.0,
}


def extract_result_from_syoin(syoin: str) -> tuple[str | None, float]:
    """syoinコメントから前走着順を抽出してボーナスを返す"""
    if not syoin:
        return None, 0.0
    m = re.search(r"（([１２３４５６７８９１０１１１２１３１４１５１６１７１８]+着)）", syoin)
    if m:
        rank_str = m.group(1)
        bonus = RESULT_BONUS.get(rank_str, 0.0)
        return rank_str, bonus
    return None, 0.0


def score_horse(danwa: str, syoin: str) -> dict:
    """
    1頭のスコアリング。
    戻り値: {score: float, grade: str, rank_result: str|None, fatal_b: bool, notes: list}
    """
    danwa = danwa or ""
    syoin = syoin or ""
    combined = danwa + " " + syoin
    score = 5.0  # ベースライン（全馬同条件）
    notes = []
    fatal_b = False

    # ── 1. 陣営印 ──
    for mark, bonus in DANWA_MARKS.items():
        if danwa.startswith(mark):
            score += bonus
            notes.append(f"{mark}印({bonus:+.1f})")
            break

    # ── 2. 真致命チェック ──
    for w in FATAL_B_CEILING:
        if w in combined:
            fatal_b = True
            notes.append(f"🔴B天井[{w}]")

    # ── 3. 準致命 ──
    for w in QUASI_FATAL:
        if w in combined:
            score -= 1.0
            notes.append(f"🟡準致命[{w}](-1.0)")

    # ── 4. 強気ワード HIGH ──
    for w in POSITIVE_HIGH:
        if w in combined:
            score += 1.0
            notes.append(f"🟢+1.0[{w}]")

    # ── 5. 強気ワード MID ──
    for w in POSITIVE_MID:
        if w in combined:
            score += 0.5
            notes.append(f"🔵+0.5[{w}]")

    # ── 6. 消極ワード ──
    for w in NEGATIVE_MID:
        if w in combined:
            score -= 0.5
            notes.append(f"⬇-0.5[{w}]")

    # ── 7. 前走結果（syoin） ──
    rank_result, bonus = extract_result_from_syoin(syoin)
    if rank_result:
        score += bonus
        notes.append(f"前走{rank_result}({bonus:+.2f})")

    # syoin騎手コメント強気
    if syoin:
        syoin_positive = ["チャンスがあ", "次はもっと良く", "強い競馬", "力をつけて", "すぐにチャンス"]
        for w in syoin_positive:
            if w in syoin:
                score += 0.3
                notes.append(f"🔵syoin+0.3[{w}]")

    # ── 8. B天井適用 ──
    if fatal_b:
        score = min(score, 7.5)  # B上限

    # ── 9. grade変換 ──
    if score >= 9.5:
        grade = "S"
    elif score >= 8.0:
        grade = "A"
    elif score >= 6.5:
        grade = "B"
    elif score >= 5.0:
        grade = "C"
    else:
        grade = "D"

    # B天井 → grade最大B
    if fatal_b and grade in ("S", "A"):
        grade = "B"

    return {
        "score": round(score, 2),
        "grade": grade,
        "rankResult": rank_result,
        "fatalB": fatal_b,
        "notes": notes,
    }


GRADE_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}


def process_roster(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        roster = json.load(f)

    # cols に新フィールドを追記（重複しないよう）
    new_cols = ["kotodamaGrade", "kotodamaScore", "kotodamaRank", "kotodamaNotes"]
    for col in new_cols:
        if col not in roster["cols"]:
            roster["cols"].append(col)

    total_horses = 0
    for race in roster["races"]:
        horses = race["horses"]
        # スコアリング
        for horse in horses:
            result = score_horse(
                horse.get("danwaComment", ""),
                horse.get("syoinComment", ""),
            )
            horse["kotodamaGrade"] = result["grade"]
            horse["kotodamaScore"] = result["score"]
            horse["kotodamaRank"] = 0  # 後で付与
            horse["kotodamaNotes"] = " | ".join(result["notes"])

        # レース内ランキング（score降順、同点はgradeで）
        sorted_horses = sorted(
            horses,
            key=lambda h: (-h["kotodamaScore"], GRADE_ORDER.get(h["kotodamaGrade"], 9)),
        )
        for rank, horse in enumerate(sorted_horses, start=1):
            # 同スコアは同順位
            horse["kotodamaRank"] = rank

        total_horses += len(horses)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    return roster


def print_summary(roster: dict):
    venue = roster["venue"]
    print(f"\n{'='*60}")
    print(f"  {venue}  {roster['date']}")
    print(f"{'='*60}")
    for race in roster["races"]:
        rn = race["raceNum"]
        rname = race.get("raceName", "")
        horses = sorted(race["horses"], key=lambda h: h["kotodamaRank"])
        top3 = " / ".join(
            f"[{h['kotodamaRank']}]{h['name']}({h['kotodamaGrade']}:{h['kotodamaScore']})"
            for h in horses[:3]
        )
        print(f"  {rn} {rname[:12]:<12} TOP3: {top3}")


# ──────────────────────────────────────────────
# メイン
# ──────────────────────────────────────────────
BASE = Path("/Users/buntawakase/Desktop/ug-keiba/docs/data/kotodama-test")
import sys as _sys
_date = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17").replace("-", "")
FILES = [
    BASE / f"{_date}_tokyo_roster.json",
    BASE / f"{_date}_kyoto_roster.json",
    BASE / f"{_date}_niigata_roster.json",
]

grand_total = 0
for fp in FILES:
    if not fp.exists():
        print(f"⚠ ファイルなし: {fp}")
        continue
    roster = process_roster(fp)
    print_summary(roster)
    total = sum(len(r["horses"]) for r in roster["races"])
    grand_total += total
    print(f"  → {fp.name} 保存完了 ({total}頭)")

print(f"\n✅ 全{grand_total}頭スコアリング完了")
