#!/usr/bin/env python3
"""
⚡スピード指数1位抽出（エヒト型＝過去最高点突出馬）
- 既存race-notesのlapFactors.sp(5走分)から過去最高値を算出
- 前走最高値（右肩上がり型）もフラグで検出
- 致命ワード除外フィルタ付き
"""
import json
import os

NOTES_DIR = '/Users/buntawakase/Desktop/ug-keiba/docs/data/race-notes'
FILES = [
    ('WIN1 観月橋S',  '2026-04-25-kyoto-10r.json'),
    ('WIN2 鎌倉S',    '2026-04-25-tokyo-10r.json'),
    ('WIN3 福島TV',   '2026-04-25-fukushima-11r.json'),
    ('WIN4 天王山S',  '2026-04-25-kyoto-11r.json'),
    ('WIN5 青葉賞',   '2026-04-25-tokyo-11r.json'),
]

def is_fatal(h):
    """言霊致命ワード判定"""
    d = h.get('danwaGrade', {})
    if d.get('fatal', False):
        return True, d.get('fatalTag', d.get('reason', ''))
    # seiryu=Dも致命扱い
    sei = h.get('seiryu', {})
    if sei.get('grade') == 'D':
        return True, sei.get('reason', '')
    return False, None

def analyze(h):
    """スピード指数分析"""
    sp = [x for x in (h.get('lapFactors', {}).get('sp') or []) if x is not None]
    if not sp:
        return None
    peak = max(sp)
    peak_idx = sp.index(peak)  # 0=5走前, 4=前走
    last = sp[-1]
    # 右肩上がり判定: 直近3走の平均 > 古い2走の平均
    if len(sp) >= 5:
        recent = sum(sp[-3:]) / 3
        old = sum(sp[:2]) / 2
        ascending = recent > old + 2.0
    else:
        ascending = False
    # 前走=最高 判定
    prev_peak = (peak_idx == 4)
    # エヒト型: 過去最高点が直近3走より+3以上突出
    if len(sp) >= 5:
        recent_avg = sum(sp[-3:]) / 3
        ehito_gap = peak - recent_avg
    else:
        ehito_gap = 0
    return {
        'peak': peak,
        'last': last,
        'peak_age': 4 - peak_idx,  # 0=前走, 4=5走前
        'ascending': ascending,
        'prev_peak': prev_peak,
        'ehito_gap': ehito_gap,
        'sp': sp,
    }

def main():
    print('=' * 95)
    print('⚡スピード指数1位マトリクス（エヒト型=過去最高点）')
    print('=' * 95)
    results = {}
    for label, fname in FILES:
        path = os.path.join(NOTES_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            d = json.load(f)
        horses = d.get('horses', [])

        # 全馬分析
        scored = []
        for h in horses:
            a = analyze(h)
            if a is None:
                continue
            fatal, ftag = is_fatal(h)
            scored.append({
                'name': h.get('name'),
                'num': h.get('num'),
                'peak': a['peak'],
                'last': a['last'],
                'prev_peak': a['prev_peak'],
                'ehito_gap': a['ehito_gap'],
                'ascending': a['ascending'],
                'fatal': fatal,
                'ftag': ftag,
            })

        # ソート: peak降順
        scored.sort(key=lambda x: -x['peak'])
        top3_raw = scored[:3]
        # 致命除外1位
        clean = [s for s in scored if not s['fatal']]
        top1_clean = clean[0] if clean else None

        print(f'\n■ {label}')
        print(f'  {"馬名":<18s} peak  前走  前=P  エヒト  右肩  致命')
        print('  ' + '─' * 75)
        for s in scored[:6]:
            name = s['name'] or ''
            pp = '★' if s['prev_peak'] else ' '
            asc = '↗' if s['ascending'] else ' '
            fm = f"🔴{s['ftag'][:12]}" if s['fatal'] else ''
            print(f'  {name:<18s} {s["peak"]:5.1f} {s["last"]:5.1f}  {pp}  {s["ehito_gap"]:+5.1f}   {asc}   {fm}')

        if top1_clean:
            mark = '★前走最高' if top1_clean['prev_peak'] else ('↗右肩上がり' if top1_clean['ascending'] else '')
            print(f'  ▶ ⚡SP1位(致命除外): {top1_clean["name"]} peak{top1_clean["peak"]} {mark}')
        results[label] = top1_clean
    return results

if __name__ == '__main__':
    main()
