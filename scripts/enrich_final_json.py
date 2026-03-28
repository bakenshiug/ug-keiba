#!/usr/bin/env python3
"""
enrich_final_json.py
--------------------
重賞展望CSVから騎手・厩舎・外厩名・前走情報を抽出し
final-*.json の各馬データへ自動注入するスクリプト。

CSV命名規則: docs/{date}-{race}.csv
JSON命名規則: docs/data/final-{race}-{date}.json

使い方:
  python3 scripts/enrich_final_json.py
"""

import json, csv, re, os, glob
from pathlib import Path

BASE = Path(__file__).parent.parent / "docs"
DATA = BASE / "data"

# ── ヘルパー ────────────────────────────────────────────

def clean_trainer(raw: str) -> str:
    """'栗東・橋口慎介厩舎' → '橋口慎介'"""
    if not raw:
        return ""
    s = re.sub(r"^(栗東|美浦|地方)[・・]", "", raw.strip())
    s = re.sub(r"厩舎$", "", s)
    return s.strip()

def clean_last_race(raw: str) -> str:
    """'阪神C G2 2着\u3000ルメール騎手' → '阪神C G2 2着'"""
    if not raw:
        return ""
    # 全角スペース or '　' 以降のジョッキー情報を除去
    s = re.split(r"[　\u3000]", raw.strip())[0]
    return s.strip()

def normalize_name(name: str) -> str:
    return name.strip().replace("\u3000", "").replace(" ", "")

def find_csv_for_json(json_path: Path):
    """
    final-takamatsunomiya-kinen-2026-03-29.json
    → docs/2026-03-29-takamatsunomiya-kinen.csv
    """
    stem = json_path.stem  # e.g. final-takamatsunomiya-kinen-2026-03-29
    # 末尾の日付部分を抽出
    m = re.search(r"(\d{4}-\d{2}-\d{2})$", stem)
    if not m:
        return None
    date = m.group(1)
    race = re.sub(r"^final-", "", stem[: m.start()]).strip("-")
    csv_path = BASE / f"{date}-{race}.csv"
    return csv_path if csv_path.exists() else None

def load_csv(csv_path: Path) -> dict[str, dict]:
    """馬名 → 行データ の辞書を返す"""
    horses = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize_name(row.get("馬名", ""))
            if name:
                horses[name] = row
    return horses

def enrich_json(json_path: Path, csv_data: dict[str, dict]) -> int:
    """JSONの各馬をCSVで補完し保存。変更した馬数を返す。"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for horse in data.get("horses", []):
        name = normalize_name(horse.get("name", ""))
        row = csv_data.get(name)
        if not row:
            print(f"  ⚠️  CSV未マッチ: {name}")
            continue

        changed = False

        # 騎手
        jockey = row.get("騎手", "").strip()
        if jockey and not horse.get("jockey"):
            horse["jockey"] = jockey
            changed = True

        # 厩舎
        trainer_raw = row.get("厩舎", "").strip()
        trainer = clean_trainer(trainer_raw)
        if trainer and not horse.get("trainer"):
            horse["trainer"] = trainer
            changed = True

        # 外厩
        gaiku = row.get("外厩名", "").strip()
        if gaiku and not horse.get("gaiku"):
            horse["gaiku"] = gaiku
            changed = True

        # 前走
        last_race_raw = row.get("前走情報", "").strip()
        last_race = clean_last_race(last_race_raw)
        if last_race and not horse.get("lastRace"):
            horse["lastRace"] = last_race
            changed = True

        if changed:
            updated += 1
            print(f"  ✅ {name}: jockey={horse.get('jockey')} trainer={horse.get('trainer')} gaiku={horse.get('gaiku')} lastRace={horse.get('lastRace')}")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated

# ── メイン ──────────────────────────────────────────────

def main():
    json_files = sorted(DATA.glob("final-*.json"))
    if not json_files:
        print("final-*.json が見つかりません")
        return

    total_updated = 0
    for json_path in json_files:
        if json_path.name in ("final-list.json", "final-history.json"):
            continue
        csv_path = find_csv_for_json(json_path)
        if not csv_path:
            print(f"⏭️  CSV なし: {json_path.name}")
            continue

        print(f"\n📄 {json_path.name} ← {csv_path.name}")
        csv_data = load_csv(csv_path)
        n = enrich_json(json_path, csv_data)
        total_updated += n
        print(f"  → {n} 頭更新")

    print(f"\n✨ 完了: 合計 {total_updated} 頭を更新しました")

if __name__ == "__main__":
    main()
