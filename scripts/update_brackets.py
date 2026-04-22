#!/usr/bin/env python3
"""
枠順確定(4/23木)流し込みスクリプト
====================================
Usage: python3 scripts/update_brackets.py

読み込み:
  scripts/brackets/2026-04-25-aobasho.tsv   (列: gate / num / name)
  scripts/brackets/2026-04-26-floras.tsv
  scripts/brackets/2026-04-26-milers-c.tsv

書き込み:
  - analysis/{race}/shutuba.json の各馬に waku, num 追加
  - docs/data/race-notes/{race-notes}.json の各馬に gate, num 追加
  - listOrder を num 昇順に振り直し
  - dataStatus を "preparation" → "bracket-fixed" に更新

TSVサンプル:
  gate	num	name
  1	1	アッカン
  1	2	アローメタル
  ...
"""
import json
import sys
from pathlib import Path

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')

RACE_MAP = [
    ('2026-04-25-aobasho',   '2026-04-25-tokyo-11r'),
    ('2026-04-26-floras',    '2026-04-26-tokyo-11r'),
    ('2026-04-26-milers-c',  '2026-04-26-kyoto-11r'),
]


def parse_tsv(path):
    """Return list of {gate, num, name}. Skip comments and empty rows."""
    rows = []
    header = None
    for line in path.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        parts = line.split('\t')
        if header is None:
            header = [p.strip() for p in parts]
            continue
        if len(parts) < 3:
            continue
        gate = parts[0].strip()
        num = parts[1].strip()
        name = parts[2].strip()
        if not name:
            continue
        if not gate or not num:
            print(f'  ⚠ 未入力スキップ: {name}', file=sys.stderr)
            continue
        try:
            rows.append({'gate': int(gate), 'num': int(num), 'name': name})
        except ValueError:
            print(f'  ⚠ 数値変換失敗: {line}', file=sys.stderr)
    return rows


def update_race(rd_name, rn_name):
    tsv = BASE / 'scripts/brackets' / f'{rd_name}.tsv'
    shutuba = BASE / 'analysis' / rd_name / 'shutuba.json'
    notes = BASE / 'docs/data/race-notes' / f'{rn_name}.json'

    if not tsv.exists():
        print(f'skip: {tsv.name} not found')
        return
    rows = parse_tsv(tsv)
    if not rows:
        print(f'skip: {tsv.name} 全列未入力')
        return

    by_name = {r['name']: r for r in rows}
    print(f'\n=== {rd_name} → {len(rows)}頭流し込み ===')

    # shutuba.json
    if shutuba.exists():
        s = json.loads(shutuba.read_text(encoding='utf-8'))
        hit = 0
        for h in s.get('horses', []):
            r = by_name.get(h['name'])
            if r:
                h['num'] = r['num']
                h['waku'] = r['gate']  # shutuba側は 'waku' フィールド
                hit += 1
        # 馬番順にソート
        s['horses'].sort(key=lambda h: h.get('num') or 999)
        shutuba.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'  shutuba.json: {hit}/{len(s["horses"])} 馬マッチ')

    # race-notes
    if notes.exists():
        n = json.loads(notes.read_text(encoding='utf-8'))
        hit = 0
        for h in n.get('horses', []):
            r = by_name.get(h['name'])
            if r:
                h['num'] = r['num']
                h['gate'] = r['gate']
                hit += 1
        # 馬番順にソート + listOrder振り直し
        n['horses'].sort(key=lambda h: h.get('num') or 999)
        for i, h in enumerate(n['horses'], 1):
            h['listOrder'] = i
        # ステータス更新
        if n.get('dataStatus') == 'preparation':
            n['dataStatus'] = 'bracket-fixed'
        notes.write_text(json.dumps(n, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'  race-notes: {hit}/{len(n["horses"])} 馬マッチ / dataStatus={n.get("dataStatus")}')


if __name__ == '__main__':
    for rd, rn in RACE_MAP:
        update_race(rd, rn)
    print('\n完了。枠順確定後はこのスクリプトを実行するだけ。')
