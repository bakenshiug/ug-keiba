#!/usr/bin/env python3
"""
2026-04-23: 青龍(言霊) grade 第2次微調整
  前走インタビュー+次走メモ採点(1次) に加え、
  【コースデータ × フォトパドック】の独自視点で重要な馬のみ再調整。

方針:
  新聞/フォトパドックは基本「厩舎の目気にしてネガ書かない」→ 単独加点せず、
  **前走コメント × コース血統適性 × フォトパドック仕上がり** の3軸一致時だけ動かす。
  特に「記者断定 S/A」でも「血統コース適性0%」は裏付け薄と判断して減点。

対象9頭のみ更新。他の馬は1次採点を維持。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE_NOTES_DIR = ROOT / "docs" / "data" / "race-notes"

MICRO = {
    "2026-04-25-tokyo-11r": {  # 青葉賞
        # リオンディーズ産駒×東京2400m = 0-0-0-3 = 3着内率0.0%
        # 記者「2400適性断定」もコース血統実績0は危険。A→Bに減点。
        "ノーブルサヴェージ": ("B", "記者断定も血統0%裏付け薄"),
    },
    "2026-04-26-kyoto-11r": {  # マイラーズC
        # ドレフォン産駒×京都マイル = 16.1% コース適性薄。A→B。
        "ウォーターリヒト": ("B", "記者高評価もコース血統16%"),
        # ファー産駒75%(小)+吉村厩舎37%+岩田望36% - 記者D弱気だが素材は揃う。D→C。
        "オフトレイル": ("C", "弱気も血統/騎手/厩舎全て◎"),
        # ヴィクトワールピサ産駒33%+前年覇者。C→B。
        "ロングラン": ("B", "前年覇者・血統33%の裏付け"),
        # リオンディーズ産駒33.8%+フォト絶好調。C→B。
        "ブエナオンダ": ("B", "フォト絶好+京都マイル33%"),
    },
    "2026-04-26-tokyo-11r": {  # フローラS
        # アルアイン産駒×東京2000m = 0-0-0-11 = 0.0%!!
        # レーン騎手68%で相殺してもコース血統0は重大。S→A。
        "ラフターラインズ": ("A", "能力高もコース血統0%慎重"),
        # 記者フォトも「マイラーの印象」と認定。B→C。
        "ラベルセーヌ": ("C", "記者もマイラー印象・距離疑問"),
        # フォト「器大きい・末の切れ非凡」+血統キズナ36%+記者A - 3軸一致でS昇格。
        "エンネ": ("S", "器大きい・血統36%・3軸一致"),
    },
}


def main():
    for stem, horses_micro in MICRO.items():
        path = RACE_NOTES_DIR / f"{stem}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        race_name = data.get("race", {}).get("name", stem)
        diffs = []
        for h in data["horses"]:
            name = h["name"]
            if name in horses_micro:
                new_grade, new_keyword = horses_micro[name]
                old = h.get("relComment", {}) or {}
                old_grade = old.get("grade")
                old_keyword = old.get("keyword")
                h["relComment"] = {"keyword": new_keyword, "grade": new_grade}
                diffs.append((name, old_grade, new_grade, old_keyword, new_keyword))

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n=== {race_name} ({stem}) - 微調整 ===")
        print(f"{'馬名':<18}{'旧G':<4}{'新G':<4}  {'旧keyword':<28}→  新keyword")
        print("-" * 110)
        for name, og, ng, ok, nk in diffs:
            print(f"{name:<16}  {og or '-':<3} {ng:<3}  {(ok or '-'):<26}→  {nk}")
        print(f"  微調整: {len(diffs)}頭")


if __name__ == "__main__":
    main()
