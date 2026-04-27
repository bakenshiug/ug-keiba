#!/usr/bin/env python3
"""
UG競馬ワイド神宮 結果反映スクリプト
使い方:
  python3 scripts/update_result.py \
    --date 2026/5/3 \
    --race 天皇賞春 --grade G1 --venue 京都 --surface 芝3200m \
    --horse アドマイヤテラ --mark ☆ --pop 3 --odds 8.5 --result 1 \
    [--payout 4800] [--invest 1200] [--comment "言霊S・玄武S"]
"""
import argparse
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_JSON = BASE_DIR / "docs" / "data" / "results.json"


def result_to_type(result: int) -> str:
    if result in (1, 3):
        return "hit1"
    elif result == 2:
        return "hit2"
    else:
        return "miss"


def result_to_label(result: int) -> str:
    if result == 1:
        return "1着激走"
    elif result == 2:
        return "2着連対"
    elif result == 3:
        return "3着激走"
    else:
        return f"{result}着 外れ"


def main():
    parser = argparse.ArgumentParser(description="UG神宮 結果反映ツール")
    parser.add_argument("--date",    required=True, help="例: 2026/5/3")
    parser.add_argument("--race",    required=True, help="例: 天皇賞春")
    parser.add_argument("--grade",   default="",   help="例: G1")
    parser.add_argument("--venue",   default="",   help="例: 京都")
    parser.add_argument("--surface", default="",   help="例: 芝3200m")
    parser.add_argument("--horse",   required=True, help="馬名")
    parser.add_argument("--mark",    required=True, help="例: ☆ / ○ / △ / 🔥朱雀1位")
    parser.add_argument("--pop",     type=int, required=True, help="番人気")
    parser.add_argument("--odds",    type=float, default=None, help="単勝オッズ")
    parser.add_argument("--result",  type=int, required=True, help="着順")
    parser.add_argument("--payout",  type=int, default=None, help="払戻金額（円）")
    parser.add_argument("--invest",  type=int, default=None, help="投資金額（円）")
    parser.add_argument("--comment", default="", help="任意コメント")
    parser.add_argument("--no-push", action="store_true", help="git pushを省略")
    args = parser.parse_args()

    entry = {
        "date":    args.date,
        "race":    args.race,
        "grade":   args.grade,
        "venue":   args.venue,
        "surface": args.surface,
        "horse":   args.horse,
        "mark":    args.mark,
        "pop":     args.pop,
        "odds":    args.odds,
        "result":  args.result,
        "label":   result_to_label(args.result),
        "type":    result_to_type(args.result),
        "payout":  args.payout,
        "invest":  args.invest,
        "comment": args.comment,
    }

    # 既存データ読込
    if RESULTS_JSON.exists():
        data = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
    else:
        RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
        data = []

    # 先頭に追加（新しい順）
    data.insert(0, entry)
    RESULTS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    rtype_emoji = {"hit1": "🎯", "hit2": "🎯", "miss": "🏴‍☠️"}.get(entry["type"], "")
    print(f"{rtype_emoji} 追加完了: {args.horse}（{args.race} {args.result}着）")
    print(f"   → {RESULTS_JSON}")

    if args.no_push:
        print("   --no-push 指定のため git push をスキップ")
        return

    # git add → commit → push
    subprocess.run(["git", "-C", str(BASE_DIR), "add", str(RESULTS_JSON)], check=True)
    subprocess.run(
        ["git", "-C", str(BASE_DIR), "commit", "-m",
         f"結果反映: {args.race} {args.horse} {args.result}着"],
        check=True
    )
    subprocess.run(["git", "-C", str(BASE_DIR), "push"], check=True)
    print("🚀 プッシュ完了！")


if __name__ == "__main__":
    main()
