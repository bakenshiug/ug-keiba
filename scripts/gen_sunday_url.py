#!/usr/bin/env python3
"""
gen_sunday_url.py
NOTE購入者専用の限定URL生成
- ランダムハッシュ付きHTMLファイルを docs/ に生成
- 元の kotodama.html をベースにし、paidDay フラグを強制 false に上書き
- 該当日のJSONだけを読み込む

Usage:
    python3 scripts/gen_sunday_url.py 2026-05-10
    python3 scripts/gen_sunday_url.py 2026-05-10 --cleanup   # 古いsunday-*.html削除
"""
import argparse
import re
import secrets
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TEMPLATE = DOCS / "kotodama.html"


def gen_hash(length=6):
    """URL safe ランダムハッシュ"""
    return secrets.token_urlsafe(8)[:length]


def cleanup_old(keep_date=None):
    """古い sunday-*.html を削除"""
    removed = []
    for f in DOCS.glob("sunday-*.html"):
        if keep_date and keep_date.replace("-", "")[-4:] in f.name:
            continue
        f.unlink()
        removed.append(f.name)
    return removed


def generate(date_str, cleanup=False):
    """限定URLファイル生成"""
    if not TEMPLATE.exists():
        print(f"❌ テンプレートが見つかりません: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    # 日付フォーマット：2026-05-10 → 0510（月日のみ）
    date_short = date_str.replace("-", "")[-4:]

    # ハッシュ生成
    hash_part = gen_hash(6)
    out_filename = f"sunday-{date_short}-{hash_part}.html"
    out_path = DOCS / out_filename

    # ベースHTML読み込み
    html = TEMPLATE.read_text(encoding="utf-8")

    # 1) 該当日のJSONだけ読み込むよう FILES 配列を限定
    target_json = f"data/kotodama-test/{date_str}.json"
    html = re.sub(
        r"const FILES\s*=\s*\[[^\]]*\];",
        f"const FILES = ['{target_json}'];",
        html,
        count=1,
    )

    # 2) paidDay フラグを強制 false に（ロック解除）
    #    load() 内で paidDay を読む箇所を上書き
    html = html.replace(
        "const paidDay = d.paidDay === true;",
        "const paidDay = false; /* 限定URL：ロック解除 */",
    )

    # 3) <title> を変更
    html = re.sub(
        r"<title>[^<]*</title>",
        f"<title>言霊神宮 限定 {date_str} ｜ UG競馬神宮</title>",
        html,
        count=1,
    )

    # 4) 限定URL バナー注入（body直後）
    banner = f"""
<div style="background:linear-gradient(135deg,#fff8e8,#fff5dc);border-bottom:2px solid #c9a84c;
            padding:12px 20px;text-align:center;font-family:'Shippori Mincho',serif;letter-spacing:.05em">
  📜 <b style="color:#a44a3f">神宮NOTEパック購入者限定URL</b>
  ｜ {date_str} 全12R picks 公開中
  ｜ <span style="color:#7A1E1E">本URLの転載・共有はご遠慮ください</span>
</div>
"""
    html = html.replace("<body>", "<body>" + banner, 1)

    # 書き出し
    out_path.write_text(html, encoding="utf-8")

    # クリーンアップ
    removed = []
    if cleanup:
        removed = cleanup_old(keep_date=date_str)

    return out_path, hash_part, removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("--cleanup", action="store_true",
                        help="古い sunday-*.html を削除")
    args = parser.parse_args()

    out_path, hash_part, removed = generate(args.date, cleanup=args.cleanup)

    full_url = f"https://bakenshiug.github.io/ug-keiba/{out_path.name}"

    print("=" * 60)
    print(f"✅ 限定URL生成完了")
    print("=" * 60)
    print(f"📁 ファイル：{out_path.relative_to(ROOT)}")
    print(f"🔐 ハッシュ：{hash_part}")
    print()
    print(f"📋 NOTE貼付用URL：")
    print(f"   {full_url}")
    print()
    if removed:
        print(f"🗑  古いファイル削除：{len(removed)}件")
        for r in removed:
            print(f"   - {r}")
    print()
    print("⚠ 反映には git push が必要です：")
    print(f"   git add docs/{out_path.name}")
    print(f"   git commit -m 'NOTE限定URL追加 {args.date}'")
    print(f"   git push")
    print("=" * 60)


if __name__ == "__main__":
    main()
