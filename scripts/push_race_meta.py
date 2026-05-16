#!/usr/bin/env python3
"""
レースメタ情報プッシュ v1.0
netkeibaの出馬表HTMLから surface/distance/startTime を取得し
{DATE}.json の各レースに書き込む。

EUC-JP でHTMLをデコードして RaceData01 ブロックを解析。
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

_date_arg = (sys.argv[1] if len(sys.argv) > 1 else "2026-05-17")
_date_hyphen = _date_arg if "-" in _date_arg else f"{_date_arg[:4]}-{_date_arg[4:6]}-{_date_arg[6:]}"

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")
TARGET_JSON = BASE / f"docs/data/kotodama-test/{_date_hyphen}.json"

SHUTUBA_URL = "https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://race.netkeiba.com/",
}

# 芝/ダート/障害の略称 → 表示文字
SURFACE_MAP = {
    "芝": "芝",
    "ダ": "ダート",
    "障": "障害",
}


def fetch_race_meta(race_id: str) -> dict:
    """
    出馬表HTMLから { surface, distance, startTime, numHorses } を返す。
    失敗時は空dict。
    """
    url = SHUTUBA_URL.format(race_id=race_id)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        html = raw.decode("euc-jp", errors="ignore")
    except Exception as e:
        print(f"    ⚠ fetch error [{race_id}]: {e}")
        return {}

    # RaceData01 ブロック抽出
    m = re.search(r'RaceData01.{0,800}', html, re.DOTALL)
    if not m:
        print(f"    ⚠ RaceData01 not found [{race_id}]")
        return {}
    block = m.group()

    result = {}

    # 発走時刻
    tm = re.search(r'(\d{2}:\d{2})発走', block)
    result["startTime"] = tm.group(1) if tm else ""

    # 芝/ダート/障害 + 距離
    sd = re.search(r'([ダ芝障])(\d{3,4})m', block)
    if sd:
        abbr = sd.group(1)
        result["surface"]  = SURFACE_MAP.get(abbr, abbr)
        result["distance"] = sd.group(2) + "m"
    else:
        result["surface"]  = ""
        result["distance"] = ""

    # 頭数（RaceData02 にある）
    nh = re.search(r'(\d+)頭', block)
    if nh:
        result["numHorses"] = int(nh.group(1))

    return result


def main():
    with open(TARGET_JSON, encoding="utf-8") as f:
        base = json.load(f)

    total = 0
    skipped = 0

    for race in base["races"]:
        race_id = race.get("raceId", "")
        venue   = race.get("venue", "")
        rnum    = race.get("raceNum", "")

        if not race_id:
            skipped += 1
            continue

        meta = fetch_race_meta(race_id)
        if not meta:
            skipped += 1
            continue

        if meta.get("surface"):
            race["surface"] = meta["surface"]
        if meta.get("distance"):
            race["distance"] = meta["distance"]
        if meta.get("startTime"):
            race["startTime"] = meta["startTime"]
        if meta.get("numHorses") is not None:
            race["numHorses"] = meta["numHorses"]

        print(f"  {venue}{rnum} [{race_id}] "
              f"{meta.get('surface','')} {meta.get('distance','')} "
              f"/ {meta.get('numHorses','')}頭 "
              f"/ 発走{meta.get('startTime','')}")
        total += 1
        time.sleep(0.4)   # サーバー負荷軽減

    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"\n✅ レースメタ更新完了")
    print(f"   更新: {total}R / スキップ: {skipped}R")


if __name__ == "__main__":
    main()
