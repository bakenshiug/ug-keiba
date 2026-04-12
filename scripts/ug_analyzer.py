#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ug_analyzer.py — UG強奪競馬新聞 Target競馬CSV統合アナライザー
---------------------------------------------------------------
Usage:
  python3 ug_analyzer.py マーチS               # カレントディレクトリのCSVを使用
  python3 ug_analyzer.py マーチS --dir ~/Downloads
  python3 ug_analyzer.py マーチS --dir ~/Downloads --out results/

出力:
  {race}_ug_analysis.json   → final-tool.html / shindan-tool.html に読み込む
  {race}_ug_summary.md      → 別AIに貼り付けてコメント生成用（トークン節約版）
"""

import csv
import json
import os
import sys
import argparse
from datetime import date

# ══════════════════════════════════════════
#  グレード → ポイント変換
# ══════════════════════════════════════════
GRADE_PT = {'S': 7, 'A': 6, 'B+': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, '': 0}

GRADE_LABEL = {
    'S':  '🏆 S（最上位）',
    'A':  '⭐ A（上位）',
    'B+': '✅ B+',
    'B':  '📌 B',
    'C':  '➖ C',
    'D':  '⬇️ D',
    'E':  '❌ E',
}

# ══════════════════════════════════════════
#  CSV読み込みユーティリティ
# ══════════════════════════════════════════
def read_csv(path):
    """Shift-JIS / UTF-8-BOM の両方に対応して読み込む"""
    for enc in ['utf-8-sig', 'utf-8', 'cp932', 'shift-jis']:
        try:
            with open(path, encoding=enc, newline='') as f:
                rows = list(csv.DictReader(f))
            if rows:
                return rows
        except (UnicodeDecodeError, Exception):
            continue
    raise ValueError(f'ファイルを読み込めません: {path}')


def find_csv(directory, prefix, suffix):
    """prefix + suffix のCSVファイルを検索（ファイル名の揺れに対応）"""
    candidates = [
        os.path.join(directory, f'{prefix}_{suffix}.csv'),
        os.path.join(directory, f'{prefix}{suffix}.csv'),
        os.path.join(directory, f'{prefix} {suffix}.csv'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ══════════════════════════════════════════
#  各CSVのパース
# ══════════════════════════════════════════
def parse_sogo_score(rows):
    """総合スコア.csv → {馬名: データ}"""
    result = {}
    for r in rows:
        name = r.get('馬名', '').strip()
        if not name:
            continue
        result[name] = {
            'num':           r.get('馬番', '').strip(),
            'name':          name,
            'sex_age':       r.get('性齢', '').strip(),
            'sire':          r.get('父', '').strip(),
            'jockey':        r.get('騎手', '').strip(),
            'trainer':       r.get('調教師', '').strip(),
            'gaiku':         r.get('外厩', '').strip(),
            'overall_grade': r.get('総合グレード', '').strip(),
            'overall_pt':    _int(r.get('総合ポイント', '0')),
            'factors': {
                '年齢':     _factor(r, '年齢'),
                '前走脚質': _factor(r, '前走脚質'),
                '馬体重':   _factor(r, '馬体重'),
                '血統':     _factor(r, '血統'),
                '厩舎':     _factor(r, '厩舎'),
                '前走評価': {'grade': r.get('前走評価_G',''), 'pt': _int(r.get('前走評価_pt','0'))},
                '外厩':     {'grade': r.get('外厩_G',''),    'pt': _int(r.get('外厩_pt','0'))},
                '過去PF':   {
                    'grade':     r.get('過去PF_G',''),
                    'pt':        _int(r.get('過去PF_pt','0')),
                    'max_score': _float(r.get('過去PF_最高スコア(×1.7)', '0')),
                },
            },
        }
    return result


def parse_prev_eval(rows):
    """前走評価.csv → {馬名: コメント類}"""
    result = {}
    for r in rows:
        name = r.get('馬名', '').strip()
        if not name:
            continue
        result[name] = {
            'prev_race':       r.get('前走', '').strip(),
            'prev_rank':       r.get('前走着順', '').strip(),
            'prev_eval':       r.get('前走評価', '').strip(),
            'prev_pt':         _int(r.get('前走ポイント', '0')),
            'gaiku_name':      r.get('外厩', '').strip(),
            'gaiku_eval':      r.get('外厩評価', '').strip(),
            'gaiku_pt':        _int(r.get('外厩ポイント', '0')),
            'jockey_comment':  r.get('騎手コメント', '').strip(),
            'next_memo':       r.get('次走メモ', '').strip(),
            'prev_nick':       r.get('前走ニックコメント', '').strip(),
            'gaiku_nick':      r.get('外厩ニックコメント', '').strip(),
        }
    return result


def parse_past_pf(rows):
    """過去パフォーマンス.csv → {馬名: スピード指数&コメント}"""
    result = {}
    for r in rows:
        name = (r.get('horse') or r.get('馬名') or '').strip()
        if not name:
            continue
        result[name] = {
            'max_score_raw': _float(r.get('最高スコア_元', '0')),
            'max_score_x17': _float(r.get('最高スコア_x17', '0')),
            'max_course':    r.get('最高コース', '').strip(),
            'prev_score_raw':_float(r.get('前走スコア_元', '0')),
            'prev_score_x17':_float(r.get('前走スコア_x17', '0')),
            'grade':         r.get('評価', '').strip(),
            'pt':            _int(r.get('ポイント', '0')),
            'nick_comment':  r.get('ニックコメント', '').strip(),
        }
    return result


# ══════════════════════════════════════════
#  データ統合
# ══════════════════════════════════════════
def merge_all(sogo, prev_eval, past_pf):
    """全CSVをマージして馬リストを生成"""
    horses = []
    for name, base in sogo.items():
        h = dict(base)
        # 前走評価コメント
        ev = prev_eval.get(name, {})
        h['prev_race']      = ev.get('prev_race', '')
        h['prev_rank']      = ev.get('prev_rank', '')
        h['gaiku_name']     = ev.get('gaiku_name', '') or h.get('gaiku', '')
        h['comments'] = {
            'jockey':    ev.get('jockey_comment', ''),
            'next_memo': ev.get('next_memo', ''),
            'prev_nick': ev.get('prev_nick', ''),
            'gaiku_nick':ev.get('gaiku_nick', ''),
        }
        # スピード指数
        pf = past_pf.get(name, {})
        h['speed'] = {
            'max_raw':    pf.get('max_score_raw', 0),
            'max_x17':    pf.get('max_score_x17', 0),
            'max_course': pf.get('max_course', ''),
            'prev_raw':   pf.get('prev_score_raw', 0),
            'prev_x17':   pf.get('prev_score_x17', 0),
            'nick':       pf.get('nick_comment', ''),
        }
        # 総合スコア再計算（全ファクターptの合計）
        total = sum(
            v.get('pt', 0) for v in h['factors'].values()
        )
        h['total_factor_pt'] = total
        horses.append(h)

    # 総合ポイント降順でソート
    horses.sort(key=lambda x: x['overall_pt'], reverse=True)
    return horses


# ══════════════════════════════════════════
#  JSON出力
# ══════════════════════════════════════════
def to_json(race_name, horses, out_path):
    data = {
        'race':        race_name,
        'analyzed_at': str(date.today()),
        'count':       len(horses),
        'horses':      horses,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'✅ JSON出力: {out_path}')


# ══════════════════════════════════════════
#  Markdown出力（別AI投入用・トークン節約）
# ══════════════════════════════════════════
def to_markdown(race_name, horses, out_path):
    lines = []
    lines.append(f'# {race_name} UG強奪スコア分析\n')
    lines.append(f'分析日: {date.today()}\n')

    # ── スコアランキング表 ──
    lines.append('## 総合スコアランキング\n')
    lines.append('| 順位 | 馬名 | 総合 | pt | 過去PF | 前走評価 | 外厩 | 血統 | 厩舎 | 最高指数 |')
    lines.append('|------|------|------|----|--------|----------|------|------|------|----------|')
    for i, h in enumerate(horses, 1):
        f = h['factors']
        lines.append(
            f"| {i} | {h['name']} | {h['overall_grade']} | {h['overall_pt']} "
            f"| {f['過去PF']['grade']} | {f['前走評価']['grade']} "
            f"| {f['外厩']['grade']} | {f['血統']['grade']} "
            f"| {f['厩舎']['grade']} | {h['speed']['max_x17']:.1f} |"
        )
    lines.append('')

    # ── 馬別詳細 ──
    lines.append('## 馬別詳細\n')
    for i, h in enumerate(horses, 1):
        f  = h['factors']
        sp = h['speed']
        c  = h['comments']

        lines.append(f"### {i}. {h['name']}（{h['overall_grade']} / {h['overall_pt']}pt）")
        lines.append(f"**性齢:** {h['sex_age']}　**父:** {h['sire']}　**騎手:** {h['jockey']}　**厩舎:** {h['trainer']}")
        lines.append(f"**外厩:** {h['gaiku_name'] or h['gaiku'] or '不明'}")
        lines.append(f"**前走:** {h['prev_race']} {h['prev_rank']}")

        # ファクター一覧
        factor_str = '　'.join([
            f"年齢{f['年齢']['grade']}",
            f"脚質{f['前走脚質']['grade']}",
            f"馬体重{f['馬体重']['grade']}",
            f"血統{f['血統']['grade']}",
            f"厩舎{f['厩舎']['grade']}",
            f"前走{f['前走評価']['grade']}",
            f"外厩{f['外厩']['grade']}",
            f"過去PF {f['過去PF']['grade']}",
        ])
        lines.append(f"**ファクター:** {factor_str}")

        # スピード指数
        if sp['max_x17'] > 0:
            lines.append(
                f"**スピード指数:** 最高{sp['max_x17']:.1f}（元{sp['max_raw']:.1f}・{sp['max_course']}）"
                f"　前走{sp['prev_x17']:.1f}（元{sp['prev_raw']:.1f}）"
            )

        # コメント（長いので先頭80文字）
        if c['jockey']:
            lines.append(f"**騎手コメント:** {c['jockey'][:120]}")
        if c['prev_nick']:
            lines.append(f"**前走分析:** {c['prev_nick'][:120]}")
        if c['gaiku_nick']:
            lines.append(f"**外厩分析:** {c['gaiku_nick'][:80]}")
        if sp['nick']:
            lines.append(f"**指数分析:** {sp['nick'][:80]}")
        if c['next_memo']:
            lines.append(f"**次走メモ:** {c['next_memo'][:100]}")

        lines.append('')

    # ── AI分析依頼プロンプト ──
    lines.append('---')
    lines.append('## ✍️ AI分析依頼（このまま別AIに貼り付けてください）')
    lines.append(f"""
上記は{race_name}の全出走馬データです。
以下の観点で穴馬を3頭セレクションしてください。

1. 総合スコアが低いのに特定ファクターで突出している馬
2. 外厩・騎手コメントから本気度が読み取れる馬
3. スピード指数の上昇傾向がある馬

各馬について：
- 推奨理由（3行以内）
- 懸念点（1行）
- UG穴馬セレクション評価（◎/○/▲）

出力形式はMarkdownで。
""")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'✅ Markdown出力: {out_path}')


# ══════════════════════════════════════════
#  ユーティリティ
# ══════════════════════════════════════════
def _int(v):
    try:
        return int(str(v).replace(',', '').strip())
    except:
        return 0

def _float(v):
    try:
        return float(str(v).replace(',', '').strip())
    except:
        return 0.0

def _factor(row, key):
    return {
        'grade': row.get(f'{key}_G', '').strip(),
        'pt':    _int(row.get(f'{key}_pt', '0')),
        'rate':  row.get(f'{key}_複勝率', '').strip(),
    }


# ══════════════════════════════════════════
#  メイン
# ══════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description='UG強奪競馬新聞 Target競馬CSVアナライザー')
    parser.add_argument('race', help='レース名プレフィックス（例: マーチS, 日経賞）')
    parser.add_argument('--dir', default=os.path.expanduser('~/Downloads'),
                        help='CSVファイルのディレクトリ（デフォルト: ~/Downloads）')
    parser.add_argument('--out', default='.', help='出力ディレクトリ（デフォルト: カレント）')
    args = parser.parse_args()

    race   = args.race
    d      = args.dir
    outdir = args.out
    os.makedirs(outdir, exist_ok=True)

    print(f'\n🏇 {race} の分析を開始します...')
    print(f'   CSVディレクトリ: {d}')

    # ── ファイル検索 ──
    sogo_path  = find_csv(d, race, '総合スコア')
    prev_path  = find_csv(d, race, '前走評価')
    past_path  = find_csv(d, race, '過去パフォーマンス')

    if not sogo_path:
        print(f'❌ エラー: {race}_総合スコア.csv が見つかりません（{d}）')
        sys.exit(1)

    print(f'   総合スコア : {os.path.basename(sogo_path)}')
    print(f'   前走評価   : {os.path.basename(prev_path) if prev_path else "（なし）"}')
    print(f'   過去PF     : {os.path.basename(past_path) if past_path else "（なし）"}')

    # ── パース ──
    sogo     = parse_sogo_score(read_csv(sogo_path))
    prev_eval= parse_prev_eval(read_csv(prev_path))   if prev_path  else {}
    past_pf  = parse_past_pf(read_csv(past_path))     if past_path  else {}

    # ── マージ＆ソート ──
    horses = merge_all(sogo, prev_eval, past_pf)
    print(f'\n✅ {len(horses)}頭を分析しました\n')

    # ── ランキング表示 ──
    print(f'{"順位":>3}  {"馬名":<16}  {"総合":>3}  {"pt":>3}  {"過去PF":>5}  {"最高指数":>7}')
    print('-' * 55)
    for i, h in enumerate(horses, 1):
        sp = h['speed']
        print(
            f"{i:>3}. {h['name']:<16}  {h['overall_grade']:>3}  {h['overall_pt']:>3}pt"
            f"  {h['factors']['過去PF']['grade']:>5}  {sp['max_x17']:>7.1f}"
        )

    # ── 出力 ──
    print()
    json_path = os.path.join(outdir, f'{race}_ug_analysis.json')
    md_path   = os.path.join(outdir, f'{race}_ug_summary.md')
    to_json(race, horses, json_path)
    to_markdown(race, horses, md_path)

    print(f'\n🎯 完了！')
    print(f'   別AIへの投入 → {md_path}')
    print(f'   ツール読み込み → {json_path}')


if __name__ == '__main__':
    main()
