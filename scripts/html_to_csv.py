#!/usr/bin/env python3
"""
UG競馬 HTML → CSV 変換スクリプト
使い方: python3 html_to_csv.py <htmlファイル> [出力csvファイル]
例:    python3 html_to_csv.py ../docs/2026-03-29-takamatsunomiya-kinen.html
"""

import re
import csv
import sys
import os

# セクション名の正規化マップ（HTML上の表記 → CSV列名）
SECTION_MAP = {
    '過去パフォーマンス': '過去パフォーマンス',
    'スピード指数':       '過去パフォーマンス',
    '前走ジャッジ':       '前走ジャッジ',
    '外厩 & 厩舎':        '外厩&厩舎',
    '外厩&厩舎':          '外厩&厩舎',
    '外厩ジャッジ':       '外厩&厩舎',
    '血統ジャッジ':       '血統ジャッジ',
    '馬格（前走馬体重）': '馬格',
    '馬格':               '馬格',
    'コース実績':         'コース実績',
    '前走脚質・上がり':   '前走脚質・上がり',
    '年齢':               '年齢',
}

GRADE_ORDER = {'S': 7, 'A': 6, 'B+': 5, 'B': 4, 'C+': 3, 'C': 3, 'D': 2, 'E': 1, '': 0}

CSV_COLUMNS = [
    '馬名', '総合グレード', '総合pt',
    '過去パフォーマンス', '前走ジャッジ', '外厩&厩舎',
    '血統ジャッジ', '馬格', 'コース実績', '前走脚質・上がり', '年齢',
    '前走情報', '性齢', '騎手', '馬体重', '厩舎', '外厩名',
]


def strip_tags(html):
    """HTMLタグを除去してテキストを返す"""
    return re.sub(r'<[^>]+>', '', html).strip()


def find_div_end(content, start):
    """start位置の<div>に対応する</div>の終端インデックスを返す"""
    depth = 0
    i = start
    while i < len(content):
        if content[i:i+4] == '<div':
            depth += 1
            i += 4
        elif content[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                return i + 6
            i += 6
        else:
            i += 1
    return len(content)


def parse_card(card_html):
    """カードHTMLから各フィールドを抽出してdictを返す"""
    data = {col: '' for col in CSV_COLUMNS}

    # 馬名
    m = re.search(r'<h2[^>]*serif-headline[^>]*>([^<]+)</h2>', card_html)
    if m:
        name = m.group(1).strip()
        # 印を除去
        name = re.sub(r'^[◎○▲☆△]\s*', '', name)
        data['馬名'] = name

    # 総合グレード・pt（label-data spanから）
    m = re.search(r'<span[^>]*label-data[^>]*>総合\s*([^<]+)</span>', card_html)
    if m:
        data['総合グレード'] = m.group(1).strip()

    # ptはカードコメントまたはcard divのクラスから取得済み（呼び出し元で設定）

    # 前走情報（最初の小テキスト p）
    m = re.search(r'<p class="text-\[10px\] text-\[#707a6a\] font-bold">([^<]+)</p>', card_html)
    if m:
        data['前走情報'] = strip_tags(m.group(1)).replace('前走：', '').strip()

    # 性齢・騎手・馬体重・厩舎（2行目の小テキスト）
    m = re.search(r'<p class="text-\[10px\] text-\[#707a6a\] mt-0\.5">([^<]+)</p>', card_html)
    if m:
        info = m.group(1).strip()
        # 例: "牝7 浜中俊 56kg　栗東・長谷川浩厩舎"
        parts = re.split(r'\s+', info.replace('　', ' '))
        if len(parts) >= 1:
            data['性齢'] = parts[0]
        if len(parts) >= 2:
            data['騎手'] = parts[1]
        if len(parts) >= 3:
            data['馬体重'] = parts[2]
        if len(parts) >= 4:
            data['厩舎'] = ' '.join(parts[3:])

    # 外厩名（bg-[#c4eab5] spanから）
    m = re.search(r'<span[^>]*bg-\[#c4eab5\][^>]*>([^<]+)</span>', card_html)
    if m:
        data['外厩名'] = strip_tags(m.group(1)).replace('🌿', '').replace('🏠 在厩', '在厩').strip()

    # 各セクションのグレード
    # パターン: grade-XX のspanの次にセクション名
    section_pattern = re.compile(
        r'<span[^>]*class="[^"]*rounded-full\s+grade-([^"]+)"[^>]*>[^<]*</span>\s*'
        r'<p[^>]*>([^<]+)</p>',
        re.DOTALL
    )
    for sm in section_pattern.finditer(card_html):
        grade = sm.group(1).strip()
        section_raw = sm.group(2).strip()
        section_key = SECTION_MAP.get(section_raw)
        if section_key and not data[section_key]:
            data[section_key] = grade

    return data


def parse_html(filepath):
    """HTMLファイルを解析して全カードのデータリストを返す"""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    horses = []

    # カードコメント: <!-- ① 馬名 総合X (NNpt) -->
    comment_pattern = re.compile(
        r'<!--\s*[①-㉟㊀-㊿\d]+\s+(.+?)\s+総合(\S+)\s+\((\d+)pt\)\s*-->'
    )

    # カードdivのパターン
    card_div_pattern = re.compile(
        r'<div class="(?:bg-white )?rounded-2xl[^"]*border[^"]*"'
    )

    i = 0
    while i < len(content):
        # カードコメントを探す
        cm = comment_pattern.search(content, i)
        if not cm:
            break

        horse_name_comment = cm.group(1).strip()
        grade_comment = cm.group(2).strip()
        pt = int(cm.group(3))

        # コメントの直後からカードdivを探す
        search_start = cm.end()
        dm = card_div_pattern.search(content, search_start, search_start + 500)
        if not dm:
            i = cm.end()
            continue

        card_start = dm.start()
        card_end = find_div_end(content, card_start)
        card_html = content[card_start:card_end]

        data = parse_card(card_html)
        data['総合グレード'] = grade_comment
        data['総合pt'] = pt

        # 馬名はコメントから取得（印除去済み）
        if not data['馬名']:
            data['馬名'] = horse_name_comment

        horses.append(data)
        i = card_end

    return horses


def main():
    if len(sys.argv) < 2:
        print('使い方: python3 html_to_csv.py <htmlファイル> [出力csvファイル]')
        sys.exit(1)

    html_path = sys.argv[1]
    if not os.path.exists(html_path):
        print(f'ファイルが見つかりません: {html_path}')
        sys.exit(1)

    # 出力先
    if len(sys.argv) >= 3:
        csv_path = sys.argv[2]
    else:
        base = os.path.splitext(os.path.basename(html_path))[0]
        csv_path = os.path.join(os.path.dirname(html_path), base + '.csv')

    horses = parse_html(html_path)

    if not horses:
        print('カードが見つかりませんでした。')
        sys.exit(1)

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(horses)

    print(f'{len(horses)}頭のデータを出力しました → {csv_path}')

    # プレビュー表示
    print()
    print(f"{'馬名':<16} {'総合':>4} {'pt':>4} {'パフォ':>4} {'前走':>4} {'外厩':>4} {'血統':>4} {'馬格':>4} {'コース':>5} {'脚質':>4} {'年齢':>4}")
    print('-' * 75)
    for h in horses:
        print(
            f"{h['馬名']:<16} "
            f"{h['総合グレード']:>4} "
            f"{str(h['総合pt']):>4} "
            f"{h['過去パフォーマンス']:>4} "
            f"{h['前走ジャッジ']:>4} "
            f"{h['外厩&厩舎']:>4} "
            f"{h['血統ジャッジ']:>4} "
            f"{h['馬格']:>4} "
            f"{h['コース実績']:>5} "
            f"{h['前走脚質・上がり']:>4} "
            f"{h['年齢']:>4}"
        )


if __name__ == '__main__':
    main()
