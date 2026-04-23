#!/usr/bin/env python3
"""
2026-04-23: 青龍(言霊) grade 第2次微調整 (v2.1)
  前走インタビュー+次走メモ採点(1次) に加え、
  【コースデータ × 記者評価】の2軸一致で重要な馬のみ再調整。

方針 (v2.1):
  新聞は基本「厩舎の目気にしてネガ書かない」→ 単独加点せず、
  **前走コメント × コース血統/騎手/厩舎適性** の2軸一致時だけ動かす。
  特に「記者断定 S/A」でも「血統コース適性0%」は裏付け薄と判断して減点。

  PHOTOパドック (v2.0まで3軸目として使用) は**採点対象から除外**。
  理由: 体型評価(マイラー印象/小柄/胴詰まり等)は実戦距離適性と乖離することが多く、
       主観ノイズが大きいため (ラベルセーヌ事例で確認)。

対象馬のみ更新。他の馬は1次採点を維持。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RACE_NOTES_DIR = ROOT / "docs" / "data" / "race-notes"

MICRO = {
    "2026-04-25-tokyo-11r": {  # 青葉賞
        # リオンディーズ産駒×東京2400m = 0-0-0-3 = 3着内率0.0%
        # 記者「2400適性断定」もコース血統実績0は危険。A→Bに減点。
        "ノーブルサヴェージ": ("B", "メディア高評価も血統裏付け薄"),
    },
    "2026-04-26-kyoto-11r": {  # マイラーズC
        # ドレフォン産駒×京都マイル = 16.1% コース適性薄。A→B。
        "ウォーターリヒト": ("B", "メディア高評価もコース適性薄"),
        # ファー産駒75%(小)+吉村厩舎37%+岩田望36% - 記者D弱気だが素材は揃う。D→C。
        "オフトレイル": ("C", "弱気も血統/騎手/厩舎全て◎"),
        # ヴィクトワールピサ産駒33%+前年覇者。C→B。
        "ロングラン": ("B", "前年覇者・血統33%の裏付け"),
        # リオンディーズ産駒33.8% コース適性◎。C→B。(v2.1: フォト根拠削除)
        "ブエナオンダ": ("B", "京都マイル血統33%の裏付け"),
    },
    "2026-04-26-tokyo-11r": {  # フローラS
        # アルアイン産駒×東京2000m = 0-0-0-11 = 0.0%!!
        # レーン騎手68%で相殺してもコース血統0は重大。S→A。
        "ラフターラインズ": ("A", "能力高もコース血統0%慎重"),
        # v2.1: PHOTOパドック根拠削除 → 記者評価「突き放した・経験馬相手に芸当」A級に復元。
        # 前走コメント荻野極「素質高・走り切り」A +
        # 次走メモ「経験馬相手に芸当」A〜S +
        # キズナ産駒×東京2000mのコースデータ要検証 → A昇格が妥当。
        "ラベルセーヌ": ("A", "突き放した完勝"),
        # v2.1: フォト根拠削除 → キズナ産駒×東京2000m = 36% + 記者A評価の2軸一致でS昇格維持。
        "エンネ": ("S", "血統36%・媒体高評価・2軸一致"),
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
