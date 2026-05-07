#!/usr/bin/env python3
"""
export_x_result.py
kotodama-test JSON → X(旧Twitter)速報用テキスト生成
レース後にresult追記済みのJSONを読み込み、場別にX投稿用テキストを生成。

Usage:
    python3 scripts/export_x_result.py 2026-05-10
    python3 scripts/export_x_result.py 2026-05-10 --venue 東京
"""
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data" / "kotodama-test"
OUT_DIR = ROOT / "scripts" / "out_x"
OUT_DIR.mkdir(exist_ok=True)

X_LIMIT = 280  # 1ポスト文字数上限


def calc_payout_line(r):
    """1レース分の速報ライン生成 (例: '1R ◎10番 9着 ❌')"""
    rn = r["raceNum"]
    picks = r.get("picks", [])
    if not picks:
        return f"{rn} （picks未設定）"

    main = picks[0]  # ◎
    num = main.get("num", "?")
    rank_str = main.get("finalRank", "")
    odds_str = main.get("finalOdds", "")

    if not rank_str or rank_str == "":
        return f"{rn} ◎{num}番 結果待ち"

    try:
        rank = int(rank_str)
    except ValueError:
        return f"{rn} ◎{num}番 {rank_str}"

    # 結果判定
    if rank == 1:
        return f"{rn} ◎{num} 1着！単¥{int(float(odds_str)*100) if odds_str else '?'} 🎯"
    elif rank == 2:
        return f"{rn} ◎{num} 2着 ✅"
    elif rank == 3:
        return f"{rn} ◎{num} 3着 ✅"
    elif rank <= 5:
        return f"{rn} ◎{num} {rank}着 ⚠"
    else:
        return f"{rn} ◎{num} {rank}着 ❌"


def fmt_venue_post(date, venue, races):
    """1場分のX投稿テキスト（複数ポストに分割）"""
    posts = []

    header = f"🏆 神宮 {date} {venue} 結果速報\n\n"
    footer = f"\n\n詳細→ bakenshiug.github.io/ug-keiba/kotodama-test.html\n#神宮 #競馬予想"

    races_sorted = sorted(races, key=lambda r: int(r["raceNum"].replace("R", "")))

    # 着順カウント集計
    hit = 0
    win = 0
    fuku = 0
    for r in races_sorted:
        picks = r.get("picks", [])
        if not picks:
            continue
        rs = picks[0].get("finalRank", "")
        try:
            rk = int(rs)
            if rk == 1:
                win += 1
                hit += 1
            elif rk <= 3:
                fuku += 1
                hit += 1
        except ValueError:
            pass

    # 投稿1：ヘッダー＋成績サマリ
    summary = f"{header}的中：{hit}/12（◎勝ち {win}・複勝 {fuku}）\n\n[1] 1〜6R\n"
    body1 = ""
    for r in races_sorted[:6]:
        body1 += calc_payout_line(r) + "\n"
    posts.append(summary + body1.strip() + footer)

    # 投稿2：7〜12R
    body2 = "[2] 7〜12R\n"
    for r in races_sorted[6:12]:
        body2 += calc_payout_line(r) + "\n"
    posts.append(body2.strip() + footer)

    return posts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("--venue", default=None)
    args = parser.parse_args()

    src = DATA_DIR / f"{args.date}.json"
    if not src.exists():
        print(f"❌ ファイル未存在: {src}", file=sys.stderr)
        sys.exit(1)

    data = json.load(open(src))
    races = data.get("races", [])

    venues = {}
    for r in races:
        venues.setdefault(r["venue"], []).append(r)

    target_venues = [args.venue] if args.venue else list(venues.keys())

    for v in target_venues:
        if v not in venues:
            continue
        posts = fmt_venue_post(args.date, v, venues[v])
        out = OUT_DIR / f"{args.date}_{v}.txt"
        with open(out, "w", encoding="utf-8") as f:
            for i, p in enumerate(posts, 1):
                f.write(f"========== POST {i} ({len(p)}字) ==========\n")
                f.write(p)
                f.write("\n\n")
        print(f"✅ {out}")
        for i, p in enumerate(posts, 1):
            mark = "⚠ OVER" if len(p) > X_LIMIT else "OK"
            print(f"  POST {i}: {len(p)}字 [{mark}]")


if __name__ == "__main__":
    main()
