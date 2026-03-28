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

def clean_trainer(raw):
    """'栗東・橋口慎介厩舎' → '橋口慎介'"""
    if not raw:
        return ""
    s = re.sub(r"^(栗東|美浦|地方)[・・]", "", raw.strip())
    s = re.sub(r"厩舎$", "", s)
    return s.strip()

def clean_last_race(raw):
    """'阪神C G2 2着　ルメール騎手' → '阪神C G2 2着'"""
    if not raw:
        return ""
    s = re.split(r"[　\u3000]", raw.strip())[0]
    return s.strip()

def normalize_name(name):
    return name.strip().replace("\u3000", "").replace(" ", "")

def find_source_for_json(json_path):
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

def load_csv(csv_path):
    """馬名 → 行データ の辞書を返す"""
    horses = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize_name(row.get("馬名", ""))
            if name:
                horses[name] = row
    return horses

# ── HTML から馬情報を総合抽出 ──────────────────────────────

def load_horse_data_from_html(html_path):
    """
    重賞展望HTMLを解析し 馬名 → {sire, trainer, gaiku, lastRace} の辞書を返す。

    対応HTML構造（2種）:
    【A型】mainichi-hai など: h2直後に前走・父・厩舎・外厩
      <h2>馬名</h2>
      <p>📍 前走：阪神芝1800m　1着</p>
      <span>父 XXX</span>
      <span>XXX厩舎 栗東</span>
      <span>🌿 外厩名</span> or <span>🏠 在厩</span>

    【B型】march-stakes / nikkei-sho など: h2直前に前走、h2直後に父・厩舎・外厩
      <p>📍 前走：レース名 着順　未定騎手</p>
      <h2><span>馬番</span>馬名</h2>
      <span>父 XXX</span>
      <span>XXX厩舎 美浦</span>
      <span>🌿 外厩名</span> or <span>🏠 在厩</span>
    """
    text = html_path.read_text(encoding="utf-8")
    horse_map = {}

    # h2タグの馬名と位置を全取得（改行含む複数行対応）
    h2_matches = list(re.finditer(
        r'<h2[^>]*class="[^"]*serif[^"]*"[^>]*>([\s\S]*?)</h2>',
        text
    ))

    for i, m in enumerate(h2_matches):
        # spanタグ等を除去 → 空白除去 → 先頭の馬番数字を除去
        raw = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        raw = re.sub(r'^\d+\s*', '', raw)
        horse_name = normalize_name(raw)
        if not horse_name:
            continue

        # ─ h2直後のブロック（次のh2まで、最大2000文字）
        after_start = m.end()
        after_end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else after_start + 2000
        after_block = text[after_start:after_end]

        # ─ h2直前のブロック（前のh2終端から今のh2先頭まで）
        before_start = h2_matches[i - 1].end() if i > 0 else 0
        before_block = text[before_start:m.start()]

        data = {}

        # ── 父名: after_block から
        sire_m = re.search(r'>父\s+([^<]+)<', after_block)
        if sire_m:
            sire = sire_m.group(1).strip()
            if sire:
                data['sire'] = sire

        # ── 厩舎: after_block の「XXX厩舎 美浦/栗東」span
        trainer_m = re.search(
            r'>([^\s<>]+)厩舎\s*(?:美浦|栗東|地方)[^<]*<',
            after_block
        )
        if trainer_m:
            data['trainer'] = trainer_m.group(1).strip()

        # ── 外厩: after_block の🌿(外厩あり) / 🏠在厩(外厩なし)
        gaiku_m = re.search(r'🌿\s*([^<]+)</span>', after_block)
        if gaiku_m:
            data['gaiku'] = gaiku_m.group(1).strip()
        elif re.search(r'🏠\s*在厩', after_block):
            data['gaiku'] = ''  # 在厩（外厩なし）を明示

        # ── 前走: after_block → before_block の順に検索
        #    「📍 前走：XX　XX着　XX騎手」→ 騎手部分を除去してクリーン
        def extract_last_race(block):
            # after_blockに複数ある場合は最初の1件（A型）、
            # before_blockに複数ある場合は最後の1件（B型・前の馬の前走を拾わないため）
            return re.findall(r'📍\s*前走[：:]\s*([^<\n]+)', block)

        lr_candidates = extract_last_race(after_block)
        if lr_candidates:
            lr_raw = lr_candidates[0]
        else:
            lr_candidates = extract_last_race(before_block)
            lr_raw = lr_candidates[-1] if lr_candidates else ""

        if lr_raw:
            # 「　未定騎手」「　ルメール騎手」などの騎手表記を除去
            lr = re.sub(r'[　\s]+[^\s　]*騎手.*$', '', lr_raw.strip())
            # 全角スペースで分かれた着順を結合（例:「阪神芝1800m　1着」→「阪神芝1800m 1着」）
            lr = re.sub(r'[　]+', ' ', lr).strip()
            # ※注釈（「※ダート→芝替わり」等）を除去
            lr = re.sub(r'\s*※.+$', '', lr).strip()
            if lr:
                data['lastRace'] = lr

        if data:
            horse_map[horse_name] = data

    return horse_map

# ── JSON 補完 ────────────────────────────────────────────

def enrich_json(json_path, csv_data, html_map):
    """JSONの各馬をCSV＋HTMLで補完し保存。変更した馬数を返す。"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for horse in data.get("horses", []):
        name = normalize_name(horse.get("name", ""))
        row       = csv_data.get(name, {})
        html_data = html_map.get(name, {})
        changed   = False

        if not row and not html_data:
            print(f"  ⚠️  未マッチ: {name}")
            continue

        # ── 騎手（CSVから優先）
        jockey = row.get("騎手", "").strip()
        if jockey and not horse.get("jockey"):
            horse["jockey"] = jockey
            changed = True

        # ── 厩舎（CSVから優先、なければHTMLから）
        trainer = clean_trainer(row.get("厩舎", ""))
        if not trainer:
            trainer = html_data.get("trainer", "")
        if trainer and not horse.get("trainer"):
            horse["trainer"] = trainer
            changed = True

        # ── 外厩（CSVから優先、なければHTMLから）
        gaiku = row.get("外厩名", "").strip()
        if not gaiku and "gaiku" in html_data:
            gaiku = html_data["gaiku"]
        # gaiku=""（在厩）でも未設定なら注入（keyが無い場合のみ）
        if "gaiku" not in horse and ("gaiku" in html_data or gaiku):
            horse["gaiku"] = gaiku
            changed = True
        elif gaiku and not horse.get("gaiku"):
            horse["gaiku"] = gaiku
            changed = True

        # ── 前走（CSVから優先、なければHTMLから）
        last_race = clean_last_race(row.get("前走情報", ""))
        if not last_race:
            last_race = html_data.get("lastRace", "")
        if last_race and not horse.get("lastRace"):
            horse["lastRace"] = last_race
            changed = True

        # ── 父名（HTMLから）
        sire = html_data.get("sire", "")
        if sire and not horse.get("sire"):
            horse["sire"] = sire
            changed = True

        if changed:
            updated += 1
            print(f"  ✅ {name}: 父={horse.get('sire','—')} 騎={horse.get('jockey','—')} 厩={horse.get('trainer','—')} 外厩={horse.get('gaiku') or '在厩'} 前走={horse.get('lastRace','—')}")

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
        html_map = load_horse_data_from_html(html_path) if html_path else {}

        n = enrich_json(json_path, csv_data, html_map)
        total_updated += n
        print(f"  → {n} 頭更新")

    print(f"\n✨ 完了: 合計 {total_updated} 頭を更新しました")

if __name__ == "__main__":
    main()
