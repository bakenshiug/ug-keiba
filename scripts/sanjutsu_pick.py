import sys as _sys
_date = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17").replace("-", "")
#!/usr/bin/env python3
"""
三術ピック v1.0
kotodamaScore × 1.0 + suzakuScore × 0.5 + genbuScore × 0.3 の合算スコアで
各レースの上位3頭に ◎/○/▲ を付与してroster.jsonに保存。

全頭スコア(kotodama/suzaku/genbu)は一切変更しない。
totalScore / pickMark / pickRank のみ追記。
"""

import json
from pathlib import Path

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")
ROSTER_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_roster.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_roster.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_roster.json",
}

# 合算ウェイト
W_KOTODAMA = 1.0
W_SUZAKU   = 0.5
W_GENBU    = 0.3

# 印マップ
MARK_MAP = {1: "◎", 2: "○", 3: "▲"}


def calc_total(horse: dict) -> float:
    k = horse.get("kotodamaScore", 0.0) or 0.0
    s = horse.get("suzakuScore",   0.0) or 0.0
    g = horse.get("genbuScore",    0.0) or 0.0
    return round(k * W_KOTODAMA + s * W_SUZAKU + g * W_GENBU, 3)


def process_roster(venue: str, path: Path):
    with open(path, encoding="utf-8") as f:
        roster = json.load(f)

    # cols 追記
    for col in ["totalScore", "pickMark", "pickRank"]:
        if col not in roster["cols"]:
            roster["cols"].append(col)

    race_summaries = []

    for race in roster["races"]:
        horses = race["horses"]

        # totalScore 付与
        for h in horses:
            h["totalScore"] = calc_total(h)
            h["pickMark"]   = ""
            h["pickRank"]   = 0

        # totalScore 降順ソート（同点: kotodamaScore → suzakuScore → 馬番）
        ranked = sorted(
            horses,
            key=lambda h: (
                -h["totalScore"],
                -h.get("kotodamaScore", 0),
                -h.get("suzakuScore", 0),
                -h.get("genbuScore", 0),
                h.get("num", 99),
            )
        )

        # 上位3頭に印を付与
        for rank, horse in enumerate(ranked[:3], start=1):
            # horse オブジェクトは roster["horses"] の参照なので直接変更でOK
            horse["pickMark"] = MARK_MAP[rank]
            horse["pickRank"] = rank

        race_summaries.append((race["raceNum"], race.get("raceName", ""), ranked[:3]))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    return roster, race_summaries


def print_venue_picks(venue: str, roster: dict, summaries: list):
    print(f"\n{'='*70}")
    print(f"  🎯 三術ピック — {venue}  {roster['date']}")
    print(f"  ウェイト: 言霊×1.0 + 朱雀×0.5 + 玄武×0.3")
    print(f"{'='*70}")
    for rn, rname, top3 in summaries:
        picks_str = "  ".join(
            f"{h['pickMark']}{h['name']}[{h.get('kotodamaGrade','?')}] T={h['totalScore']:.2f}"
            f"(言{h.get('kotodamaScore',0):.1f}+朱{h.get('suzakuScore',0):.2f}+玄{h.get('genbuScore',0):.2f})"
            for h in top3
        )
        print(f"  {rn:>2}R {rname[:8]:<8} {picks_str}")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    grand = 0
    for venue, path in ROSTER_FILES.items():
        if not path.exists():
            print(f"⚠ ファイルなし: {path}")
            continue
        roster, summaries = process_roster(venue, path)
        print_venue_picks(venue, roster, summaries)
        total = sum(len(r["horses"]) for r in roster["races"])
        picks = sum(1 for r in roster["races"] for h in r["horses"] if h["pickMark"])
        grand += total
        print(f"  → {path.name} 保存完了（全{total}頭 / 印付き{picks}頭）")

    print(f"\n✅ 全{grand}頭 三術ピック完了（◎{grand//total if grand else 0}×36R = 108印）")
