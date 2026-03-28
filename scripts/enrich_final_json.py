#!/usr/bin/env python3
"""
enrich_final_json.py
--------------------
重賞展望CSV + HTMLから騎手・厩舎・外厩名・前走情報・父名を抽出し
final-*.json の各馬データへ自動注入するスクリプト。

CSV命名規則: docs/{date}-{race}.csv
HTML命名規則: docs/{date}-{race}.html
JSON命名規則: docs/data/final-{race}-{date}.json

使い方:
  python3 scripts/enrich_final_json.py
"""

import json, csv, re
from pathlib import Path

BASE = Path(__file__).parent.parent / "docs"
DATA = BASE / "data"

# ── 手動マッピング（JSONファイル名 → HTMLファイル名, CSVファイル名）──────
# 自動マッチングが効かない場合（日付やレース名が異なる）に記述する
MANUAL_MAP = {
    "final-nikkeisho-2026-03-28": {
        "html": "2026-03-29-nikkei-sho.html",
        "csv":  None,
    },
}

# ── ヘルパー ────────────────────────────────────────────

def clean_trainer(raw: str) -> str:
    """'栗東・橋口慎介厩舎' → '橋口慎介'"""
    if not raw:
        return ""
    s = re.sub(r"^(栗東|美浦|地方)[・・]", "", raw.strip())
    s = re.sub(r"厩舎$", "", s)
    return s.strip()

def clean_last_race(raw: str) -> str:
    """'阪神C G2 2着　ルメール騎手' → '阪神C G2 2着'"""
    if not raw:
        return ""
    s = re.split(r"[　\u3000]", raw.strip())[0]
    return s.strip()

def normalize_name(name: str) -> str:
    return name.strip().replace("\u3000", "").replace(" ", "")

def find_source_for_json(json_path: Path):
    """
    final-takamatsunomiya-kinen-2026-03-29.json
    → (2026-03-29-takamatsunomiya-kinen.csv, 2026-03-29-takamatsunomiya-kinen.html)
    手動マッピング(MANUAL_MAP)が優先される。
    """
    stem = json_path.stem

    # 手動マッピング優先
    if stem in MANUAL_MAP:
        manual = MANUAL_MAP[stem]
        csv_path  = BASE / manual["csv"]  if manual.get("csv")  else None
        html_path = BASE / manual["html"] if manual.get("html") else None
        return (
            csv_path  if csv_path  and csv_path.exists()  else None,
            html_path if html_path and html_path.exists() else None,
        )

    # 自動マッピング
    m = re.search(r"(\d{4}-\d{2}-\d{2})$", stem)
    if not m:
        return None, None
    date = m.group(1)
    race = re.sub(r"^final-", "", stem[: m.start()]).strip("-")
    csv_path  = BASE / f"{date}-{race}.csv"
    html_path = BASE / f"{date}-{race}.html"
    return (
        csv_path  if csv_path.exists()  else None,
        html_path if html_path.exists() else None,
    )

# ── CSV 読み込み ─────────────────────────────────────────

def load_csv(csv_path: Path) -> dict:
    """馬名 → 行データ の辞書を返す"""
    horses = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize_name(row.get("馬名", ""))
            if name:
                horses[name] = row
    return horses

# ── HTML から父名を抽出 ───────────────────────────────────

def load_sire_from_html(html_path: Path) -> dict:
    """
    重賞展望HTMLを解析し 馬名 → 父名 の辞書を返す。
    構造例:
      <h2 ...>パンジャタワー</h2>
      ...
      <span ...>父 タワーオブロンドン</span>
    """
    text = html_path.read_text(encoding="utf-8")

    # <h2> タグで馬名を含むブロックに分割
    # 各ブロック: h2の馬名 + 直後の数百文字
    sire_map = {}

    # h2タグの馬名と位置を全取得（改行含む複数行対応）
    h2_matches = list(re.finditer(
        r'<h2[^>]*class="[^"]*serif[^"]*"[^>]*>([\s\S]*?)</h2>',
        text
    ))

    for i, m in enumerate(h2_matches):
        # spanタグ等を除去 → 空白除去 → 先頭の馬番数字を除去
        raw = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        raw = re.sub(r'^\d+\s*', '', raw)  # 先頭の馬番数字を除去
        horse_name = normalize_name(raw)
        # このh2から次のh2までのブロック（最大1500文字）を切り取る
        start = m.start()
        end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else start + 1500
        block = text[start:end]

        # 「父 XXXX」パターンを検索（spanタグ内）
        sire_m = re.search(r'>父\s+([^<]+)<', block)
        if sire_m:
            sire = sire_m.group(1).strip()
            if sire:
                sire_map[horse_name] = sire

    return sire_map

# ── JSON 補完 ────────────────────────────────────────────

def enrich_json(json_path: Path, csv_data: dict, sire_map: dict) -> int:
    """JSONの各馬をCSV＋HTMLで補完し保存。変更した馬数を返す。"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for horse in data.get("horses", []):
        name = normalize_name(horse.get("name", ""))
        row  = csv_data.get(name, {})
        changed = False

        if not row and not sire_map.get(name):
            print(f"  ⚠️  未マッチ: {name}")
            continue

        # 騎手
        jockey = row.get("騎手", "").strip()
        if jockey and not horse.get("jockey"):
            horse["jockey"] = jockey
            changed = True

        # 厩舎
        trainer = clean_trainer(row.get("厩舎", ""))
        if trainer and not horse.get("trainer"):
            horse["trainer"] = trainer
            changed = True

        # 外厩
        gaiku = row.get("外厩名", "").strip()
        if gaiku and not horse.get("gaiku"):
            horse["gaiku"] = gaiku
            changed = True

        # 前走
        last_race = clean_last_race(row.get("前走情報", ""))
        if last_race and not horse.get("lastRace"):
            horse["lastRace"] = last_race
            changed = True

        # 父名（HTMLから）
        sire = sire_map.get(name, "")
        if sire and not horse.get("sire"):
            horse["sire"] = sire
            changed = True

        if changed:
            updated += 1
            print(f"  ✅ {name}: 父={horse.get('sire','—')} 騎={horse.get('jockey','—')} 厩={horse.get('trainer','—')} 外厩={horse.get('gaiku','—')} 前走={horse.get('lastRace','—')}")

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

        csv_path, html_path = find_source_for_json(json_path)
        if not csv_path and not html_path:
            print(f"⏭️  ソースなし: {json_path.name}")
            continue

        print(f"\n📄 {json_path.name}")
        if csv_path:  print(f"   ← CSV : {csv_path.name}")
        if html_path: print(f"   ← HTML: {html_path.name}")

        csv_data = load_csv(csv_path) if csv_path else {}
        sire_map = load_sire_from_html(html_path) if html_path else {}

        n = enrich_json(json_path, csv_data, sire_map)
        total_updated += n
        print(f"  → {n} 頭更新")

    print(f"\n✨ 完了: 合計 {total_updated} 頭を更新しました")

if __name__ == "__main__":
    main()
