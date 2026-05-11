"""
🐢 馬主・直近成績スクレイパー
   keibabook /db/banushi/{ownerId} から各馬主の直近成績を取得
   banushi_watchlist.json をループ → docs/data/genbu/banushi/ に保存

認証:
   keibabook はログイン制。Cookie を環境変数 KEIBABOOK_COOKIE で渡す。
   ブラウザの開発者ツール → Application → Cookies からセッションCookieをコピー。
   例: export KEIBABOOK_COOKIE="PHPSESSID=xxx; loginid=yyy"

使い方:
   export KEIBABOOK_COOKIE="..."
   python3 fetch_banushi_recent.py
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import date

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("⚠ requests/bs4 が必要")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / "docs" / "data" / "genbu" / "banushi" / "banushi_watchlist.json"
OUT_DIR = ROOT / "docs" / "data" / "genbu" / "banushi"

COOKIE = os.environ.get("KEIBABOOK_COOKIE", "")


def fetch_owner(owner_id: str) -> dict:
    """1馬主の直近成績ページを取得して解析"""
    url = f"https://p.keibabook.co.jp/db/banushi/{owner_id}"
    headers = {"Cookie": COOKIE} if COOKIE else {}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "ownerId": owner_id}
    soup = BeautifulSoup(r.text, "html.parser")

    # 直近の出走履歴を抽出
    runs = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) < 10:
            continue
        # 「N着」形式のセルを含む行を出走履歴とみなす
        last = cells[-1]
        if re.match(r"^\d+着$", last):
            finish = int(re.match(r"^(\d+)", last).group(1))
            runs.append({
                "horse":  cells[0].split("\n")[0],
                "race":   cells[1] if len(cells) > 1 else "",
                "rname":  cells[2] if len(cells) > 2 else "",
                "course": cells[3] if len(cells) > 3 else "",
                "pop":    cells[8] if len(cells) > 8 else "",
                "finish": finish,
            })

    # 集計
    total = len(runs)
    in_money = sum(1 for r in runs if r["finish"] <= 3)
    show_rate = (in_money / total * 100) if total else 0.0

    return {
        "ownerId":   owner_id,
        "totalRuns": total,
        "inMoney":   in_money,
        "showRate":  round(show_rate, 1),
        "runs":      runs,
    }


def main():
    if not COOKIE:
        print("⚠ KEIBABOOK_COOKIE 環境変数が未設定")
        print("   ブラウザの開発者ツールから keibabook の cookie をコピーして:")
        print("   export KEIBABOOK_COOKIE='PHPSESSID=...; loginid=...'")
        sys.exit(1)

    watchlist = json.load(open(WATCHLIST))
    today = date.today().isoformat()
    results = []

    print(f"📡 {len(watchlist['owners'])} 馬主の直近成績を取得中...")
    for owner in watchlist["owners"]:
        oid = owner["ownerId"]
        name = owner["shortName"]
        print(f"   {name:18} (id={oid})", end=" ")
        data = fetch_owner(oid)
        data["name"] = owner["name"]
        data["shortName"] = name
        data["leadingRank"] = owner.get("leadingRank")
        results.append(data)
        if "error" not in data:
            print(f"→ {data['inMoney']}/{data['totalRuns']} ({data['showRate']}%)")
        else:
            print(f"❌ {data['error']}")
        time.sleep(1)  # サーバ負荷軽減

    # HOTリスト：直近で複勝率30%超
    hot = [
        x for x in results
        if "error" not in x and x.get("showRate", 0) >= 30
    ]
    hot.sort(key=lambda x: -x.get("showRate", 0))

    out_data = {
        "version": "v1.0",
        "snapshotDate": today,
        "totalOwners": len(results),
        "hotList": {
            "condition": "直近の複勝率30%超",
            "count": len(hot),
            "entries": [
                {"name": x["name"], "shortName": x["shortName"],
                 "showRate": x["showRate"], "inMoney": x["inMoney"],
                 "totalRuns": x["totalRuns"]}
                for x in hot
            ],
        },
        "all": results,
    }

    out_file = OUT_DIR / f"banushi_recent_{today}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 保存完了 → {out_file}")
    print(f"🔥 HOTリスト ({len(hot)}件):")
    for x in hot:
        print(f"   {x['shortName']:14} {x['showRate']:5.1f}%  ({x['inMoney']}/{x['totalRuns']})")


if __name__ == "__main__":
    main()
