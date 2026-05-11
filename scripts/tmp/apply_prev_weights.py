#!/usr/bin/env python3
"""
JRDB txt-extracted/*.txt から前走馬体重を抽出して race-notes JSON に反映

対象3レース:
  - 青葉賞 (2026-04-25 東京11R)
  - フローラS (2026-04-26 東京11R)
  - マイラーズC (2026-04-26 京都11R)

処理内容:
  1. 各馬のtxtから前走体重を抽出
  2. race-notes JSONのhorses[].prevHorseWeight/prevHorseWeightDelta に反映
  3. 体重履歴全走もprevHorseWeightHistory配列で保持（任意）
"""
import re
import json
from pathlib import Path

BASE = Path("/Users/buntawakase/Desktop/ug-keiba")

TARGETS = [
    {
        "name": "青葉賞",
        "txt_dir": BASE / "analysis/2026-04-25-aobasho/txt-extracted",
        "notes_path": BASE / "docs/data/race-notes/2026-04-25-tokyo-11r.json",
    },
    {
        "name": "フローラS",
        "txt_dir": BASE / "analysis/2026-04-26-floras/txt-extracted",
        "notes_path": BASE / "docs/data/race-notes/2026-04-26-tokyo-11r.json",
    },
    {
        "name": "マイラーズC",
        "txt_dir": BASE / "analysis/2026-04-26-milers-c/txt-extracted",
        "notes_path": BASE / "docs/data/race-notes/2026-04-26-kyoto-11r.json",
    },
]

# 体重3桁(380-580) + 増減(-99〜+99 or --) + 漢字1文字
WEIGHT_PAT = re.compile(r'(?<![\d.])(\d{3})\s+(-?\d{1,2}|--)\s+([\u4E00-\u9FFF])', re.MULTILINE)


def extract_weights(txt_path):
    """txtから過去走の体重リストを抽出（新しい順）"""
    content = txt_path.read_text(encoding='utf-8')
    weights = []
    seen_positions = set()
    for m in WEIGHT_PAT.finditer(content):
        w = int(m.group(1))
        if 380 <= w <= 580:
            if m.start() in seen_positions:
                continue
            seen_positions.add(m.start())
            delta = None if m.group(2) == '--' else int(m.group(2))
            weights.append({'weight': w, 'delta': delta})
    return weights


def process(target):
    name = target["name"]
    txt_dir = target["txt_dir"]
    notes_path = target["notes_path"]

    print(f"\n━━━ {name} ━━━")

    # race-notes JSON 読み込み
    notes = json.loads(notes_path.read_text(encoding='utf-8'))

    # 馬ごとに体重を反映
    hit = 0
    miss = []
    for horse in notes["horses"]:
        hname = horse["name"]
        txt_file = txt_dir / f"{hname}.txt"

        if not txt_file.exists():
            miss.append(hname)
            continue

        weights = extract_weights(txt_file)
        if not weights:
            miss.append(f"{hname}(データ無し)")
            continue

        prev = weights[0]
        horse["prevHorseWeight"] = prev["weight"]
        horse["prevHorseWeightDelta"] = prev["delta"]
        horse["prevHorseWeightHistory"] = weights  # 全走履歴も保持

        small_flag = "🔴小柄" if prev["weight"] <= 420 else ("⚠ボーダー" if prev["weight"] <= 430 else "")
        delta_str = f"{prev['delta']:+d}" if prev["delta"] is not None else "—"
        print(f"  {hname:20s} 前走:{prev['weight']}kg({delta_str}) {small_flag}")
        hit += 1

    # 書き戻し
    notes_path.write_text(
        json.dumps(notes, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(f"\n  → {hit}頭反映 / {len(miss)}頭ミス: {miss}")
    print(f"  → 保存: {notes_path.relative_to(BASE)}")


def main():
    for t in TARGETS:
        process(t)
    print("\n✅ 完了")


if __name__ == "__main__":
    main()
