#!/usr/bin/env python3
"""
激走ピック v1.0
◎/○/▲ 以外の馬から、各レース1頭の「激走候補」を選出。

採点軸:
  ① 初ブリンカー(hatsuBri=1)       +3.0
  ② 馬具変更キーワード(非初ブリ)    +2.0
  ③ 一変・変わり身キーワード        +2.0
  ④ 距離/コース/芝ダ転換キーワード   +1.5
  ⑤ 装具微調整キーワード            +0.5
  ⑥ 玄武スコア補正                  genbuScore × 0.4
  ⑦ 高言霊ボーナス（非ピックで7.0+） +0.5

gekisouScore = ①〜⑥⑦ 合算
同点: gekisouScore → genbuScore → kotodamaScore → 馬番
"""

import json
import sys as _sys
from pathlib import Path

_date = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17").replace("-", "")

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")
ROSTER_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_roster.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_roster.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_roster.json",
}

# ──────────────────────────────────────────────
# キーワード定義
# ──────────────────────────────────────────────

# ② 馬具変更（装具を「変える」ことを示すフレーズ、+2.0）
BAGU_KEYWORDS = [
    "ブリンカーを", "ブリンカー着", "ブリンカーに", "ブリンカーから",
    "チークＰを外", "チークから", "チークＰに変",
    "遮眼革", "シャドーロール",
    "メンコを外", "メンコを着", "メンコを変",
    "耳覆いを外",
]

# ③ 一変・変わり身（+2.0）
IPPEN_KEYWORDS = [
    "一変", "変わり身", "様変わり", "大きく変わ", "変わってほしい",
    "変貌", "一皮むけ",
]

# ④ 距離/コース/芝ダ転換（+1.5）
JOUKEN_KEYWORDS = [
    "距離短縮", "距離延長", "距離を延ばし", "距離を短く",
    "芝に変わ", "芝から", "ダートに変わ", "ダートから", "初芝", "初ダート",
    "コース替わり", "コースが変わ", "コースは変わ",
    "左回りが合", "左回りは合", "左回りは得意", "左回りで",
    "右回りが合", "右回りは合",
    "外回りで", "外回りの方", "外回りは",
    "マイルは合", "マイルが合", "マイルなら",
    "短い距離", "長い距離",
]

# ⑤ 装具微調整（+0.5）
BIMICHOUSEI_KEYWORDS = [
    "メンコ", "チークＰ", "チークピース",
    "鼻革", "舌縛り", "シャドーロール",
]


def calc_gekisou(horse: dict) -> tuple[float, list[str]]:
    """
    激走スコアと根拠リストを返す。
    対象: pickMark == "" の馬のみ呼ばれること前提
    """
    danwa = horse.get("danwaComment", "") or ""
    syoin = horse.get("syoinComment", "") or ""
    combined = danwa + " " + syoin

    score = 0.0
    reasons = []

    # ① 初ブリンカー
    if horse.get("hatsuBri") == 1:
        score += 3.0
        reasons.append("⚡初ブリ(+3.0)")

    # ② 馬具変更（初ブリでない場合のみ加点、重複防止）
    elif any(kw in combined for kw in BAGU_KEYWORDS):
        score += 2.0
        hit = next(kw for kw in BAGU_KEYWORDS if kw in combined)
        reasons.append(f"🔧馬具変更[{hit}](+2.0)")

    # ③ 一変・変わり身
    for kw in IPPEN_KEYWORDS:
        if kw in combined:
            score += 2.0
            reasons.append(f"🌀一変[{kw}](+2.0)")
            break  # 1回のみ

    # ④ 条件転換
    hit_jouken = []
    for kw in JOUKEN_KEYWORDS:
        if kw in combined:
            hit_jouken.append(kw)
    if hit_jouken:
        score += 1.5
        reasons.append(f"🔄条件変更{hit_jouken[:2]}(+1.5)")

    # ⑤ 装具微調整（②で加点済みの馬は対象外）
    if not any(kw in combined for kw in BAGU_KEYWORDS) and horse.get("hatsuBri") != 1:
        for kw in BIMICHOUSEI_KEYWORDS:
            if kw in combined:
                score += 0.5
                reasons.append(f"🔩装具微調[{kw}](+0.5)")
                break

    # ⑥ 玄武スコア補正
    genbu = horse.get("genbuScore", 0.0) or 0.0
    if genbu > 0:
        g_bonus = round(genbu * 0.4, 2)
        score += g_bonus
        reasons.append(f"🐢玄武×0.4(+{g_bonus:.2f})")

    # ⑦ 高言霊ボーナス（非ピックでkotodamaScore≥7.0）
    koto = horse.get("kotodamaScore", 0.0) or 0.0
    if koto >= 7.0:
        score += 0.5
        reasons.append(f"🐉高言霊{koto:.1f}(+0.5)")

    return round(score, 3), reasons


def process_roster(venue: str, path: Path):
    with open(path, encoding="utf-8") as f:
        roster = json.load(f)

    # cols 追記
    for col in ["gekisouScore", "gekisouMark", "gekisouNote"]:
        if col not in roster["cols"]:
            roster["cols"].append(col)

    race_summaries = []

    for race in roster["races"]:
        horses = race["horses"]

        # 初期化
        for h in horses:
            h["gekisouScore"] = 0.0
            h["gekisouMark"]  = ""
            h["gekisouNote"]  = ""

        # 非ピック馬だけ採点
        candidates = [h for h in horses if not h.get("pickMark")]

        if not candidates:
            race_summaries.append((race["raceNum"], race.get("raceName", ""), None, 0.0, []))
            continue

        scored = []
        for h in candidates:
            sc, reasons = calc_gekisou(h)
            h["gekisouScore"] = sc
            h["gekisouNote"]  = " | ".join(reasons) if reasons else "シグナルなし"
            scored.append((h, sc))

        # スコア降順ソート（同点: genbu → kotodama → 馬番）
        scored.sort(key=lambda x: (
            -x[1],
            -x[0].get("genbuScore", 0),
            -x[0].get("kotodamaScore", 0),
            x[0].get("num", 99),
        ))

        winner_horse, winner_score = scored[0]
        winner_horse["gekisouMark"] = "激"

        race_summaries.append((
            race["raceNum"],
            race.get("raceName", ""),
            winner_horse,
            winner_score,
            winner_horse["gekisouNote"].split(" | "),
        ))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)

    return roster, race_summaries


def print_venue_picks(venue: str, roster: dict, summaries: list):
    print(f"\n{'='*72}")
    print(f"  ⚡ 激走ピック — {venue}  {roster['date']}")
    print(f"{'='*72}")
    for rn, rname, horse, score, reasons in summaries:
        if horse is None:
            print(f"  {rn:>2}R {rname[:8]:<8} (候補なし)")
            continue
        mark_str = "初ブリ" if horse.get("hatsuBri") == 1 else ""
        print(
            f"  {rn:>2}R {rname[:8]:<8} 激{horse['name']}({horse.get('jockey','?')}) "
            f"G={score:.2f}  [{' / '.join(reasons[:3])}]"
        )


# ──────────────────────────────────────────────
if __name__ == "__main__":
    grand = 0
    for venue, path in ROSTER_FILES.items():
        if not path.exists():
            print(f"⚠ ファイルなし: {path}")
            continue
        roster, summaries = process_roster(venue, path)
        print_venue_picks(venue, roster, summaries)
        total = sum(len(r["horses"]) for r in roster["races"])
        picks = sum(1 for r in roster["races"] for h in r["horses"] if h.get("gekisouMark") == "激")
        grand += total
        print(f"  → {path.name} 保存完了（激走印{picks}頭 / 全{total}頭）")

    print(f"\n✅ 全36R 激走ピック完了（計{grand//total if grand else 0}×36R = 36頭）")
