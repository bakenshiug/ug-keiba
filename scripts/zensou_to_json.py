#!/usr/bin/env python3
"""
前走成績CSV → JSON 変換スクリプト
使い方:
  python3 scripts/zensou_to_json.py <CSVファイルパス> <出力JSONパス>

例:
  python3 scripts/zensou_to_json.py \
    local/analysis/zensou-2026-04-05-nakayama-11r.csv \
    docs/data/prevrace/zensou-2026-04-05-nakayama-11r.json

CSVカラム:
  番,馬名,性齢,間,前走日,コース,状,着,人,前走レース名,上3F,決手,体重,3F順,PCI,平均1F,速度,着差
"""

import csv
import json
import sys
import os
import re
from pathlib import Path


def parse_course(course_str):
    """コース文字列をパース: 例 '中・T16' → {venue, surface, distance}"""
    # venue: 東/阪/中/京/小/新/福 など
    # surface: T=芝, D=ダート
    # distance: 数字
    m = re.match(r'([東阪中京小新福])・([TD])(\d+)', course_str)
    if m:
        venue_map = {
            '東': '東京', '阪': '阪神', '中': '中山',
            '京': '京都', '小': '小倉', '新': '新潟', '福': '福島'
        }
        surf_map = {'T': '芝', 'D': 'ダート'}
        return {
            'venue': venue_map.get(m.group(1), m.group(1)),
            'surface': surf_map.get(m.group(2), m.group(2)),
            'distance': int(m.group(3)) * 100
        }
    return {'venue': course_str, 'surface': '?', 'distance': 0}


def parse_pci(pci_str):
    """PCI文字列をパース: 例 '56.6*' → {value: 56.6, aboveAvg: True}"""
    star = pci_str.endswith('*')
    try:
        value = float(pci_str.rstrip('*'))
    except ValueError:
        value = None
    return {'value': value, 'aboveAvg': star}


def safe_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def safe_int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def convert(csv_path, json_path):
    horses = []

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # カラム名の揺れに対応: 場コース / コース、月.日 / 前走日
            course_raw = row.get('コース') or row.get('場コース') or ''
            date_raw   = row.get('前走日') or row.get('月.日') or ''
            course = parse_course(course_raw.strip())
            pci = parse_pci(row.get('PCI', '0'))

            horse = {
                'umaban':        safe_int(row.get('番')),
                'umaname':       row.get('馬名', '').strip(),
                'sexAge':        row.get('性齢', '').strip(),
                'interval':      safe_int(row.get('間')),      # 中何週（"連"等はNone）
                'interval2':     row.get('間2', '').strip() or None,   # 前々走間隔（初戦表記等）
                'prevDate':      date_raw,
                'prevVenue':     course['venue'],
                'prevSurface':   course['surface'],
                'prevDistance':  course['distance'],
                'prevCourse':    course_raw.strip(),
                'prevCondition': row.get('状', '').strip(),
                'prevRank':      safe_int(row.get('着')),
                'prevPopularity':safe_int(row.get('人')),
                'prevRaceName':  row.get('前走レース名', '').strip(),
                'last3F':        safe_float(row.get('上3F')),
                'runningStyle':  row.get('決手', '').strip(),
                'weight':        safe_int(row.get('体重')),
                'last3FRank':    safe_int(row.get('3F順')),
                'pci':           pci['value'],
                'pciAboveAvg':   pci['aboveAvg'],
                'avg1F':         safe_float(row.get('平均1F')),
                'last3FDiff':    safe_float(row.get('-3F差')),  # 上3F差（前後半差）
                'speed':         safe_float(row.get('速度')),
                'margin':        safe_float(row.get('着差')),
            }
            horses.append(horse)

    # ファイル名からメタ情報を推定
    basename = Path(csv_path).stem  # zensou-2026-04-05-nakayama-11r
    parts = basename.split('-')

    output = {
        'generatedFrom': os.path.basename(csv_path),
        'horses': horses
    }

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✓ {len(horses)}頭分を変換: {json_path}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
