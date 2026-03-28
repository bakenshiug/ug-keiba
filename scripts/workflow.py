#!/usr/bin/env python3
"""
workflow.py
-----------
重賞展望 → 最終予想 の一括ワークフロースクリプト

使い方:
  python3 scripts/workflow.py            # Downloadsから新JSONを取り込み→注入→push
  python3 scripts/workflow.py --publish  # published:true に変更してpush
  python3 scripts/workflow.py --list     # 現在の最終予想一覧を表示

手順:
  1. final-tool.html でJSON作成 → ダウンロード
  2. python3 scripts/workflow.py  （取り込み・注入・push）
  3. レース直前に python3 scripts/workflow.py --publish
"""

import json, re, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime, timedelta

BASE      = Path(__file__).parent.parent / "docs"
DATA      = BASE / "data"
DOWNLOADS = Path.home() / "Downloads"
LIST_JSON = DATA / "final-list.json"
SKIP      = {"final-list.json", "final-history.json"}

WEEK_LABELS = {
    "04-04": "4月4日（土）〜5日（日）重賞週",
    "04-05": "4月4日（土）〜5日（日）重賞週",
    "04-11": "4月11日（土）〜12日（日）重賞週",
    "04-12": "4月11日（土）〜12日（日）重賞週",
    "04-18": "4月18日（土）〜19日（日）重賞週",
    "04-19": "4月18日（土）〜19日（日）重賞週",
    "04-25": "4月25日（土）〜26日（日）重賞週",
    "04-26": "4月25日（土）〜26日（日）重賞週",
    "05-02": "5月2日（土）〜3日（日）重賞週",
    "05-03": "5月2日（土）〜3日（日）重賞週",
}

def run(cmd, **kwargs):
    return subprocess.run(cmd, shell=True, check=True, **kwargs)

def load_list():
    if LIST_JSON.exists():
        return json.loads(LIST_JSON.read_text(encoding="utf-8"))
    return {"week": "", "label": "", "files": []}

def save_list(data):
    LIST_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_week_label(files):
    """ファイル名の日付からweek・labelを自動判定"""
    dates = []
    for f in files:
        m = re.search(r"(\d{4}-\d{2}-\d{2})$", f)
        if m:
            dates.append(m.group(1))
    if not dates:
        return "", ""
    earliest = sorted(dates)[0]
    md = earliest[5:]  # MM-DD
    label = WEEK_LABELS.get(md, f"{earliest}週")
    return earliest, label

# ─────────────────────────────────────────────────────────
# コマンド: --list
# ─────────────────────────────────────────────────────────

def cmd_list():
    lst = load_list()
    print(f"\n📅 {lst.get('label', lst.get('week', ''))}")
    for f in lst.get("files", []):
        path = DATA / f"{f}.json"
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            r = d.get("race", {})
            pub = "✅ 公開中" if d.get("published") else "🔒 非公開"
            honmei = next((h["name"] for h in d.get("horses", []) if h.get("mark") == "◎"), "—")
            print(f"  {pub}  {r.get('grade','')} {r.get('name','')}  ◎{honmei}")
    print()

# ─────────────────────────────────────────────────────────
# コマンド: --publish
# ─────────────────────────────────────────────────────────

def cmd_publish():
    lst = load_list()
    changed = []
    for f in lst.get("files", []):
        path = DATA / f"{f}.json"
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        if not d.get("published"):
            d["published"] = True
            path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            r = d.get("race", {})
            changed.append(r.get("name", f))
            print(f"  ✅ 公開: {r.get('name', f)}")
    if not changed:
        print("  ℹ️  公開済みでない予想はありませんでした")
        return
    names = "・".join(changed)
    run(f'git add docs/data/final-*.json && git commit -m "fix: {names} published: true に変更・公開" && git push')
    print(f"\n🚀 push完了！ {names} が公開されました")

# ─────────────────────────────────────────────────────────
# コマンド: デフォルト（取り込み → 注入 → push）
# ─────────────────────────────────────────────────────────

def cmd_import():
    # 1. Downloadsから新しいfinal-*.jsonを探す（24時間以内）
    cutoff = datetime.now() - timedelta(hours=24)
    new_files = []
    for f in DOWNLOADS.glob("final-*.json"):
        if f.name in SKIP:
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime > cutoff:
            new_files.append(f)

    if not new_files:
        print("⚠️  Downloads に新しい final-*.json が見つかりません（24時間以内）")
        print("   final-tool.html でJSONをダウンロードしてから再実行してください")
        return

    # 2. docs/data/ にコピー
    copied = []
    for f in new_files:
        dest = DATA / f.name
        shutil.copy2(f, dest)
        print(f"  📥 取り込み: {f.name}")
        copied.append(f.name)

    # 3. enrich（データ注入）
    print("\n  💉 データ注入中...")
    enrich_script = Path(__file__).parent / "enrich_final_json.py"
    subprocess.run(f"python3 {enrich_script}", shell=True)

    # 4. final-list.json 更新
    lst = load_list()
    existing = set(lst.get("files", []))

    # 今週のJSONを全スキャン（新規含む）
    all_files = []
    for p in sorted(DATA.glob("final-*.json")):
        if p.name in SKIP:
            continue
        all_files.append(p.stem)

    # 新しく追加されたファイルがあれば追記
    added = [s for s in all_files if s not in existing]
    if added:
        # 新しい週が始まった場合はリセット
        current_dates = [re.search(r"(\d{4}-\d{2}-\d{2})$", f).group(1) for f in existing if re.search(r"(\d{4}-\d{2}-\d{2})$", f)]
        new_dates = [re.search(r"(\d{4}-\d{2}-\d{2})$", f).group(1) for f in added if re.search(r"(\d{4}-\d{2}-\d{2})$", f)]

        if current_dates and new_dates:
            current_week = sorted(current_dates)[0][:7]  # YYYY-MM
            new_week = sorted(new_dates)[0][:7]
            if current_week != new_week:
                # 新しい月/週 → リセット
                print(f"\n  📅 新しい週を検出: {new_week}。final-list.json をリセットします")
                all_files = [f for f in all_files if re.search(r"\d{4}-" + new_week[5:], f)]

        week, label = get_week_label(all_files)
        lst["week"] = week
        lst["label"] = label
        lst["files"] = all_files
        save_list(lst)
        print(f"\n  📝 final-list.json 更新: {', '.join(added)}")

    # 5. git push
    print("\n  🚀 push中...")
    run('git add docs/data/ && git commit -m "data: 最終予想データ取り込み・自動注入" && git push')
    print("\n✨ 完了！")
    print("   公開するときは: python3 scripts/workflow.py --publish")

# ─────────────────────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if "--list" in args:
        cmd_list()
    elif "--publish" in args:
        cmd_publish()
    else:
        cmd_import()

if __name__ == "__main__":
    main()
