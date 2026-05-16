#!/usr/bin/env python3
"""
想定オッズ・レース情報プッシュ v1.0
netkeiba 単勝オッズ API から各馬の想定人気(ninkiPred)を取得し
2026-05-16.json の picks.ninkiPred を更新する。

APIレスポンス例:
  data.odds["1"]["01"] = ["2.8", "", "1"]  → 馬番01: 2.8倍・1番人気
"""

import json
import sys as _sys
import time
import urllib.request
from pathlib import Path

_date_arg = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17")
_date_hyphen = _date_arg if "-" in _date_arg else f"{_date_arg[:4]}-{_date_arg[4:6]}-{_date_arg[6:]}"

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")
TARGET_JSON = BASE / f"docs/data/kotodama-test/{_date_hyphen}.json"

ODDS_API = (
    "https://race.netkeiba.com/api/api_get_jra_odds.html"
    "?race_id={race_id}&type=1&action=update"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://race.netkeiba.com/",
}


def fetch_odds_ninki(race_id: str) -> dict[int, int]:
    """
    単勝オッズAPIから { 馬番(int) → 人気(int) } を返す。
    取得失敗時は空dict。
    """
    url = ODDS_API.format(race_id=race_id)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        odds_1 = payload["data"]["odds"]["1"]  # 単勝オッズ dict
        result = {}
        for num_str, val in odds_1.items():
            try:
                ninki = int(val[2])   # 3番目要素が人気順位
                # "07" → 7 → "7" に正規化（pick.num は "7" 形式の文字列）
                result[str(int(num_str))] = ninki
            except (IndexError, ValueError):
                pass
        return result
    except Exception as e:
        print(f"    ⚠ fetch error [{race_id}]: {e}")
        return {}


def main():
    with open(TARGET_JSON, encoding="utf-8") as f:
        base = json.load(f)

    total_picks = 0
    total_races = 0
    skipped = 0

    for race in base["races"]:
        race_id = race.get("raceId", "")
        venue   = race.get("venue", "")
        rnum    = race.get("raceNum", "")

        if not race_id:
            skipped += 1
            continue

        odds_map = fetch_odds_ninki(race_id)
        if not odds_map:
            print(f"  ⚠ {venue}{rnum} ({race_id}) オッズ取得失敗")
            skipped += 1
            continue

        updated = 0
        for pick in race.get("picks", []):
            horse_num = pick.get("num")
            if horse_num is not None:
                # "08" → "8" に正規化（ゼロパディング除去）
                normalized = str(int(str(horse_num)))
                if normalized in odds_map:
                    pick["ninkiPred"] = odds_map[normalized]
                    updated += 1

        total_picks += updated
        total_races += 1

        # 人気ラベル付きサマリー
        picks_str = "  ".join(
            f"{p['mark']}{p['name']}→{p.get('ninkiPred','?')}人気"
            for p in race.get("picks", [])
        )
        print(f"  {venue}{rnum} [{race_id}] {picks_str}")

        time.sleep(0.3)   # API負荷軽減

    # 上書き保存
    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"\n✅ ninkiPred更新完了")
    print(f"   更新: {total_races}R / {total_picks}頭 / スキップ: {skipped}R")

    # ── サマリー表示（各場3Rまで）
    for venue in ["東京", "京都", "新潟"]:
        races = [r for r in base["races"] if r["venue"] == venue]
        print(f"\n  {venue}")
        for r in races[:3]:
            picks_summary = "  ".join(
                f"{p['mark']}{p['name']}[{p.get('ninkiPred','?')}人気]"
                for p in r.get("picks", [])
            )
            print(f"    {r['raceNum']}: {picks_summary}")
        print(f"    ... 全{len(races)}R")


if __name__ == "__main__":
    main()
