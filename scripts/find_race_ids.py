#!/usr/bin/env python3
"""
find_race_ids.py — 開催日を入れるだけで全race_idを自動取得

使い方:
  python3 scripts/find_race_ids.py 2026-04-26
  python3 scripts/find_race_ids.py 20260426          # ハイフンなしもOK
  python3 scripts/find_race_ids.py 2026-04-26 --win5 # WIN5用config形式で出力
  python3 scripts/find_race_ids.py 2026-04-26 --json # JSON形式で出力

出力例:
  📅 2026-04-26（日）開催レース
  ─────────────────────────────────
  📍 3回中山9日 — 天気☀️ / 芝B良 / ダ良
    10R 千葉S             [OP]   16:05  ダ1200m      race_id=202606030910
    11R 天皇賞(春)          [G1]   15:40  芝3200m      race_id=202606030911
    ...
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
URL_TEMPLATE = "https://race.netkeiba.com/top/race_list_sub.html?kaisai_date={date}"

# 場所コード対応（race_id 中4-5桁）
VENUE_CODES = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
    "09": "阪神", "10": "小倉",
}

# グレードアイコン → 表示ラベル
GRADE_MAP = {
    "Icon_GradeType1":  "G1",
    "Icon_GradeType2":  "G2",
    "Icon_GradeType3":  "G3",
    "Icon_GradeType4":  "OP",   # JpnI相当（地方）
    "Icon_GradeType5":  "L",    # リステッド
    "Icon_GradeType15": "L",    # 念のため
    "Icon_GradeType16": "3勝",
    "Icon_GradeType17": "2勝",
    "Icon_GradeType18": "1勝",
}


def normalize_date(s: str) -> str:
    """'2026-04-26' or '20260426' → '20260426'"""
    s = s.replace("-", "").replace("/", "").strip()
    if len(s) != 8 or not s.isdigit():
        sys.exit(f"❌ 日付形式が不正です: {s}  (例: 2026-04-26)")
    return s


def fetch_html(date: str) -> str:
    url = URL_TEMPLATE.format(date=date)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as res:
        return res.read().decode("utf-8", errors="replace")


def parse_venues(html: str) -> list[dict]:
    """開催日の全レースをvenueごとに配列で返す"""
    venues = []
    # venueブロック: RaceList_DataHeader から 次の RaceList_DataHeader (or 末尾) まで
    # ヘッダ: <p class="RaceList_DataTitle"><small>N回</small> 場所名 <small>M日目</small></p>
    chunks = re.split(r'(?=<dt class="RaceList_DataHeader">)', html)
    for chunk in chunks:
        m = re.search(
            r'<p class="RaceList_DataTitle">\s*<small>(\d+)回</small>\s*([^<\s]+)\s*<small>(\d+)日目</small></p>',
            chunk,
        )
        if not m:
            continue
        kai, venue, nichi = m.groups()
        desc = ""
        dm = re.search(r'RaceList_DataDesc">(.*?)</div>', chunk, re.DOTALL)
        if dm:
            raw = re.sub(r"<[^>]+>", " ", dm.group(1))
            desc = re.sub(r"\s+", " ", raw).strip()

        races = []
        for rm in re.finditer(
            r'<a href="\.\./race/shutuba\.html\?race_id=(\d{12})[^"]*"[^>]*>(.*?)</a>',
            chunk,
            re.DOTALL,
        ):
            rid, inner = rm.group(1), rm.group(2)
            # R番号
            rnum_m = re.search(r'Race_Num[^>]*>\s*(?:<span[^>]*>)?\s*(?:<span[^>]*></span>)?\s*(\d+)\s*R\s*</span>', inner, re.DOTALL)
            rnum = int(rnum_m.group(1)) if rnum_m else int(rid[-2:])
            # レース名
            name_m = re.search(r'ItemTitle">([^<]+)</span>', inner)
            name = name_m.group(1).strip() if name_m else ""
            # グレード（Icon_GradeType1 が Icon_GradeType13 等に誤マッチしないよう単語境界付き）
            grade = ""
            for gclass, gname in GRADE_MAP.items():
                if re.search(rf'\b{re.escape(gclass)}\b', inner):
                    grade = gname
                    break
            # 発走時刻
            time_m = re.search(r'RaceList_Itemtime">([^<]+)</span>', inner)
            post_time = time_m.group(1).strip() if time_m else ""
            # コース
            course_m = re.search(r'RaceList_ItemLong[^"]*">([^<]+)</span>', inner)
            course = course_m.group(1).strip() if course_m else ""
            # 頭数
            heads_m = re.search(r'RaceList_Itemnumber">([^<]+)</span>', inner)
            heads = heads_m.group(1).strip() if heads_m else ""

            races.append({
                "race_id":  rid,
                "r":        rnum,
                "name":     name,
                "grade":    grade,
                "time":     post_time,
                "course":   course,
                "heads":    heads,
                "venue":    venue,
            })
        races.sort(key=lambda x: x["r"])
        venues.append({
            "kai": int(kai),
            "venue": venue,
            "nichi": int(nichi),
            "desc": desc,
            "races": races,
        })
    return venues


def fmt_pretty(date: str, venues: list[dict]) -> str:
    out = [f"\n📅 {date[:4]}-{date[4:6]}-{date[6:8]} 開催レース"]
    out.append("─" * 52)
    if not venues:
        out.append("（レースなし・開催されていない可能性あり）")
        return "\n".join(out)
    for v in venues:
        out.append(f"\n📍 {v['kai']}回{v['venue']}{v['nichi']}日 — {v['desc']}")
        for r in v["races"]:
            grade_tag = f"[{r['grade']}]".ljust(5) if r["grade"] else "     "
            out.append(
                f"  {r['r']:>2}R {r['name']:<14} {grade_tag} {r['time']:>5}  {r['course']:<12} {r['heads']:<6} race_id={r['race_id']}"
            )
    return "\n".join(out)


def fmt_win5_config(date: str, venues: list[dict]) -> str:
    """fetch_odds.py に貼り付けやすい形式で出力（主要レース候補）"""
    out = [f"# fetch_odds.py 用 RACES 候補 — {date[:4]}-{date[4:6]}-{date[6:8]}"]
    out.append("# （重賞・L・OP・特別を優先表示。WIN5指定レースは公式告知で確認してください）")
    out.append("")
    # 重賞+L+特別の10R/11Rを中心にピックアップ
    picks = []
    for v in venues:
        for r in v["races"]:
            if r["r"] in (10, 11) or r["grade"] in ("G1", "G2", "G3", "L"):
                picks.append(r)
    for r in picks:
        jpath = f'docs/data/race-notes/{date[:4]}-{date[4:6]}-{date[6:8]}-{VENUE_ROMAJI.get(r["venue"], r["venue"].lower())}-{r["r"]}r.json'
        out.append(
            f'    {{"leg":"?", "label":"{r["name"]}（{r["venue"]}{r["r"]}R）", '
            f'"race_id":"{r["race_id"]}", "json":"{jpath}"}},'
        )
    return "\n".join(out)


VENUE_ROMAJI = {
    "札幌": "sapporo", "函館": "hakodate", "福島": "fukushima", "新潟": "niigata",
    "東京": "tokyo",   "中山":   "nakayama",  "中京":   "chukyo",    "京都":   "kyoto",
    "阪神": "hanshin", "小倉":   "kokura",
}


def main():
    ap = argparse.ArgumentParser(description="開催日から全race_idを自動取得")
    ap.add_argument("date", help="開催日 (2026-04-26 or 20260426)")
    ap.add_argument("--win5",   action="store_true", help="fetch_odds.py 貼付用形式で出力")
    ap.add_argument("--json",   action="store_true", help="JSON形式で出力")
    args = ap.parse_args()

    date = normalize_date(args.date)
    print(f"🐶 {date[:4]}-{date[4:6]}-{date[6:8]} のレース情報をnetkeibaから取得中...", file=sys.stderr)
    html = fetch_html(date)
    venues = parse_venues(html)

    if args.json:
        print(json.dumps({"date": date, "venues": venues}, ensure_ascii=False, indent=2))
    elif args.win5:
        print(fmt_pretty(date, venues))
        print("\n" + "─" * 52)
        print(fmt_win5_config(date, venues))
    else:
        print(fmt_pretty(date, venues))

    # ヒント
    total = sum(len(v["races"]) for v in venues)
    print(f"\n✓ {len(venues)}開催場・{total}レース取得完了", file=sys.stderr)


if __name__ == "__main__":
    main()
