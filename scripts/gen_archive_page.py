#!/usr/bin/env python3
"""
gen_archive_page.py
言霊神宮の過去週アーカイブページを生成
- kotodama.html をベースにし、特定週のJSONのみ読み込み・paidDayロック解除
- ファイル名は archive-{YYYY-MM-DD}.html
- アーカイブ用バナーを上部に表示

Usage:
    python3 scripts/gen_archive_page.py 2026-05-03 --label "天皇賞・春週"
    python3 scripts/gen_archive_page.py 2026-05-03   # ラベル省略可
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TEMPLATE = DOCS / "kotodama.html"


def generate(date_str, label=None):
    if not TEMPLATE.exists():
        print(f"❌ テンプレートが見つかりません: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    out_filename = f"archive-{date_str}.html"
    out_path = DOCS / out_filename
    label_text = f"（{label}）" if label else ""

    html = TEMPLATE.read_text(encoding="utf-8")

    # 1) 該当日のJSONだけ読み込む
    target_json = f"data/kotodama-test/{date_str}.json"
    html = re.sub(
        r"const FILES\s*=\s*\[[^\]]*\];",
        f"const FILES = ['{target_json}'];",
        html,
        count=1,
    )

    # 2) paidDay 強制 false（アーカイブは全公開）
    html = html.replace(
        "const paidDay = d.paidDay === true;",
        "const paidDay = false; /* アーカイブ：全公開 */",
    )

    # 3) <title> 変更
    html = re.sub(
        r"<title>[^<]*</title>",
        f"<title>言霊神宮アーカイブ {date_str}{label_text} ｜ UG競馬神宮</title>",
        html,
        count=1,
    )

    # 4) アーカイブバナー注入
    banner = f"""
<div style="background:linear-gradient(135deg,#f5f2eb,#fbf7ee);border-bottom:2px solid #8a7a3a;
            padding:14px 20px;text-align:center;font-family:'Shippori Mincho',serif;letter-spacing:.05em">
  📜 <b style="color:#7A1E1E">言霊神宮アーカイブ</b>
  ｜ {date_str}{label_text} 全レース picks
  ｜ <a href="kotodama.html" style="color:#a44a3f;font-weight:700;text-decoration:underline">最新週へ戻る ▶</a>
  ｜ <a href="kotodama-archive.html" style="color:#a44a3f;font-weight:700;text-decoration:underline">アーカイブ一覧 📚</a>
</div>
"""
    html = html.replace("<body>", "<body>" + banner, 1)

    out_path.write_text(html, encoding="utf-8")

    print("=" * 60)
    print(f"✅ アーカイブページ生成完了")
    print("=" * 60)
    print(f"📁 ファイル：{out_path.relative_to(ROOT)}")
    print(f"🌐 URL：https://bakenshiug.github.io/ug-keiba/{out_filename}")
    print(f"📅 対象週：{date_str}{label_text}")
    print("=" * 60)
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("--label", default=None, help="週の通称（例：天皇賞・春週）")
    args = parser.parse_args()
    generate(args.date, args.label)


if __name__ == "__main__":
    main()
