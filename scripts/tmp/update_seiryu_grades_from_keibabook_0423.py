#!/usr/bin/env python3
"""
2026-04-23: 競馬ブック「前走インタビュー＋次走へのメモ」全頭読破から
青龍(relComment) grade再採点→ race-notes JSON に投入。

採点ルール:
  - 前走gradeは騎手/関係者コメントの断定度 (S=断定/A=明確期待/B=前向き/C=感触/D=弱気)
  - 次走メモgrade は記者観戦コメントのキーワード
     S: 快勝/完勝/断然
     A: メドが立った/本番楽しみ/上のクラスでもやれる
     B: 悪くない/渋太く追い上げ
     C: 進展あり/感触良好
     D: 見切り/不振
  - 総合 = 両軸の平均寄り
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE_NOTES_DIR = ROOT / "docs" / "data" / "race-notes"

# {file_stem: {horse_name: (grade, keyword)}}
UPDATES = {
    "2026-04-25-tokyo-11r": {  # 青葉賞
        "アッカン": ("C", "進展あるも敗因気掛り"),
        "カットソロ": ("B", "メド立つ"),
        "ケントン": ("A", "押し切り快勝"),
        "コスモギガンティア": ("B", "嵌まり待ち"),
        "ゴーイントゥスカイ": ("B", "絞れれば変わる"),
        "サガルマータ": ("A", "立て直し奏功"),
        "シャドウマスター": ("A", "長距離で良さ出た"),
        "タイダルロック": ("D", "器用さ一瞬欠く"),
        "テルヒコウ": ("A", "状態パーフェクト"),
        # トゥーナスタディ: 地方馬データなし・スキップ
        "ノチェセラーダ": ("B", "力は示した"),
        "ノーブルサヴェージ": ("A", "2400適性断定"),
        "パラディオン": ("C", "14着で勉強"),
        # ヒシアムルーズ: コメント無・スキップ
        "ブラックオリンピア": ("A", "長距離向き成長"),
        "ミッキーファルコン": ("A", "楽に差し切る"),
        "ヨカオウ": ("D", "道悪マイナス"),
        "ラストスマイル": ("C", "舞台替えも伸び負け"),
    },
    "2026-04-26-kyoto-11r": {  # マイラーズC
        # アサヒ: コメント無・スキップ
        "アドマイヤズーム": ("B", "敗因明確も伸び欠く"),
        "ウォーターリヒト": ("A", "凄くいい雰囲気・接触不利"),
        "エルトンバローズ": ("D", "本調子にない"),
        "オフトレイル": ("D", "1400ベスト自認"),
        "キョウエイブリッサ": ("C", "切れ脚欠く"),
        "クルゼイロドスル": ("C", "間に合わず"),
        "シックスペンス": ("D", "ムラな面"),
        "シャンパンカラー": ("D", "中途半端"),
        "ショウナンアデイブ": ("B", "走る気持ち戻る"),
        "ドラゴンブースト": ("A", "収穫多き快勝"),
        "ファインライン": ("A", "今日は鮮やか"),
        "ファーヴェント": ("A", "力つけてきた"),
        "ブエナオンダ": ("C", "噛み合わず"),
        "ベラジオボンド": ("S", "重賞十分・強くなる余地"),
        "マテンロウスカイ": ("D", "芝も選択肢(弱気)"),
        "ランスオブカオス": ("D", "イレ込みで失速"),
        "ロングラン": ("C", "芝戻り感触のみ"),
    },
    "2026-04-26-tokyo-11r": {  # フローラS
        "エイシンウィスパー": ("A", "上のクラスでやれる"),
        "エンネ": ("A", "鮮やか抜出・楽しみ"),
        "コウギョク": ("C", "キャリア/距離不足"),
        "ゴバド": ("D", "これからのレース希望"),
        "サムシングスイート": ("B", "位置取り奏功"),
        "スタニングレディ": ("B", "渋太く粘って"),
        "ファムクラジューズ": ("A", "タフでファイト心"),
        "ペイシャシス": ("A", "センス有・差し切る"),
        "ペンダント": ("B", "昇級戦で結果"),
        "ラフターラインズ": ("S", "能力相当高・牝馬同士なら"),
        "ラベルセーヌ": ("B", "なかなかの芸当"),
        "リアライズルミナス": ("B", "僅かに競り勝つ"),
        "リスレジャンデール": ("D", "切れる脚使えず"),
    },
}


def main():
    for stem, horses_updates in UPDATES.items():
        path = RACE_NOTES_DIR / f"{stem}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        diffs = []
        race_name = data.get("race", {}).get("name", stem)
        for h in data["horses"]:
            name = h["name"]
            if name in horses_updates:
                new_grade, new_keyword = horses_updates[name]
                old = h.get("relComment", {}) or {}
                old_grade = old.get("grade")
                old_keyword = old.get("keyword")
                h["relComment"] = {"keyword": new_keyword, "grade": new_grade}
                change_flag = "★" if old_grade != new_grade else "  "
                diffs.append((name, old_grade, new_grade, old_keyword, new_keyword, change_flag))

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n=== {race_name} ({stem}) ===")
        print(f"{'馬名':<22}{'旧G':<4}{'新G':<4}差  {'旧keyword':<26}→  新keyword")
        print("-" * 120)
        for name, og, ng, ok, nk, flag in diffs:
            print(f"{name:<20}  {og or '-':<3} {ng:<3} {flag}  {(ok or '-'):<24}→  {nk}")
        print(f"  更新: {len(diffs)}頭")


if __name__ == "__main__":
    main()
