import sys as _sys
_date = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17").replace("-", "")
#!/usr/bin/env python3
"""
玄武スコアリング v1.0
厩舎ランク(trainer_rank) + 厩舎直近トレンド(trainer_recent) +
外厩直近複勝率(gaikyu_recent) を合算して
genbuScore / genbuTrend / genbuNote を全馬に付与。
※ NULL（DBなし）= 0.0 フラット（減点なし）
※ 馬主は今回対象外（roster未登録）
"""

import json
from pathlib import Path

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")

TRAINER_RANK_PATH  = BASE / "docs/data/genbu/trainer/trainer_rank_2026.json"
TRAINER_RECENT_PATH = BASE / "docs/data/genbu/trainer/trainer_recent_2026-05-11.json"
GAIKYU_RECENT_PATH  = BASE / "docs/data/genbu/gaikyu/gaikyu_recent_2026-05-11.json"

ROSTER_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_roster.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_roster.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_roster.json",
}

# ──────────────────────────────────────────────
# DBロード
# ──────────────────────────────────────────────

with open(TRAINER_RANK_PATH, encoding="utf-8") as f:
    _tr = json.load(f)
TRAINER_LIST: list = _tr["trainers"]  # [{name, tier, winRate, ...}]

with open(TRAINER_RECENT_PATH, encoding="utf-8") as f:
    _trr = json.load(f)
TRAINER_HOT_NAMES: set = {e["name"] for e in _trr["hotList"]["entries"]}

with open(GAIKYU_RECENT_PATH, encoding="utf-8") as f:
    _gk = json.load(f)
GAIKYU_ALL: list = _gk["all"]   # [{rank, name, showRate, w1, w2, w3, ...}]
GAIKYU_HOT_NAMES: set = {e["name"] for e in _gk["hotList"]["entries"]}

# 外厩DBをdict化（DB名 → entry）
GAIKYU_DB: dict = {g["name"]: g for g in GAIKYU_ALL}

# 外厩名エイリアス（roster名 → DB名）
# DB側が全角略称、roster側がフル表記のため変換
GAIKYU_ALIAS: dict[str, str] = {
    "ノーザンファーム天栄":       "ノーザンＦ天栄",
    "ノーザンファームしがらき":    "ノーザンＦしがらき",
    "ノーザンファーム空港":       "ノーザンＦしがらき",   # 空港=しがらき系・暫定
    "チャンピオンヒルズ":         "チャンピオンヒルズ",
    "山元トレーニングセンター":    "山元トレセン",
    "宇治田原優駿ステーブル":      "宇治田原優駿Ｓ",
    "エスティファーム小見川":      "エスティＦ小見川",
    "キャニオンファーム土山":      "キャニオンＦ土山",
    "吉澤ステーブルＷＥＳＴ":     "吉澤Ｓ－ＷＥＳＴ",
    "吉澤ステーブルＥＡＳＴ":     "吉澤Ｓ－ＥＡＳＴ",
    "阿見トレーニングセンター":    "阿見トレセン",
    "ＫＳトレーニングセンター":    "ＫＳトレーニングＣ",
    "グリーンウッド・トレーニング": "グリーンウッド",
    "有限会社高橋トレーニングセンター": "高橋ＴＣ",
    "ミッドウェイファーム":        "ミッドウェイＦ",
    "ＪＯＪＩ　ＳＴＡＢＬＥ":    "ＪＯＪＩ　Ｓ",
    "ビッグレッドファーム鉾田":    "ビッグレッドＦ鉾田",
    "フォレストヒル":             "フォレストヒル",
    "大山ヒルズ":                 "大山ヒルズ",
    "社台ファーム鈴鹿":           "社台ファーム鈴鹿",
    "松風馬事センター":            "松風馬事センター",
}

# ──────────────────────────────────────────────
# 厩舎マッチング（roster短縮名 → DBフルネーム）
# ──────────────────────────────────────────────

def find_trainer(short_name: str) -> dict | None:
    """
    roster内の短縮/略称厩舎名 → DB厩舎データを返す。
    1. 完全一致
    2. DB名に short_name が含まれる（rosterが短縮形）
    3. short_name に DB名が含まれる
    4. 見つからなければ None（フラット=0.0）
    """
    if not short_name:
        return None
    # 1. exact
    for t in TRAINER_LIST:
        if t["name"] == short_name:
            return t
    # 2 & 3. substring
    candidates = []
    for t in TRAINER_LIST:
        name = t["name"]
        if short_name in name or name in short_name:
            candidates.append(t)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # 最長マッチ優先
        return max(candidates, key=lambda x: len(x["name"]))
    return None


# ──────────────────────────────────────────────
# 外厩マッチング
# ──────────────────────────────────────────────

def find_gaikyu(roster_name: str) -> dict | None:
    """
    roster外厩名 → DB外厩データを返す。
    1. エイリアスマップで変換
    2. DB名に roster_name の先頭6文字が含まれるか確認
    3. 見つからなければ None（フラット=0.0）
    """
    if not roster_name or not roster_name.strip():
        return None

    # 1. エイリアスマップ
    db_name = GAIKYU_ALIAS.get(roster_name)
    if db_name and db_name in GAIKYU_DB:
        return GAIKYU_DB[db_name]

    # 2. 直接一致
    if roster_name in GAIKYU_DB:
        return GAIKYU_DB[roster_name]

    # 3. 先頭4文字で部分一致（ノーザンＦ系など）
    prefix = roster_name[:4]
    candidates = [g for name, g in GAIKYU_DB.items() if prefix in name or name[:4] in roster_name]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        return max(candidates, key=lambda x: len(x["name"]))

    return None


# ──────────────────────────────────────────────
# 厩舎スコア
# ──────────────────────────────────────────────

TIER_BASE: dict[str, float] = {
    "S": 2.0,
    "A": 1.5,
    "B": 1.0,
    "C": 0.5,
    "D": 0.3,
    "E": 0.0,
}
TRAINER_HOT_BONUS = 0.3


def calc_trainer_score(short_name: str) -> tuple[float, str]:
    """
    戻り値: (score, note_str)
    """
    tdata = find_trainer(short_name)
    if tdata is None:
        return 0.0, f"厩舎DB未登録({short_name or '空欄'})"

    base = TIER_BASE.get(tdata["tier"], 0.0)
    hot = tdata["name"] in TRAINER_HOT_NAMES
    score = base + (TRAINER_HOT_BONUS if hot else 0.0)
    hot_str = "🔥" if hot else ""
    note = f"厩舎{tdata['name']}[{tdata['tier']}]({base:.1f}){hot_str}"
    return score, note


# ──────────────────────────────────────────────
# 外厩スコア
# ──────────────────────────────────────────────

def calc_gaikyu_score(roster_name: str) -> tuple[float, str]:
    """
    複勝率(showRate)ベースで採点。
    戻り値: (score, note_str)
    """
    gdata = find_gaikyu(roster_name)
    if gdata is None:
        label = roster_name if roster_name and roster_name.strip() else "外厩なし"
        return 0.0, f"外厩DB未登録({label})"

    sh = gdata.get("showRate", 0.0) or 0.0
    if sh >= 30:
        base = 2.0
    elif sh >= 25:
        base = 1.5
    elif sh >= 20:
        base = 1.0
    elif sh >= 15:
        base = 0.5
    else:
        base = 0.0

    hot = gdata["name"] in GAIKYU_HOT_NAMES
    score = base + (0.5 if hot else 0.0)
    hot_str = "🔥" if hot else ""
    note = f"外厩{gdata['name']}[SH{sh:.1f}%]({base:.1f}){hot_str}"
    return score, note


# ──────────────────────────────────────────────
# 玄武スコア集計
# ──────────────────────────────────────────────

def calc_genbu_score(trainer: str, gaikyu: str) -> dict:
    """
    戻り値: {genbuScore, genbuTrend, genbuNote}
    """
    t_score, t_note = calc_trainer_score(trainer)
    g_score, g_note = calc_gaikyu_score(gaikyu)

    total = round(t_score + g_score, 2)

    if total >= 3.0:
        trend = "🔥"
    elif total >= 2.0:
        trend = "↗︎"
    elif total >= 1.0:
        trend = "→"
    else:
        trend = "—"

    note = f"{t_note} | {g_note} → {total}"
    return {
        "genbuScore": total,
        "genbuTrend": trend,
        "genbuNote":  note,
    }


# ──────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────

def process_roster(venue: str, path: Path):
    with open(path, encoding="utf-8") as f:
        roster = json.load(f)

    # cols 追記
    for col in ["genbuScore", "genbuTrend", "genbuNote"]:
        if col not in roster["cols"]:
            roster["cols"].append(col)

    stats = {"total": 0, "trainer_matched": 0, "gaikyu_matched": 0}

    for race in roster["races"]:
        for horse in race["horses"]:
            trainer = horse.get("trainer", "")
            gaikyu  = horse.get("gaikyu", "")
            result  = calc_genbu_score(trainer, gaikyu)

            horse["genbuScore"] = result["genbuScore"]
            horse["genbuTrend"] = result["genbuTrend"]
            horse["genbuNote"]  = result["genbuNote"]

            stats["total"] += 1
            if find_trainer(trainer):
                stats["trainer_matched"] += 1
            if find_gaikyu(gaikyu):
                stats["gaikyu_matched"] += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    return roster, stats


def print_venue_summary(venue: str, roster: dict):
    print(f"\n{'='*64}")
    print(f"  🐢 玄武スコア — {venue}  {roster['date']}")
    print(f"{'='*64}")
    for race in roster["races"]:
        rn = race["raceNum"]
        rname = race.get("raceName", "")[:10]
        sorted_h = sorted(race["horses"], key=lambda h: -h.get("genbuScore", 0))
        top = " / ".join(
            f"{h['name']}({h.get('trainer','?')}) G={h['genbuScore']}"
            for h in sorted_h[:3]
            if h.get("genbuScore", 0) > 0
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
        t_rate = stats["trainer_matched"] / stats["total"] * 100 if stats["total"] else 0
        g_rate = stats["gaikyu_matched"] / stats["total"] * 100 if stats["total"] else 0
        print(f"  → {path.name} 保存完了")
        print(f"     厩舎マッチ: {stats['trainer_matched']}/{stats['total']}頭 ({t_rate:.0f}%)")
        print(f"     外厩マッチ: {stats['gaikyu_matched']}/{stats['total']}頭 ({g_rate:.0f}%)")
        grand += stats["total"]

    print(f"\n✅ 全{grand}頭 玄武スコア付与完了")
