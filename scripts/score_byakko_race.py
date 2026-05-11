"""
🐅 白虎レース採点モジュール（v0.1 / 5/17本番）

入力:
  - race-notes JSON （horses[] に jockey/trainer/comment/relComment 等）
  - JRDB n_live JSON （docs/data/byakko/{date}_{code}_nlive.json）
  - keibabook 短評（race-notes の relComment.keyword または別途 tanpyou フィールド）

出力:
  各馬に byakko: {score, tier, mark, hits, jrdb_score, book_score} を付与し、
  上位順に並んだリストを返す。
"""
import json
from pathlib import Path
from byakko_dict import byakko_score

ROOT = Path(__file__).resolve().parent.parent
RN_DIR = ROOT / "docs" / "data" / "race-notes"
NLIVE_DIR = ROOT / "docs" / "data" / "byakko"


def load_nlive(yyyymmdd: str, race_code: str) -> dict:
    """JRDB n_live が保存されていれば馬番→{buri,bagu}を返す。なければ空。"""
    p = NLIVE_DIR / f"{yyyymmdd}_{race_code}_nlive.json"
    if not p.exists():
        return {}
    return json.load(open(p)).get("horses", {})


def extract_tanpyou(horse: dict) -> str:
    """keibabook 短評相当のテキストを馬データから抽出"""
    parts = []
    rc = horse.get("relComment") or {}
    if isinstance(rc, dict):
        for k in ("keyword", "tanpyou", "trainer", "interview"):
            v = rc.get(k)
            if isinstance(v, str):
                parts.append(v)
    if isinstance(horse.get("tanpyou"), str):
        parts.append(horse["tanpyou"])
    if isinstance(horse.get("comment"), str):
        parts.append(horse["comment"])
    return " ".join(parts)


def score_race(horses: list, nlive_map=None) -> list:
    """各馬を白虎採点して、score 降順にソート"""
    nlive_map = nlive_map or {}
    out = []
    for h in horses:
        num = h.get("num") or h.get("umaban")
        nlive = nlive_map.get(str(num)) or nlive_map.get(num) or {}
        buri = nlive.get("buri", "")
        bagu = nlive.get("bagu", "")
        tanpyou = extract_tanpyou(h)
        bs = byakko_score(buri=buri, bagu=bagu, tanpyou=tanpyou)
        out.append({
            "num": num,
            "name": h.get("name"),
            "byakko": bs,
        })
    out.sort(key=lambda x: -x["byakko"]["score"])
    return out


def pick_anaba(byakko_ranked: list, kotodama_top3_names: set):
    """
    白虎の中から「穴」を選定。
    優先順位:
      1. 言霊1-3位に既に居る馬は除外（多様性確保）
      2. byakko.score >= 1.5（軽白虎以上）
      3. score 最高
    該当無しなら None（呼び出し側で言霊4位フォールバック）
    """
    for cand in byakko_ranked:
        if cand["name"] in kotodama_top3_names:
            continue
        if cand["byakko"]["score"] >= 1.5:
            return cand
    return None


def process(race_key: str, kotodama_top3: list[str], yyyymmdd: str = "", race_code: str = ""):
    """1レース分の白虎処理。戻り値: 穴馬 or None + ランキング"""
    p = RN_DIR / f"{race_key}.json"
    if not p.exists():
        return None, []
    d = json.load(open(p))
    horses = d.get("horses") or []
    nlive_map = load_nlive(yyyymmdd, race_code) if yyyymmdd else {}
    ranked = score_race(horses, nlive_map)
    anaba = pick_anaba(ranked, set(kotodama_top3))
    return anaba, ranked


if __name__ == "__main__":
    # スモークテスト
    fake_horses = [
        {"num": 13, "name": "キボウホー", "comment": "遮眼革を着用"},
        {"num": 9,  "name": "ヘクセンハウス", "comment": "自己条件戻り"},
        {"num": 12, "name": "エバーウインド", "comment": "目先替えるが"},
        {"num": 1,  "name": "ノーマル馬", "comment": "順調に乗り込み"},
    ]
    fake_nlive = {"13": {"buri": "初B", "bagu": ""}}
    ranked = score_race(fake_horses, fake_nlive)
    for r in ranked:
        print(f"  {r['num']:2}番 {r['name']:12} {r['byakko']['mark']:4} {r['byakko']['score']:4.1f} {r['byakko']['tier']}")
    anaba = pick_anaba(ranked, {"言霊1位馬", "言霊2位馬", "言霊3位馬"})
    print(f"\n🐅 穴: {anaba['name']} (⚡ {anaba['byakko']['score']})" if anaba else "穴: 該当なし→言霊4位充当")
