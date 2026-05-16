#!/usr/bin/env python3
"""
kotodama.html プッシュスクリプト v1.0
kaime.json + roster.json の新スコアデータを
既存 2026-05-16.json に統合して上書き保存。

既存JSONのrace metadata（surface/distance/numHorses/startTime等）を保持しつつ
picks を新データで完全差し替え。
"""

import json
import re
import sys as _sys
from pathlib import Path

_date_arg = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17")
_date = _date_arg.replace("-", "")
_date_hyphen = _date_arg if "-" in _date_arg else f"{_date[:4]}-{_date[4:6]}-{_date[6:]}"

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")

# 入力
TARGET_JSON = BASE / f"docs/data/kotodama-test/{_date_hyphen}.json"   # 上書き先
KAIME_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_kaime.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_kaime.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_kaime.json",
}
ROSTER_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_roster.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_roster.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_roster.json",
}

# 朱雀スコア → Grade変換
def suzaku_grade(score: float) -> str:
    if score >= 2.5: return "S"
    if score >= 1.5: return "A"
    if score >= 0.8: return "B"
    if score >= 0.3: return "C"
    return "D"

# 外厩名 → 炎ランク（gaikyu-c表示用）
GAIKYU_FIRE_MAP = {
    "ノーザンファーム天栄":           "🔥🔥🔥 NF天栄",
    "ノーザンファームしがらき":        "🔥🔥🔥 NFしがらき",
    "ノーザンファーム空港":           "🔥🔥🔥 NF空港",
    "チャンピオンヒルズ":             "🔥🔥 CH",
    "エスティファーム小見川":          "🔥🔥 エスティF",
    "山元トレーニングセンター":        "🔥 山元TC",
    "宇治田原優駿ステーブル":          "🔥 宇治田原",
    "阿見トレーニングセンター":        "🔥 阿見TC",
    "グリーンウッド・トレーニング":    "🔥 GW",
    "社台ファーム鈴鹿":               "🔥 社台鈴鹿",
    "ＪＯＪＩ　ＳＴＡＢＬＥ":       "🔥 JOJI",
    "ミッドウェイファーム":            "↗ MW",
    "キャニオンファーム土山":          "→ キャニオン",
    "吉澤ステーブルＷＥＳＴ":         "→ 吉澤W",
    "吉澤ステーブルＥＡＳＴ":         "→ 吉澤E",
    "ＫＳトレーニングセンター":        "→ KS",
    "大山ヒルズ":                     "→ 大山",
    "松風馬事センター":                "→ 松風",
    "フォレストヒル":                 "→ FH",
    "ビッグレッドファーム鉾田":        "→ BRF",
}


def get_gaikyu_display(gaikyu_name: str) -> str:
    """外厩名を表示用文字列に変換"""
    if not gaikyu_name or not gaikyu_name.strip():
        return "在厩"
    return GAIKYU_FIRE_MAP.get(gaikyu_name, gaikyu_name[:8])


def build_picks_from_kaime(kaime_race: dict, roster_race_map: dict) -> list:
    """kaime.json の picks を kotodama.html 形式に変換"""
    picks = []
    for p in kaime_race.get("picks", []):
        horse_name = p["name"]
        # roster から全スコアを取得
        rh = roster_race_map.get(horse_name, {})

        pick = {
            "mark":          p["mark"],
            "num":           p["num"],
            "name":          p["name"],
            "jockey":        p.get("jockey", ""),
            "trainer":       p.get("trainer", ""),
            "kotodamaGrade": p.get("kotodamaGrade", "C"),
            "kotodamaScore": p.get("kotodamaScore", 0),
            "totalScore":    p.get("totalScore", 0),
            # 外厩表示 → GAIKYU_FIRE_MAP でランク付き短縮名
            "gaikyuGrade":   get_gaikyu_display(p.get("gaikyu", "")),
            "gaikyuFull":    p.get("gaikyu", ""),
            # 朱雀
            "suzakuGrade":   suzaku_grade(rh.get("suzakuScore", 0) or 0),
            "suzakuScore":   rh.get("suzakuScore", 0) or 0,
            "suzakuAvg":     _parse_recent_avg(rh.get("suzakuNote", "")),
            # 玄武
            "genbuScore":    rh.get("genbuScore", 0) or 0,
            "genbuTrend":    rh.get("genbuTrend", ""),
            # 激走
            "gekisouScore":  rh.get("gekisouScore", 0) or 0,
            "gekisouNote":   rh.get("gekisouNote", ""),
            # 初ブリ（新フィールド）
            "hatsuBri":      rh.get("hatsuBri", 0),
            # コメント（kaime.json のテキスト見解）
            "comment":       p.get("comment", ""),
            "byakkoNote":    "",
            # 結果（後で更新）
            "finalRank":     None,
            "finalNinki":    None,
            "ninkiPred":     None,
        }
        picks.append(pick)
    return picks


def _parse_recent_avg(suzaku_note: str) -> float:
    """suzakuNote から直近平均複勝率を抽出"""
    if not suzaku_note:
        return 0.0
    m = re.search(r"直近([\d.]+)%", suzaku_note)
    return float(m.group(1)) if m else 0.0


def build_roster_map(roster: dict, race_num: str) -> dict:
    """roster.json から horse_name → horse_data の辞書を作る"""
    for race in roster["races"]:
        if race["raceNum"] == race_num:
            return {h["name"]: h for h in race.get("horses", [])}
    return {}


def main():
    # ── 既存ターゲットJSON 読み込み（race metadata 保持用）
    with open(TARGET_JSON, encoding="utf-8") as f:
        base = json.load(f)

    # ── kaime / roster 読み込み
    kaime_data = {}
    roster_data = {}
    for venue in ["東京", "京都", "新潟"]:
        with open(KAIME_FILES[venue], encoding="utf-8") as f:
            kaime_data[venue] = json.load(f)
        with open(ROSTER_FILES[venue], encoding="utf-8") as f:
            roster_data[venue] = json.load(f)

    # ── race を venue×raceNum でインデックス化
    kaime_index = {}
    for venue, kd in kaime_data.items():
        for race in kd["races"]:
            key = (venue, race["raceNum"])
            kaime_index[key] = race

    # ── 既存JSON の各レースの picks を差し替え
    updated = 0
    skipped = 0
    for race in base["races"]:
        venue = race.get("venue", "")
        rnum = race.get("raceNum", "")
        key = (venue, rnum)

        if key not in kaime_index:
            skipped += 1
            continue

        kaime_race = kaime_index[key]
        roster_map = build_roster_map(roster_data[venue], rnum)
        new_picks = build_picks_from_kaime(kaime_race, roster_map)

        # result は保持（結果反映済みのデータを消さない）
        race["picks"] = new_picks
        updated += 1

    # ── 上書き保存
    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"✅ {TARGET_JSON.name} 更新完了")
    print(f"   更新: {updated}R / スキップ: {skipped}R")

    # ── サマリー表示
    for venue in ["東京", "京都", "新潟"]:
        kd = kaime_data[venue]
        print(f"\n  {venue} {kd['date']}")
        for race in kd["races"][:3]:
            picks_str = "  ".join(
                f"{p['mark']}{p['name']}[{p.get('kotodamaGrade','?')}]"
                for p in race["picks"]
            )
            print(f"    {race['raceNum']} {picks_str}")
        print(f"    ... 全{len(kd['races'])}R")


if __name__ == "__main__":
    main()
