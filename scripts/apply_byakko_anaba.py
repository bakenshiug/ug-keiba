"""
🐅 白虎「穴」枠 picks 組成パイプライン（v0.1 / 5/17本番）

入力:
  --picks-json  既存 picks JSON （例: docs/data/kotodama-test/2026-05-17.json）
                各 race.picks には ◎○▲ の3頭 + 4頭目（言霊4位）が入っている前提
  --date        対象日 (YYYYMMDD)。JRDB n_live ファイル名と突合
  --apply       書き込み実行（デフォルトは dry-run）

処理:
  各レースで:
    1. picks の ◎○▲ 名を取得（言霊1-3位）
    2. race-notes JSON を読んで全頭白虎採点
    3. pick_anaba() で穴候補を抽出
       - 白虎スコア >= 1.5 ＆ ◎○▲と重複しない最高スコア馬がいれば採用
       - 居なければ既存4頭目（言霊4位）をそのまま「穴」マークだけ振り直す
    4. picks[3] を白虎馬で差替、mark="穴" に変更、byakko 情報を埋め込み

出力:
  各 race.picks[3] が以下スキーマに統一:
    {mark:"穴", num, name, jockey, trainer,
     kotodamaGrade, byakkoMark:"⚡⚡⚡", byakkoScore:6.5,
     byakkoTier:"白虎降臨", byakkoHits:[...],
     comment: "🐅 初B＋遮眼革で陣営本気度MAX..."}
"""
import json, argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_byakko_race import score_race, pick_anaba, load_nlive

ROOT = Path(__file__).resolve().parent.parent
RN_DIR = ROOT / "docs" / "data" / "race-notes"


def race_code_from_id(race_id: str) -> str:
    """race_id (例 202604010301) → JRDB race_code (例 0301 or 0501)"""
    # JRDB n_live URL の race_code は通常「会場2桁+R番号2桁」
    # race_id 末尾4桁 = 場所コード+R or 開催日+R...形式が混在するためそのまま末尾4桁を返す
    return race_id[-4:]


def comment_for_anaba(byakko: dict, name: str) -> str:
    hits = "・".join(byakko["hits"][:3]) if byakko["hits"] else ""
    if byakko["score"] >= 5.0:
        return f"🐅 白虎降臨{byakko['mark']} {hits}。陣営本気度MAX、穴の温床。"
    if byakko["score"] >= 3.0:
        return f"🐅 強白虎{byakko['mark']} {hits}。「変える」意志あり、要警戒。"
    if byakko["score"] >= 1.5:
        return f"🐅 軽白虎{byakko['mark']} {hits}。微シグナル捕捉。"
    return "（白虎無印・言霊4位を穴枠に充当）"


def apply_byakko_to_race(race: dict, yyyymmdd: str) -> dict:
    """1レース分の picks を白虎で書き換え。書き換え結果のメタ情報を返す"""
    picks = race.get("picks") or []
    if len(picks) < 3:
        return {"skipped": "picks<3"}

    race_id = race.get("raceId", "")
    rn_path = RN_DIR / f"{race_id}.json"
    if not rn_path.exists():
        return {"skipped": f"race-notes 無し: {race_id}"}

    horses = json.load(open(rn_path)).get("horses") or []
    nlive = load_nlive(yyyymmdd, race_code_from_id(race_id)) if yyyymmdd else {}

    top3_names = {p.get("name") for p in picks[:3]}
    ranked = score_race(horses, nlive)
    anaba = pick_anaba(ranked, top3_names)

    if anaba:
        # 白虎馬で4頭目を差替
        match = next((h for h in horses if h.get("name") == anaba["name"]), {})
        new_pick = {
            "mark": "穴",
            "num": anaba["num"],
            "name": anaba["name"],
            "jockey": match.get("jockey", "—"),
            "trainer": match.get("trainer", "—"),
            "kotodamaGrade": match.get("kotodamaGrade", "—"),
            "byakkoMark": anaba["byakko"]["mark"],
            "byakkoScore": anaba["byakko"]["score"],
            "byakkoTier": anaba["byakko"]["tier"],
            "byakkoHits": anaba["byakko"]["hits"],
            "comment": comment_for_anaba(anaba["byakko"], anaba["name"]),
        }
        # 言霊4位の元馬情報は orig4th として温存
        if len(picks) >= 4:
            new_pick["orig4th"] = {
                "name": picks[3].get("name"),
                "kotodamaGrade": picks[3].get("kotodamaGrade"),
            }
        if len(picks) >= 4:
            picks[3] = new_pick
        else:
            picks.append(new_pick)
        race["picks"] = picks
        return {"swapped": anaba["name"], "score": anaba["byakko"]["score"]}
    else:
        # 白虎無印 → 既存4位の mark だけ "穴" に変更
        if len(picks) >= 4:
            picks[3]["mark"] = "穴"
            picks[3].setdefault("comment", "")
            picks[3]["comment"] = (picks[3]["comment"] or "") + " ／ 🐅白虎無印・言霊4位充当"
        return {"fallback": "言霊4位充当"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks-json", required=True)
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    p = Path(args.picks_json)
    data = json.load(open(p))
    summary = []
    for race in data.get("races", []):
        if race.get("date", "").replace("-", "") != args.date:
            continue
        meta = apply_byakko_to_race(race, args.date)
        summary.append((race.get("raceId"), race.get("raceName"), meta))

    print(f"\n🐅 白虎適用結果（dry-run={'no' if args.apply else 'YES'}）")
    for rid, rname, meta in summary:
        print(f"  {rid} {rname}: {meta}")

    if args.apply:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 書き込み完了: {p}")
    else:
        print("\n（--apply 付けると書き込み）")


if __name__ == "__main__":
    main()
