#!/usr/bin/env python3
"""
買い目作成 v1.0
◎/○/▲/激 の4印馬を抽出し、テキスト見解付きの買い目JSONを生成。
全頭スコアは roster.json から読むのみ（書き込みなし）。
出力: docs/data/kotodama-test/20260516_{venue}_kaime.json
"""

import json
import re
import sys as _sys
from pathlib import Path

_date = (_sys.argv[1] if len(_sys.argv) > 1 else "2026-05-17").replace("-", "")

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")
ROSTER_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_roster.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_roster.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_roster.json",
}
OUTPUT_FILES = {
    "東京": BASE / f"docs/data/kotodama-test/{_date}_tokyo_kaime.json",
    "京都": BASE / f"docs/data/kotodama-test/{_date}_kyoto_kaime.json",
    "新潟": BASE / f"docs/data/kotodama-test/{_date}_niigata_kaime.json",
}

# ──────────────────────────────────────────────
# コメント本文抽出
# ──────────────────────────────────────────────

def extract_danwa_body(danwa: str) -> str:
    """印 馬名【担当者】本文 → 本文を返す（師――/助手――形式も対応）"""
    if not danwa:
        return ""
    # SVG/CSSコードを除去（.st0{fill:none;...} 等）
    danwa = re.sub(r"\.[a-z]+\d*\{[^}]*\}", "", danwa)
    danwa = re.sub(r"<style[^>]*>.*?</style>", "", danwa, flags=re.DOTALL)
    danwa = danwa.strip()
    if not danwa:
        return ""
    # 【担当者】本文 形式
    m = re.search(r"】(.+)$", danwa, re.DOTALL)
    if m:
        return m.group(1).strip()
    # 師――/助手―― 形式: 「加藤征師――本文」「山崎助手――本文」
    m = re.search(r"[^\s]{1,8}(?:師|助手)――(.+)$", danwa, re.DOTALL)
    if m:
        return m.group(1).strip()
    # 【】なしの場合は先頭印・馬名を取り除く
    text = re.sub(r"^[◎○▲△]\S+\s*", "", danwa).strip()
    return text


def extract_syoin_body(syoin: str) -> str:
    """馬名（着順）騎手名 本文 → 本文を返す（最初の200文字）"""
    if not syoin:
        return ""
    # 「騎手名 本文」or「騎手名―― 本文」
    m = re.search(r"騎手\s*[\-－―]+?\s*(.+)$", syoin, re.DOTALL)
    if m:
        return m.group(1).strip()[:160]
    # フォールバック: （着順）の後
    m = re.search(r"（\S+）\S+?\s+(.+)$", syoin, re.DOTALL)
    if m:
        return m.group(1).strip()[:160]
    return ""


def extract_suzaku_context(note: str, score: float) -> str:
    """朱雀ノートからコース複勝率情報を抽出"""
    if score < 1.5 or not note:
        return ""
    m = re.search(r"([東京都|京都|新潟]\w{1,5}SH[\d.]+%\(n=\d+\))", note)
    if m:
        return "コース巧者騎手。"
    if score >= 2.0:
        return "鞍上の当舞台適性が数値で裏付けられている。"
    return ""


def extract_genbu_context(note: str, score: float, trend: str) -> str:
    """玄武ノートから厩舎・外厩情報を抽出"""
    if score < 1.5 or not note:
        return ""
    if "天栄" in note:
        return "天栄仕上げが示す上昇気配を見逃せない。"
    if "チャンピオンヒルズ" in note:
        return "チャンピオンヒルズ帰りの本気仕様が後押しする。"
    if trend == "🔥":
        return "厩舎の直近上昇トレンドも力強い追い風。"
    if "しがらき" in note:
        return "ノーザン系のしがらき仕上げで状態は信頼できる。"
    if score >= 2.0:
        return "厩舎・外厩の数値的裏付けが揃っている。"
    return ""


# ──────────────────────────────────────────────
# 見解テキスト生成
# ──────────────────────────────────────────────

MARK_CONCLUSION = {
    "◎": {
        "S": "総合評価のトップ。この舞台での主役はこの馬と見る。",
        "A": "陣営・数値ともに一致した本命評価。複勝軸として揺るがない。",
        "B": "複合シグナルが重なり本命推奨。好走の条件は揃っている。",
        "C": "他馬の弱点と相対評価で本命に浮上。展開鍵も一考の価値あり。",
        "D": "スコアは控えめながら騎手・外厩の上乗せで上位評価。",
    },
    "○": {
        "S": "本命と甲乙つけがたい実力馬。差のない一戦を期待。",
        "A": "軸馬に次ぐ信頼度。連軸として積極的に絡めたい。",
        "B": "バランスのとれた対抗評価。2・3着安定型として注目。",
        "C": "穴としての警戒馬。人気落ちでも見逃し厳禁。",
        "D": "低評価の中に潜む上昇シグナルに注目。",
    },
    "▲": {
        "S": "格上の3番手。上位崩れの際の巻き返しが怖い。",
        "A": "3着候補として堅実なシグナル。軸から流す相手筆頭。",
        "B": "差のある3番手だが無視できない要素あり。ヒモに加えたい。",
        "C": "条件次第で上位介入も。ひと工夫加えたい一頭。",
        "D": "人気薄の3番手候補。大穴として妙味あり。",
    },
    "激": {
        "S": "激走候補としてはやや想定外の高評価。人気次第では本命级。",
        "A": "変化の度合いが大きく、人気以上の激走に期待。",
        "B": "条件変化が最大の武器。ひと変わりあれば上位食い込みも。",
        "C": "シグナルは弱いが一発候補として一考。",
        "D": "大穴狙いの激走候補。信頼度より夢を買う。",
    },
}


def build_comment(horse: dict, mark: str) -> str:
    danwa_body = extract_danwa_body(horse.get("danwaComment", ""))
    syoin_body = extract_syoin_body(horse.get("syoinComment", ""))
    suzaku_ctx = extract_suzaku_context(
        horse.get("suzakuNote", ""),
        horse.get("suzakuScore", 0) or 0,
    )
    genbu_ctx = extract_genbu_context(
        horse.get("genbuNote", ""),
        horse.get("genbuScore", 0) or 0,
        horse.get("genbuTrend", ""),
    )
    hatsu_bri = horse.get("hatsuBri", 0)
    grade = horse.get("kotodamaGrade", "C")
    gekisou_note = horse.get("gekisouNote", "") or ""
    koto_score = horse.get("kotodamaScore", 0) or 0

    sentences = []

    # ─── メインコメント（danwa本文）───
    if danwa_body:
        body = danwa_body[:130].rstrip("。").rstrip("、")
        # 「助手」「師」などの表記を中立化（ソース特定を避ける）
        body = re.sub(r"【.+?】", "", body).strip()
        body = re.sub(r"　", " ", body)
        if body:
            sentences.append(body + "。")

    # ─── 激走: 変化シグナルを先頭に挿入 ───
    if mark == "激":
        if hatsu_bri:
            sentences.insert(0, "今回から装着する初ブリンカーで集中力の向上に期待。")
        elif "一変" in gekisou_note or "変わり身" in gekisou_note:
            sentences.insert(0, "陣営が語る変わり身が今回のテーマ。")
        elif "距離" in gekisou_note:
            sentences.insert(0, "距離条件の変化がプラスに転化できれば一変の余地あり。")
        elif "芝" in gekisou_note or "ダート" in gekisou_note:
            sentences.insert(0, "舞台替わりで新たな適性を引き出せるかが鍵。")

    # ─── 朱雀コンテキスト ───
    if suzaku_ctx:
        sentences.append(suzaku_ctx)

    # ─── 玄武コンテキスト ───
    if genbu_ctx:
        sentences.append(genbu_ctx)

    # ─── 騎手コメント（syoin）が有益なら追加 ───
    if syoin_body and len(sentences) < 2:
        snippet = syoin_body[:80].rstrip("。").rstrip("、")
        if snippet:
            sentences.append(f"前走後、騎手は「{snippet}」と手応えを語った。")

    # ─── 結論 ───
    conclusion = MARK_CONCLUSION.get(mark, {}).get(grade, "注目の一頭。")
    sentences.append(conclusion)

    # 最大3文に絞る
    return " ".join(sentences[:3])


# ──────────────────────────────────────────────
# 買い目JSON構築
# ──────────────────────────────────────────────

MARK_ORDER = {"◎": 0, "○": 1, "▲": 2, "激": 3}


def build_race_picks(race: dict) -> list[dict]:
    picks = []
    for h in race["horses"]:
        mark = h.get("pickMark", "")
        if not mark:
            # 激走印チェック
            if h.get("gekisouMark") == "激":
                mark = "激"
            else:
                continue

        pick = {
            "mark":          mark,
            "num":           h.get("num", ""),
            "name":          h.get("name", ""),
            "kotodamaGrade": h.get("kotodamaGrade", ""),
            "kotodamaScore": h.get("kotodamaScore", 0),
            "totalScore":    h.get("totalScore", 0),
            "gekisouScore":  h.get("gekisouScore", 0),
            "jockey":        h.get("jockey", ""),
            "trainer":       h.get("trainer", ""),
            "gaikyu":        h.get("gaikyu", ""),
            "hatsuBri":      h.get("hatsuBri", 0),
            "ninki":         None,   # 想定人気（後で追記）
            "chakujun":      None,   # 着順（結果反映後）
            "comment":       build_comment(h, mark),
        }
        picks.append(pick)

    # 印順ソート
    picks.sort(key=lambda p: MARK_ORDER.get(p["mark"], 9))
    return picks


def build_kaime_json(venue: str, roster: dict) -> dict:
    races = []
    for race in roster["races"]:
        picks = build_race_picks(race)
        races.append({
            "raceNum":  race["raceNum"],
            "raceName": race.get("raceName", ""),
            "picks":    picks,
        })
    return {
        "venue":       venue,
        "date":        roster.get("date", ""),
        "generatedAt": "2026-05-15",
        "markRule":    "◎本命/○対抗/▲3番手/激=穴激走候補",
        "scoreWeights": "totalScore=言霊×1.0+朱雀×0.5+玄武×0.3",
        "races":        races,
    }


# ──────────────────────────────────────────────
# メイン
# ──────────────────────────────────────────────

def print_kaime_summary(venue: str, kaime: dict):
    print(f"\n{'='*70}")
    print(f"  📋 買い目サマリー — {venue}  {kaime['date']}")
    print(f"{'='*70}")
    for race in kaime["races"]:
        print(f"\n  {race['raceNum']:>2}R {race['raceName'][:10]}")
        for p in race["picks"]:
            bri = "⚡" if p["hatsuBri"] else ""
            print(f"    {p['mark']} {p['num']:>2}番 {p['name']}{bri}"
                  f" [{p['kotodamaGrade']}] "
                  f"騎:{p['jockey']} 厩:{p['trainer']}")


if __name__ == "__main__":
    for venue, roster_path in ROSTER_FILES.items():
        if not roster_path.exists():
            print(f"⚠ ファイルなし: {roster_path}")
            continue

        with open(roster_path, encoding="utf-8") as f:
            roster = json.load(f)

        kaime = build_kaime_json(venue, roster)
        out_path = OUTPUT_FILES[venue]

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(kaime, f, ensure_ascii=False, indent=2)

        print_kaime_summary(venue, kaime)
        total_picks = sum(len(r["picks"]) for r in kaime["races"])
        print(f"\n  → {out_path.name} 保存完了（{len(kaime['races'])}R × 4印 = {total_picks}頭）")

    print("\n✅ 全36R 買い目JSON生成完了")
