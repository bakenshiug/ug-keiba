#!/usr/bin/env python3
"""
2026-04-24: フローラS 玄武（外厩）情報を最新JRDBデータで更新。
ニック提供情報: ラフターラインズ・ラベルセーヌ・リスレジャンデール の3頭が
ノーザンファーム天栄 仕上げ → gaikyuFactor grade A に昇格。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "docs" / "data" / "race-notes" / "2026-04-26-tokyo-11r.json"

# 3頭とも同じ：ノーザンF天栄 / A級
UPDATES = {
    "ラフターラインズ": {
        "gaikyu": "ノーザンファーム天栄",
        "gaikyuFactor": {
            "grade": "A",
            "source": "individual",
            "canonical": "ノーザンF天栄",
            "shutubaGaikyu": "ノーザンファーム天栄",
        },
    },
    "ラベルセーヌ": {
        "gaikyu": "ノーザンファーム天栄",
        "gaikyuFactor": {
            "grade": "A",
            "source": "individual",
            "canonical": "ノーザンF天栄",
            "shutubaGaikyu": "ノーザンファーム天栄",
        },
    },
    "リスレジャンデール": {
        "gaikyu": "ノーザンファーム天栄",
        "gaikyuFactor": {
            "grade": "A",
            "source": "individual",
            "canonical": "ノーザンF天栄",
            "shutubaGaikyu": "ノーザンファーム天栄",
        },
    },
}


def main():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    diffs = []
    for h in data["horses"]:
        name = h["name"]
        if name in UPDATES:
            up = UPDATES[name]
            old_gaikyu = h.get("gaikyu")
            old_factor = h.get("gaikyuFactor") or {}
            old_grade = old_factor.get("grade")
            h["gaikyu"] = up["gaikyu"]
            h["gaikyuFactor"] = up["gaikyuFactor"]
            diffs.append((name, old_gaikyu, up["gaikyu"], old_grade, up["gaikyuFactor"]["grade"]))

    PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"=== フローラS 玄武情報更新 ===")
    print(f"{'馬名':<20}{'旧外厩':<16}→ {'新外厩':<20}  {'旧G':<4}→ 新G")
    print("-" * 90)
    for name, og, ng, ogr, ngr in diffs:
        print(f"{name:<18}  {og:<14}→ {ng:<18}  {ogr or '-':<3}→ {ngr}")
    print(f"\n更新: {len(diffs)}頭")


if __name__ == "__main__":
    main()
