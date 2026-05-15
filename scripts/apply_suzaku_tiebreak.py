#!/usr/bin/env python3
"""
apply_suzaku_tiebreak.py — 朱雀スコア付与 + 救済フラグ

【設計哲学】
  印（◎○▲激）はニックが言霊分析で確定させたもの。
  このスクリプトは「上書き禁止」。データ付与と救済提案のみ。

【処理フロー】
  1. kotodama-test JSON を読む
  2. jockey master JSON で各pick馬に suzakuScore/Grade/Avg を付与
  3. 救済候補レースを検出（全picks言霊C/D）→ rescueCandidate フラグ
  4. JSON に書き戻す（印は一切変えない）

【タイブレーク】
  HTML側の reorderPicksByTiebreaker() が
  言霊grade→suzakuScore の2段ソートを自動実行（表示のみ）

Usage:
  python3 scripts/apply_suzaku_tiebreak.py 2026-05-16
  python3 scripts/apply_suzaku_tiebreak.py 2026-05-16 --dry-run
"""

import json, sys, argparse
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs/data/kotodama-test"
JOCK_DIR = ROOT / "docs/data/jockey"

# 週次更新: 最新マスターに差替え
JOCKEY_MASTER = JOCK_DIR / "2026-05-11_master149.json"

# ── グレード設定 ──────────────────────────────────────
GRADE_PTS = {"S+": 8, "S": 7, "A+": 6, "A": 5, "B+": 4, "B": 3, "B-": 2, "C": 1, "D": 0}

# 朱雀: recent.avg → スコア(0-100) + grade
SUZAKU_THRESHOLDS = [
    (55, "S", 90),
    (42, "A", 70),
    (28, "B", 50),
    (16, "C", 30),
    (0,  "D", 10),
]

# 救済発動条件: 全picks言霊がこのgrade以下
RESCUE_MAX_GRADE = "C"

# ── 騎手マスター読み込み ─────────────────────────────
def load_jockey_map(path: Path) -> dict:
    if not path.exists():
        print(f"⚠ 騎手マスター未発見: {path}")
        return {}
    d = json.loads(path.read_text("utf-8"))
    jmap = {}
    for j in d.get("jockeys", {}).values():
        name = (j.get("name") or "").strip()
        if not name:
            continue
        jmap[name] = j
        for ln in (4, 3, 2):
            key = name[:ln]
            if key not in jmap:
                jmap[key] = j
    return jmap


def lookup_jockey(name: str, jmap: dict):
    if not name:
        return None
    return (jmap.get(name)
            or jmap.get(name[:4])
            or jmap.get(name[:3])
            or jmap.get(name[:2]))


def suzaku_info(jockey_name: str, jmap: dict) -> dict:
    j = lookup_jockey(jockey_name, jmap)
    if not j:
        return {"grade": None, "score": 0, "avg": None}
    recent = j.get("recent") or {}
    if recent.get("active") is False:
        return {"grade": "D", "score": 5, "avg": None}
    avg = recent.get("avg") or 0
    for thr, grade, score in SUZAKU_THRESHOLDS:
        if avg >= thr:
            return {"grade": grade, "score": score, "avg": round(avg, 1)}
    return {"grade": "D", "score": 5, "avg": None}


def grade_pts(g: str) -> int:
    return GRADE_PTS.get(g, 0)


# ── メイン処理 ────────────────────────────────────────
def process(date_str: str, dry_run: bool):
    path = DATA_DIR / f"{date_str}.json"
    if not path.exists():
        print(f"❌ ファイル未発見: {path}")
        sys.exit(1)

    data = json.loads(path.read_text("utf-8"))
    jmap = load_jockey_map(JOCKEY_MASTER)
    print(f"  🔥 騎手マスター: {sum(1 for j in jmap.values() if isinstance(j,dict) and 'ccd' in j)} 騎手")

    suzaku_added   = 0
    rescue_flagged = 0
    tie_races      = []

    print(f"\n📋 {date_str} — {len(data['races'])}レース処理中...\n")

    for r in data["races"]:
        picks = r.get("picks", [])
        if not picks:
            continue
        label = r.get("venue", "") + r.get("raceNum", "")

        # ① 各pick馬に suzakuScore/Grade/Avg を付与（印変更なし）
        for p in picks:
            sz = suzaku_info(p.get("jockey", ""), jmap)
            p["suzakuGrade"] = sz["grade"]
            p["suzakuScore"] = sz["score"]
            p["suzakuAvg"]   = sz["avg"]
            suzaku_added += 1

        # ② タイブレーク検出（表示のみ・印変更なし）
        main_picks = [p for p in picks if p.get("mark") != "激"]
        if len(main_picks) >= 2:
            top_grade = max(grade_pts(p.get("kotodamaGrade","D")) for p in main_picks)
            top_group = [p for p in main_picks if grade_pts(p.get("kotodamaGrade","D")) == top_grade]
            if len(top_group) >= 2:
                # 同grade馬が複数いる → タイブレーク候補
                r["tiebreakActive"] = True
                tie_races.append(label)
                sorted_top = sorted(top_group, key=lambda p: -p.get("suzakuScore",0))
                print(f"  🔀 タイブレーク候補 [{label}] (言霊{['S+','S','A+','A','B+','B','B-','C','D'][8-top_grade]}×{len(top_group)}頭):")
                for p in sorted_top:
                    sz_str = f"朱雀{p['suzakuGrade'] or '?'}({p['suzakuAvg'] or '-'}%)"
                    print(f"     {p['mark']} {p['num']}番{p['name']} {sz_str}")
            else:
                r.pop("tiebreakActive", None)

        # ③ 救済候補検出（全picks言霊C/D のレース）
        max_grade = max(grade_pts(p.get("kotodamaGrade","D")) for p in picks)
        if max_grade <= grade_pts(RESCUE_MAX_GRADE):
            # 朱雀S/A馬がいるか確認
            best_sz = max(picks, key=lambda p: p.get("suzakuScore",0))
            if best_sz.get("suzakuGrade") in ("S", "A"):
                r["rescueCandidate"] = True
                r["rescueNote"] = (
                    f"全picks言霊C/D。朱雀{best_sz['suzakuGrade']}({best_sz['suzakuAvg']}%): "
                    f"{best_sz['num']}番{best_sz['name']}→◎昇格候補"
                )
                rescue_flagged += 1
                print(f"  🚨 救済候補 [{label}] → {best_sz['num']}番{best_sz['name']} "
                      f"朱雀{best_sz['suzakuGrade']}({best_sz['suzakuAvg']}%) ← ニック確認を")
            else:
                r.pop("rescueCandidate", None)
                r.pop("rescueNote", None)
        else:
            r.pop("rescueCandidate", None)
            r.pop("rescueNote", None)

    # ── サマリー ──
    print(f"\n{'='*52}")
    print(f"✅ suzakuScore 付与: {suzaku_added}頭")
    print(f"🔀 タイブレーク候補: {len(tie_races)}レース  {tie_races[:8]}")
    print(f"🚨 救済候補: {rescue_flagged}レース")
    print(f"\n【重要】印は一切変更していません。")
    print(f"タイブレークはHTML表示で自動処理。救済は上記のニック確認後に手動変更。")

    if dry_run:
        print("\n[dry-run] ファイル書き込みスキップ")
        return

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 保存: {path}")


def main():
    ap = argparse.ArgumentParser(description="朱雀スコア付与＋救済検出")
    ap.add_argument("date", help="対象日 YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    process(args.date, args.dry_run)


if __name__ == "__main__":
    main()
