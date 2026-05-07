#!/usr/bin/env python3
"""
export_note_text.py
kotodama-test JSON → NOTE貼付用Markdownテキスト生成

Usage:
    python3 scripts/export_note_text.py 2026-05-10
    python3 scripts/export_note_text.py 2026-05-10 --venue 東京
    python3 scripts/export_note_text.py 2026-05-10 --free 1-3   # 1-3R無料表示
"""
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data" / "kotodama-test"
OUT_DIR = ROOT / "scripts" / "out_note"
OUT_DIR.mkdir(exist_ok=True)


def fmt_race_block(r, free=False):
    """レース1つ分のMarkdownブロック生成"""
    lines = []
    surface_jp = "芝" if r.get("surface") == "芝" else "ダ"
    head = f"## 【{r['raceNum']}】{r['raceName']}　{surface_jp}{r['distance']}m　{r['numHorses']}頭　発走 {r['startTime']}"
    lines.append(head)
    lines.append("")

    if free:
        lines.append("🆓 **無料公開レース**")
        lines.append("")

    # picks 4頭
    picks = r.get("picks", [])
    if not picks:
        lines.append("（picks未設定）")
        lines.append("")
        return "\n".join(lines)

    lines.append("### 神宮の見立て")
    for p in picks:
        mark = p.get("mark", "")
        num = p.get("num", "")
        name = p.get("name", "")
        jockey = p.get("jockey", "")
        grade = p.get("kotodamaGrade", "")
        lines.append(f"- {mark} **{num}番 {name}**（{jockey}／言霊{grade}）")
    lines.append("")

    # コメント（◎のみ詳細）
    if picks and picks[0].get("comment"):
        lines.append(f"**◎ 神宮メモ**：{picks[0]['comment']}")
        lines.append("")

    # 推奨買い目
    axis_num = picks[0].get("num") if picks else "-"
    aite_nums = [str(p.get("num")) for p in picks[1:4]]
    aite_str = "・".join(aite_nums)

    lines.append("### 📌 推奨買い目（予算でアレンジOK）")
    lines.append(f"- 単勝　{axis_num}　1点")
    lines.append(f"- 馬連　◎{axis_num}軸1頭流し（{aite_str}）　3点")
    lines.append(f"- 馬単　◎{axis_num}軸1頭マルチ（{aite_str}）　6点")
    lines.append(f"- 3連複　◎{axis_num}軸1頭流し（{aite_str}）　3点")
    lines.append(f"- 3連単　◎{axis_num}軸1頭マルチ（{aite_str}）　24点")
    lines.append("")

    # 致命ワードがあれば記載
    fatals = r.get("fatalWords", [])
    if fatals:
        lines.append("⚠ **致命ワード検出**")
        for fw in fatals:
            lines.append(f"- {fw['horse']}：「{fw['word']}」（{fw.get('type','')}）")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def fmt_venue_pack(date, venue, races, campaign_price=200):
    """1場分のNOTE記事Markdown生成"""
    lines = []
    lines.append(f"# 神宮 {date} {venue}競馬場パック（全12R）")
    lines.append("")
    lines.append(f"⛩ UG競馬神宮の{date}・{venue}全12R予想パックです。")
    lines.append("")
    lines.append(f"🎉 **ローンチキャンペーン：¥{campaign_price}**（通常価格 ¥800 → 75%OFF）")
    lines.append("")
    lines.append("## 📋 本パックの構成")
    lines.append("- 全12R picks（◎○▲△）")
    lines.append("- 各レース言霊grade付")
    lines.append("- 推奨買い目（5券種・予算でアレンジOK）")
    lines.append("- 致命ワード検出馬リスト")
    lines.append("- サイト落ち時バックアップテキスト同梱")
    lines.append("")
    lines.append("📺 **結果速報は X で随時更新**")
    lines.append("→ @acekeiba_gaikyu をフォロー")
    lines.append("")
    lines.append("⚠ 予想であり結果を保証するものではありません。返金は原則不可（サイト障害時のみ別対応）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1-3R無料 / 4-12R有料の境界明示
    lines.append("# 🆓 無料エリア（1〜3R）")
    lines.append("")
    for r in races:
        rn = r["raceNum"]
        if rn in ["1R", "2R", "3R"]:
            lines.append(fmt_race_block(r, free=True))

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 🔒 有料エリア（4〜12R）")
    lines.append("")
    lines.append(f"※ ここから先は ¥{campaign_price} 購入でご覧いただけます")
    lines.append("")
    for r in races:
        rn = r["raceNum"]
        if rn not in ["1R", "2R", "3R"]:
            lines.append(fmt_race_block(r, free=False))

    lines.append("---")
    lines.append("")
    lines.append("# 🎁 限定URL（おまけ・サイト版）")
    lines.append("")
    lines.append("ブラウザで読みやすい色付きHTML版もご用意しています。")
    lines.append("→ https://bakenshiug.github.io/ug-keiba/sunday-{HASH}.html")
    lines.append("（毎週URL変更）")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 📺 結果速報")
    lines.append("")
    lines.append("リアルタイム結果は X で更新します（NOTE記事は予想公開時点を保持）")
    lines.append("→ @acekeiba_gaikyu")
    lines.append("")
    lines.append("ご購入ありがとうございます⛩💚")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("--venue", help="場名指定（東京/京都/新潟）", default=None)
    parser.add_argument("--price", type=int, default=200, help="キャンペーン価格")
    args = parser.parse_args()

    src = DATA_DIR / f"{args.date}.json"
    if not src.exists():
        print(f"❌ ファイル未存在: {src}", file=sys.stderr)
        sys.exit(1)

    data = json.load(open(src))
    races = data.get("races", [])

    # 場ごとにグループ化
    venues = {}
    for r in races:
        venues.setdefault(r["venue"], []).append(r)

    # raceNum順ソート
    for v in venues:
        venues[v].sort(key=lambda r: int(r["raceNum"].replace("R", "")))

    target_venues = [args.venue] if args.venue else list(venues.keys())

    for v in target_venues:
        if v not in venues:
            print(f"⚠ 場データなし: {v}", file=sys.stderr)
            continue
        md = fmt_venue_pack(args.date, v, venues[v], args.price)
        out = OUT_DIR / f"{args.date}_{v}.md"
        out.write_text(md, encoding="utf-8")
        print(f"✅ {out} ({len(md)}文字)")


if __name__ == "__main__":
    main()
