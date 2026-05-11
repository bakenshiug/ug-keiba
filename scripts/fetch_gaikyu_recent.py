"""
🐢 外厩・直近3週成績スクレイパー
   JRDB joc/gk.php から取得 → docs/data/genbu/gaikyu/ に保存

使い方:
   export JRDB_USER=xxx
   export JRDB_PASS=yyy
   python3 fetch_gaikyu_recent.py

出力:
   docs/data/genbu/gaikyu/gaikyu_recent_YYYY-MM-DD.json
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import date

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("⚠ requests/bs4 が必要: pip install requests beautifulsoup4")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "data" / "genbu" / "gaikyu"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://www.jrdb.com/member/jrdv/joc/gk.php"
USER = os.environ.get("JRDB_USER")
PASS = os.environ.get("JRDB_PASS")


def parse_pct(s: str) -> float:
    """ '6 - 8 - 3 - 44 /27.9%' → 27.9 """
    m = re.search(r"/\s*([\d.]+)\s*%", s or "")
    return float(m.group(1)) if m else 0.0


def fetch() -> dict:
    auth = (USER, PASS) if USER else None
    r = requests.get(URL, auth=auth, timeout=30)
    r.encoding = r.apparent_encoding or "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if not table:
        return {"error": "no table found"}

    all_data = []
    rows = table.find_all("tr")
    for tr in rows[1:]:
        c = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(c) < 26:
            continue
        N = sum(int(c[j] or 0) for j in [2, 3, 4, 5, 6, 7])
        if N < 30:
            continue
        all_data.append({
            "rank":     int(c[0] or 0),
            "name":     c[1],
            "N":        N,
            "winRate":  float(c[8] or 0),
            "showRate": float(c[10] or 0),
            "w3":       parse_pct(c[23]),
            "w2":       parse_pct(c[24]),
            "w1":       parse_pct(c[25]),
        })

    hot = [
        x for x in all_data
        if x["w3"] >= 25 and x["w2"] >= 25 and x["w1"] >= 25
    ]
    hot.sort(key=lambda x: -(x["w1"] + x["w2"] + x["w3"]))

    return {
        "version": "v1.0",
        "snapshotDate": date.today().isoformat(),
        "source": URL,
        "filterCondition": "N >= 30",
        "totalCount": len(all_data),
        "hotList": {
            "condition": "直近3週連続で複勝率25%超",
            "count": len(hot),
            "entries": hot,
        },
        "all": all_data,
    }


def main():
    if not USER:
        print("⚠ JRDB_USER 環境変数を設定してください")
        sys.exit(1)

    print(f"📡 fetching: {URL}")
    data = fetch()
    if "error" in data:
        print(f"❌ {data['error']}")
        sys.exit(1)

    out = OUT_DIR / f"gaikyu_recent_{data['snapshotDate']}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ {data['totalCount']}件保存 → {out}")
    print(f"🔥 HOTリスト ({data['hotList']['count']}件):")
    for x in data["hotList"]["entries"]:
        print(f"   {x['name']:24} w3={x['w3']:5.1f} w2={x['w2']:5.1f} w1={x['w1']:5.1f}")


if __name__ == "__main__":
    main()
