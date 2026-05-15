#!/usr/bin/env python3
"""
朱雀スコアリング v1.0
騎手マスター(master149)のコース別複勝率 + 直近トレンドから
suzakuScore / suzakuTrend / suzakuNote を全馬に付与。
※ NULL騎手（データなし）= 0.0 フラット（減点なし）
"""

import json
import re
from pathlib import Path


MASTER_PATH = Path("docs/data/jockey/2026-05-11_master149.json")
ROSTER_FILES = {
    "東京": Path("docs/data/kotodama-test/20260516_tokyo_roster.json"),
    "京都": Path("docs/data/kotodama-test/20260516_kyoto_roster.json"),
    "新潟": Path("docs/data/kotodama-test/20260516_niigata_roster.json"),
}

# ──────────────────────────────────────────────
# 騎手マスターロード
# ──────────────────────────────────────────────
with open(MASTER_PATH, encoding="utf-8") as f:
    master_raw = json.load(f)

JOCKEY_MASTER: dict = master_raw["jockeys"]  # ccd → {name, venues, recent, ...}

# 名前→CCDの逆引き辞書（長い名前優先）
NAME_TO_CCD: dict[str, str] = {}
for ccd, joc in JOCKEY_MASTER.items():
    NAME_TO_CCD[joc["name"]] = ccd


def find_jockey(short_name: str) -> dict | None:
    """
    roster内の短縮名 → master149の騎手データを返す。
    1. 完全一致
    2. masterの名前に short_name が含まれる（substring）
    3. short_name に masterの名前が含まれる
    4. 見つからなければ None（フラット=0.0）
    """
    if not short_name:
        return None
    # 1. exact
    if short_name in NAME_TO_CCD:
        return JOCKEY_MASTER[NAME_TO_CCD[short_name]]
    # 2. master名がshort_nameを含む、またはその逆
    candidates = []
    for ccd, joc in JOCKEY_MASTER.items():
        name = joc["name"]
        if short_name in name or name in short_name:
            candidates.append(joc)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # 最長マッチを優先
        return max(candidates, key=lambda j: len(j["name"]))
    return None


# ──────────────────────────────────────────────
# コース別 shRate 取得
# ──────────────────────────────────────────────

def get_venue_sh_rate(joc_data: dict, venue: str) -> tuple[float, int]:
    """
    venue（東京/京都/新潟）に対して芝・ダ双方の shRate を確認し
    (max_shRate, total_n) を返す。データなしは (0.0, 0)。
    """
    venues = joc_data.get("venues", {})
    rates = []
    total_n = 0
    for surface in ["芝", "ダ"]:
        key = f"{venue}{surface}"
        if key in venues:
            entry = venues[key]
            n = entry.get("n", 0)
            if n >= 5:  # サンプル5件未満は無視
                rates.append(entry["shRate"])
                total_n += n
    if not rates:
        return 0.0, 0
    return max(rates), total_n


# ──────────────────────────────────────────────
# 朱雀スコア変換
# ──────────────────────────────────────────────

TREND_ICON_TO_MULT = {
    "🔥": 1.25,
    "↗︎": 1.05,
    "→":  0.90,
    "↘︎": 0.75,
}


def calc_suzaku_score(joc_data: dict | None, venue: str) -> dict:
    """
    戻り値: {suzakuScore: float, suzakuTrend: str, suzakuNote: str}
    """
    if joc_data is None:
        return {"suzakuScore": 0.0, "suzakuTrend": "—", "suzakuNote": "DB未登録(±0)"}

    # コース別複勝率
    sh_rate, n = get_venue_sh_rate(joc_data, venue)

    # 全体複勝率 fallback（コースデータなし）
    overall_sh = joc_data.get("shRate", 0.0) or 0.0

    # コースデータなければ全体で補完（×0.7で割引）
    if sh_rate == 0.0 and overall_sh > 0:
        sh_rate = overall_sh * 0.7
        n_note = f"全体SH{overall_sh:.1f}×0.7補完"
    else:
        n_note = f"{venue}SH{sh_rate:.1f}%(n={n})"

    # 直近トレンド
    recent = joc_data.get("recent", {})
    recent_avg = recent.get("avg", 0.0) or 0.0
    trend_icon = "—"
    trend_mult = 1.0
    # trend アイコン推定
    if recent_avg >= 50:
        trend_icon = "🔥"
        trend_mult = 1.25
    elif recent_avg >= 35:
        trend_icon = "↗︎"
        trend_mult = 1.05
    elif recent_avg >= 20:
        trend_icon = "→"
        trend_mult = 0.90
    elif recent_avg > 0:
        trend_icon = "↘︎"
        trend_mult = 0.75

    # ベーススコア（0〜3.0スケール）
    # shRate 60%+ → 3.0 / 40%+ → 2.0 / 30%+ → 1.0 / 20%+ → 0.5 / else → 0
    if sh_rate >= 60:
        base = 3.0
    elif sh_rate >= 50:
        base = 2.5
    elif sh_rate >= 40:
        base = 2.0
    elif sh_rate >= 35:
        base = 1.5
    elif sh_rate >= 28:
        base = 1.0
    elif sh_rate >= 20:
        base = 0.5
    else:
        base = 0.0

    score = round(base * trend_mult, 2)
    note = f"{joc_data['name']} | {n_note} | 直近{recent_avg:.1f}%{trend_icon}({trend_mult:.2f}x) → {score}"

    return {
        "suzakuScore": score,
        "suzakuTrend": trend_icon,
        "suzakuNote": note,
    }


# ──────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────

def process_roster(venue: str, path: Path):
    with open(path, encoding="utf-8") as f:
        roster = json.load(f)

    # cols追記
    for col in ["suzakuScore", "suzakuTrend", "suzakuNote"]:
        if col not in roster["cols"]:
            roster["cols"].append(col)

    stats = {"total": 0, "matched": 0, "top3": []}
    for race in roster["races"]:
        for horse in race["horses"]:
            short = horse.get("jockey", "")
            joc_data = find_jockey(short)
            result = calc_suzaku_score(joc_data, venue)
            horse["suzakuScore"] = result["suzakuScore"]
            horse["suzakuTrend"] = result["suzakuTrend"]
            horse["suzakuNote"] = result["suzakuNote"]
            stats["total"] += 1
            if joc_data:
                stats["matched"] += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    return roster, stats


def print_venue_summary(venue: str, roster: dict):
    print(f"\n{'='*62}")
    print(f"  🔥 朱雀スコア — {venue}  {roster['date']}")
    print(f"{'='*62}")
    for race in roster["races"]:
        rn = race["raceNum"]
        rname = race.get("raceName", "")[:10]
        # suzaku降順TOP3
        sorted_h = sorted(race["horses"], key=lambda h: -h.get("suzakuScore", 0))
        top = " / ".join(
            f"{h['name']}({h['jockey']}) S={h['suzakuScore']}"
            for h in sorted_h[:3]
            if h.get("suzakuScore", 0) > 0
        )
        print(f"  {rn} {rname:<10} {top or '(全員0.0)'}")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    grand = 0
    for venue, path in ROSTER_FILES.items():
        if not path.exists():
            print(f"⚠ ファイルなし: {path}")
            continue
        roster, stats = process_roster(venue, path)
        print_venue_summary(venue, roster)
        rate = stats["matched"] / stats["total"] * 100 if stats["total"] else 0
        print(f"  → {path.name} 保存完了 ({stats['matched']}/{stats['total']}頭マッチ {rate:.0f}%)")
        grand += stats["total"]

    print(f"\n✅ 全{grand}頭 朱雀スコア付与完了")
