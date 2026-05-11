"""
🐅 JRDB n_live スクレイパー（白虎メソッド v0.1 / 5/17本番）
直前情報ページからブリ列・馬具列を取得し、各馬の物理「変」シグナルを抽出

URL: https://jrdb.com/member/n_live_{YYYYMMDD}_{race_code}.html
列構造: tr.tds[12]=ブリ列（初B/B）, tds[13]=馬具列（＊）

使い方:
  python3 fetch_jrdb_nlive.py 20260517 0501  # 5/17 東京1R
  python3 fetch_jrdb_nlive.py --all 20260517 # その日のJRDB全レース
"""
import sys, json, re, os
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("⚠ requests/bs4 が必要: pip install requests beautifulsoup4")
    sys.exit(1)

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "data" / "byakko"
OUT_DIR.mkdir(parents=True, exist_ok=True)

JRDB_USER = os.environ.get("JRDB_USER")
JRDB_PASS = os.environ.get("JRDB_PASS")
BASE = "https://jrdb.com/member/"


def fetch_nlive(yyyymmdd: str, race_code: str) -> dict:
    """1レース分の n_live をパースして馬番→{buri, bagu} を返す"""
    url = f"{BASE}n_live_{yyyymmdd}_{race_code}.html"
    auth = (JRDB_USER, JRDB_PASS) if JRDB_USER else None
    r = requests.get(url, auth=auth, timeout=30)
    r.encoding = r.apparent_encoding or "shift_jis"
    if r.status_code != 200:
        return {"_url": url, "_error": f"HTTP {r.status_code}"}
    soup = BeautifulSoup(r.text, "html.parser")

    horses = {}
    # JRDB n_live は <tr> ベースの表構造。馬番列を見つけて各列をindex走査
    for tr in soup.select("tr"):
        tds = tr.find_all("td")
        if len(tds) < 14:
            continue
        # 馬番カラム探索（数字1〜18のセル）
        umaban_cell = tds[1] if len(tds) > 1 else None
        if not umaban_cell:
            continue
        m = re.fullmatch(r"\s*(\d{1,2})\s*", umaban_cell.get_text(strip=True))
        if not m:
            continue
        num = int(m.group(1))
        if not (1 <= num <= 18):
            continue
        buri = tds[12].get_text(strip=True) if len(tds) > 12 else ""
        bagu = tds[13].get_text(strip=True) if len(tds) > 13 else ""
        horses[num] = {"buri": buri, "bagu": bagu}

    return {
        "_url": url,
        "_yyyymmdd": yyyymmdd,
        "_race_code": race_code,
        "horses": horses,
    }


def save(yyyymmdd: str, race_code: str, data: dict):
    out = OUT_DIR / f"{yyyymmdd}_{race_code}_nlive.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → {out}")


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    yyyymmdd, race_code = args[0], args[1]
    data = fetch_nlive(yyyymmdd, race_code)
    if "_error" in data:
        print(f"❌ {data['_error']} → {data['_url']}")
        sys.exit(1)
    print(f"✅ {len(data['horses'])}頭取得")
    save(yyyymmdd, race_code, data)


if __name__ == "__main__":
    main()
