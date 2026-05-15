"""
🐢 fetch_jrdb_roster.py — Phase1 骨格JSON生成スクリプト

JRDB の JSON API エンドポイント `racekey_json51.php` から
全36レース × 全馬の基本データを一括取得し
docs/data/kotodama-test/{date}-roster.json を生成する。

【API 仕様 (2026-05-15 解析)】
  GET /member/racekey_json51.php
    ?racedate={YYYYMMDD}
    &racekey={8桁コード}  ← JRDBコード例: 05262701
    &mode=
    &cs=047
    &ts={UNIXミリ秒}
    &username={JRDBメンバーID}   ← 数字 例: 20036286

  レスポンス JSON のキー:
    ra_al.txt_racename  = レース名 (例: "３歳未勝利")
    ky_al[]             = 全馬データ配列
      .umaban           = 馬番
      .bamei9m          = 馬名（全角）
      .kisyu3m          = 騎手
      .kisyuhenko       = 乗替フラグ
      .chokyosi3m       = 調教師
      .shozoku          = 所属（美浦/栗東）
      .houbokusaki      = 外厩（放牧先）★
      .houbokusaki_rank = 外厩ランク（1〜4）
      .nyukyudate       = 入厩日 YYYYMMDD
      .banusiname       = 馬主名（半角ｶﾅ）
      .blinkercd        = ブリンカーCD (3=着用)
      .baguname1        = 馬具名（"ブ "=ブリンカー）★
      .zenbaguname1     = 前走馬具名（初ブリ判定用）★

Auth: HTTP Basic Auth (JRDB_USER / JRDB_PASS)
      + JRDB メンバー数字ID (JRDB_MEMBER_ID)

Usage:
  export JRDB_USER=your_login_id
  export JRDB_PASS=your_password
  export JRDB_MEMBER_ID=20036286   ← JRDBトップページURLの username= の数値
  python3 fetch_jrdb_roster.py 2026-05-16

  # keibabook meeting番号を指定する場合（省略時はデフォルト値使用）:
  python3 fetch_jrdb_roster.py 2026-05-16 05:0204 08:0300 04:0107
"""

import sys, json, re, os, time
from pathlib import Path

try:
    import requests
except ImportError:
    print("⚠ pip install requests")
    sys.exit(1)

# ==========================================
# 設定
# ==========================================
BASE          = "https://jrdb.com/member"
JRDB_USER     = os.environ.get("JRDB_USER")
JRDB_PASS     = os.environ.get("JRDB_PASS")
JRDB_MEMBER_ID= os.environ.get("JRDB_MEMBER_ID", "")  # 数字ID

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "data" / "kotodama-test"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VENUE_MAP = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
    "09": "阪神", "10": "小倉"
}

# ==========================================
# raceId 変換
# ==========================================
def jrdb_to_netkeiba(date_str: str, code8: str) -> str:
    """
    JRDB 8桁 → netkeiba 12桁 raceId
    05262701 → 202605020701  (venue=05, yr=26, combined=27→kaikai=2 kaisu=7, R=01)
    """
    year     = date_str[:4]
    venue    = code8[0:2]
    combined = int(code8[4:6])
    race     = int(code8[6:8])
    kaikai   = combined // 10
    kaisu    = combined % 10
    return f"{year}{venue}{kaikai:02d}{kaisu:02d}{race:02d}"


def netkeiba_to_keibabook(netkeiba_id: str, kb_meeting_map: dict) -> str | None:
    """netkeiba 12桁 → keibabook 12桁"""
    year     = netkeiba_id[0:4]
    nk_venue = netkeiba_id[4:6]
    kaisu    = netkeiba_id[8:10]
    race     = netkeiba_id[10:12]
    if nk_venue not in kb_meeting_map:
        return None
    vmeet      = kb_meeting_map[nk_venue]
    kb_venue   = vmeet[0:2]
    kb_meeting = vmeet[2:4]
    return f"{year}{kb_venue}{kb_meeting}{kaisu}{race}"


# ==========================================
# HTTP
# ==========================================
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
    return s


def api_get(session: requests.Session, url: str) -> requests.Response:
    auth = (JRDB_USER, JRDB_PASS) if JRDB_USER else None
    r = session.get(url, auth=auth, timeout=30)
    if r.status_code == 401:
        raise RuntimeError("認証失敗(401) — JRDB_USER/JRDB_PASS を export してください")
    r.raise_for_status()
    return r


# ==========================================
# レース一覧取得
# ==========================================
def fetch_race_list(session: requests.Session, date_str: str) -> list[dict]:
    r        = api_get(session, f"{BASE}/n_index.html")
    r.encoding = r.apparent_encoding or "shift_jis"
    date_cmp = date_str.replace("-", "")
    pattern  = re.compile(rf"n_live_{date_cmp}_(\d{{8}})\.html")
    seen, races = set(), []
    for m in pattern.finditer(r.text):
        code8 = m.group(1)
        if code8 in seen:
            continue
        seen.add(code8)
        vc = code8[0:2]
        races.append({
            "code8":      code8,
            "venue_code": vc,
            "venue":      VENUE_MAP.get(vc, f"?{vc}"),
            "race_num":   int(code8[6:8]),
            "url":        f"{BASE}/n_live_{date_cmp}_{code8}.html",
        })
    races.sort(key=lambda r: (r["venue_code"], r["race_num"]))
    return races


# ==========================================
# racekey_json51.php — 1レース分を取得
# ==========================================
def fetch_race_json(session: requests.Session, date_str: str, code8: str) -> dict:
    """
    racekey_json51.php を叩いて ra_al + ky_al を返す
    """
    ts       = int(time.time() * 1000)
    date_cmp = date_str.replace("-", "")
    params   = f"racedate={date_cmp}&racekey={code8}&mode=&cs=047&ts={ts}&username={JRDB_MEMBER_ID}"
    url      = f"{BASE}/racekey_json51.php?{params}"
    r        = api_get(session, url)
    r.encoding = "utf-8"
    return r.json()


# ==========================================
# 馬データパース
# ==========================================
def parse_horse(h: dict) -> dict:
    gaikyu = h.get("houbokusaki") or ""
    if str(gaikyu) in ("null", "NULL", "None"):
        gaikyu = ""

    banushi = h.get("banusiname") or ""
    try:
        import unicodedata
        banushi = unicodedata.normalize("NFKC", banushi)
    except Exception:
        pass

    baguname1    = (h.get("baguname1")    or "").strip()
    zenbaguname1 = (h.get("zenbaguname1") or "").strip()
    bri_now  = (h.get("blinkercd") is not None and str(h.get("blinkercd")) not in ("null","NULL","None")) \
               or "ブ" in baguname1
    bri_prev = "ブ" in zenbaguname1
    hatsuri  = bri_now and not bri_prev

    kisyuhenko = h.get("kisyuhenko")
    daijo = kisyuhenko is not None and str(kisyuhenko) not in ("null", "0", "")

    return {
        "num":        str(h.get("umaban", "")).lstrip("0") or h.get("umaban",""),
        "name":       (h.get("bamei9m") or "").strip(),
        "jockey":     h.get("kisyu3m")    or "",
        "daijo":      daijo,
        "trainer":    h.get("chokyosi3m") or "",
        "belong":     h.get("shozoku")    or "",
        "gaikyu":     gaikyu,
        "gaikyuRank": h.get("houbokusaki_rank"),
        "nyukyu":     h.get("nyukyudate"),
        "banushi":    banushi,
        "bri":        bri_now,
        "hatsuBri":   hatsuri,
    }


# ==========================================
# メイン
# ==========================================
def main():
    args     = sys.argv[1:]
    date_str = args[0] if args else "2026-05-16"

    # keibabook meeting番号マップ（週次で更新）
    # キー: netkeiba venue code  値: kbVenue(2) + kbMeeting(2)
    KB_MEETING: dict[str, str] = {
        "05": "0204",  # 東京
        "08": "0300",  # 京都
        "04": "0107",  # 新潟
    }
    for arg in args[1:]:
        if ":" in arg:
            vc, kb = arg.split(":", 1)
            KB_MEETING[vc.strip()] = kb.strip()

    if not JRDB_USER:
        print("⚠  認証情報未設定。以下を実行してから再試行:")
        print("   export JRDB_USER=your_login_id")
        print("   export JRDB_PASS=your_password")
        print("   export JRDB_MEMBER_ID=20036286   # JRDBの数字メンバーID")
        sys.exit(1)

    session = make_session()

    print(f"📋 [{date_str}] JRDBレース一覧取得中...")
    races = fetch_race_list(session, date_str)
    print(f"  → {len(races)} レース発見\n")

    result      = []
    bri_summary = []

    for i, race in enumerate(races, 1):
        try:
            data     = fetch_race_json(session, date_str, race["code8"])
            ra_al    = data.get("ra_al", {})
            ky_al    = data.get("ky_al", [])
            horses   = [parse_horse(h) for h in ky_al if str(h.get("torikesi","0")) != "1"]

            nb_id    = jrdb_to_netkeiba(date_str, race["code8"])
            kb_id    = netkeiba_to_keibabook(nb_id, KB_MEETING)
            race_name= ra_al.get("txt_racename") or ""

            entry = {
                "raceId":      nb_id,
                "keibabookId": kb_id,
                "date":        date_str,
                "venue":       race["venue"],
                "raceNum":     f"{race['race_num']}R",
                "raceName":    race_name,
                "jrdbCode":    race["code8"],
                "numHorses":   len(horses),
                "horses":      horses,
            }
            result.append(entry)

            # 初ブリ / ブリ継続 まとめ
            hatsuri_list = [h for h in horses if h.get("hatsuBri")]
            bri_list     = [h for h in horses if h.get("bri") and not h.get("hatsuBri")]
            tag = ""
            if hatsuri_list:
                tag = " 🐅初ブリ:" + ",".join(f"{h['num']}番{h['name']}" for h in hatsuri_list)
                for h in hatsuri_list:
                    bri_summary.append(
                        f"  ★初ブリ  {race['venue']}{race['race_num']}R  "
                        f"{h['num']}番 {h['name']} / {h['jockey']} / {h['gaikyu'] or '在厩'}"
                    )
            elif bri_list:
                tag = " ブリ継続:" + ",".join(f"{h['num']}番" for h in bri_list)

            print(f"  [{i:02d}/{len(races)}] {race['venue']}{race['race_num']}R {race_name} — {len(horses)}頭{tag}")
            time.sleep(0.3)

        except Exception as e:
            print(f"  [{i:02d}/{len(races)}] {race['venue']}{race['race_num']}R — ❌ {e}")
            result.append({
                "raceId":  jrdb_to_netkeiba(date_str, race["code8"]),
                "venue":   race["venue"],
                "raceNum": f"{race['race_num']}R",
                "error":   str(e),
                "horses":  [],
            })

    # 保存
    out = OUT_DIR / f"{date_str}-roster.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 保存 → {out}")
    print(f"   総レース: {len(result)} / 総頭数: {sum(len(r['horses']) for r in result)}")

    if bri_summary:
        print(f"\n{'='*58}")
        print(f"🐅 初ブリンカー馬（白虎穴枠最優先）— {len(bri_summary)}頭")
        print(f"{'='*58}")
        for line in bri_summary:
            print(line)
    else:
        print("\n🐅 初ブリンカー馬: なし")


if __name__ == "__main__":
    main()
