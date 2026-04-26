#!/usr/bin/env python3
"""
build_day_pipeline.py — 1日分の全レース race-notes を一括構築

netkeiba shutuba_past.html から:
  - レース情報（名・距離・場・天候・馬場）
  - 全馬データ（馬名/枠番/馬番/父/母父/騎手/厩舎/性齢/斤量/前走）
を取得し、race-notes JSON を自動生成。

Usage:
  python3 scripts/build_day_pipeline.py --day 2026-04-25
"""
import urllib.request, re, json, sys, argparse, time
from pathlib import Path

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'

VENUE_CODE = {'sapporo':'01','hakodate':'02','fukushima':'03','niigata':'04','tokyo':'05','nakayama':'06','chukyo':'07','kyoto':'08','hanshin':'09','kokura':'10'}
VENUE_KAI = {  # day → {venue: (kai, day_in_kai)}  ※既知データから定義
    '2026-04-25': {'kyoto':('03','01'), 'tokyo':('02','01'), 'fukushima':('01','05')},
    '2026-04-26': {'kyoto':('03','02'), 'tokyo':('02','02'), 'fukushima':('01','06')},
}


def fetch_html(race_id):
    url = f'https://race.netkeiba.com/race/shutuba_past.html?race_id={race_id}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('euc-jp', errors='replace')


def parse_race_info(html, race_id):
    """レース情報パース"""
    info = {'raceId': race_id}
    # title から レース名取得
    t = re.search(r'<title>([^<]+?)\s*5走表示', html)
    name = t.group(1).strip() if t else ''
    # title 内の "(G1)" 等抽出
    grade_m = re.search(r'\(([G123L]+|OP|3勝|2勝|1勝|未勝利|新馬)\)', name)
    info['name'] = re.sub(r'\([^)]+\)', '', name).strip()
    info['grade'] = grade_m.group(1) if grade_m else ''
    # 場・R番抽出
    venue_r = re.search(r'(\d+)月(\d+)日\s+(\S+?)(\d+)R', t.group(1) if t else '')
    if venue_r:
        info['venue'] = venue_r.group(3)
        info['raceNumber'] = int(venue_r.group(4))
    # コース情報
    rd = re.search(r'<div class="RaceData01">(.*?)</div>', html, re.S)
    if rd:
        txt = re.sub(r'<[^>]+>', ' ', rd.group(1))
        txt = re.sub(r'\s+', ' ', txt).strip()
        # "09:55発走 / --> ダ1800m (右) / 天候:晴 / 馬場:稍"
        st = re.search(r'(\d+:\d+)発走', txt)
        if st: info['startTime'] = st.group(1)
        course = re.search(r'(芝|ダ)(\d+)m', txt)
        if course:
            info['kind'] = course.group(1)
            info['distance'] = course.group(2)
        weather = re.search(r'天候[:：]\s*(\S+)', txt)
        if weather: info['weather'] = weather.group(1)
        track = re.search(r'馬場[:：]\s*(\S+)', txt)
        if track: info['track'] = track.group(1)
    return info


def parse_horses(html):
    """全頭の出馬表データを抽出"""
    out = []
    rows = re.findall(r'<tr[^>]*class="HorseList"[^>]*>(.*?)</tr>', html, re.S)
    seen = set()
    for row in rows:
        gate = re.search(r'<td class="Waku\d+"[^>]*>(\d+)</td>', row)
        num  = re.search(r'<td class="Waku"[^>]*>(\d+)</td>', row)
        sire = re.search(r'<div class="Horse01[^"]*">([^<]+)</div>', row)
        name_m = re.search(r'<div class="Horse02">\s*<a[^>]*>\s*([^<\n]+?)\s*</a>', row)
        dam = re.search(r'<div class="Horse03">([^<]+)</div>', row)
        bms = re.search(r'<div class="Horse04">\(([^)]+)\)</div>', row)
        trainer_m = re.search(r'<div class="Horse05[^"]*">\s*<a[^>]*>([^<]+)</a>', row)
        jockey = None
        jt = re.search(r'<td class="Jockey">(.*?)</td>', row, re.S)
        kinryo = None
        if jt:
            j = re.search(r'<a[^>]*jockey[^>]*>([^<]+)</a>', jt.group(1))
            if j: jockey = j.group(1).strip()
            kg = re.search(r'<span>(\d+(?:\.\d+)?)</span>', jt.group(1))
            kinryo = kg.group(1) if kg else None
        barei = re.search(r'<span class="Barei"[^>]*>([^<]+)</span>', row)

        # 前走（最初のPast td）
        prev_name = prev_finish = prev_dist = prev_track = ''
        past_blocks = re.findall(r'<td[^>]*class="Past[^"]*"[^>]*>(.*?)</td>', row, re.S)
        if past_blocks:
            past = past_blocks[0]
            d01 = re.search(r'<div class="Data01">(.*?)</div>', past, re.S)
            if d01:
                ds = re.search(r'<span>([^<]+?)</span>', d01.group(1))
                if ds:
                    pd = ds.group(1).replace('&nbsp;', ' ').strip()
                    parts = pd.split()
                    if len(parts) >= 2:
                        prev_track = parts[-1]
                fn = re.search(r'<span class="Num">([^<]+)</span>', d01.group(1))
                if fn: prev_finish = fn.group(1).strip()
            d02 = re.search(r'<div class="Data02">(.*?)</div>', past, re.S)
            if d02:
                a = re.search(r'<a[^>]*>([^<]+?)(?:<span|</a>)', d02.group(1), re.S)
                if a: prev_name = a.group(1).strip()
            d05 = re.search(r'<div class="Data05">([^<]+)', past)
            if d05:
                txt = re.sub(r'\s+', ' ', d05.group(1)).strip()
                p = txt.split(' ', 1)
                if p: prev_dist = p[0]

        if not name_m: continue
        # 重複馬除外（同じ馬の異なるpast tdマッチ防止）
        nm = name_m.group(1).strip()
        if nm in seen: continue
        seen.add(nm)
        out.append({
            'name': nm,
            'gate': gate.group(1) if gate else '',
            'num': num.group(1) if num else '',
            'sire': sire.group(1).strip() if sire else '',
            'dam': dam.group(1).strip() if dam else '',
            'broodmareSire': bms.group(1).strip() if bms else '',
            'trainer': trainer_m.group(1).strip().split('・')[-1] if trainer_m else '',
            'jockey': jockey or '',
            'sexAge': barei.group(1).strip() if barei else '',
            'kinryo': kinryo or '',
            'prevName': prev_name,
            'prevFinish': prev_finish,
            'prevDist': prev_dist,
            'prevTrack': prev_track,
        })
    return out


def race_key(day, venue, race_num):
    return f'{day}-{venue}-{race_num}r'


def build_one(day, venue, race_num, race_id, force=False):
    key = race_key(day, venue, race_num)
    path = RN_DIR / f'{key}.json'

    if path.exists() and not force:
        d = json.load(open(path))
    else:
        d = {}

    try:
        html = fetch_html(race_id)
    except Exception as e:
        return False, f'fetch失敗: {e}'

    info = parse_race_info(html, race_id)
    horses = parse_horses(html)

    if not horses:
        return False, '出馬表parseゼロ'

    # 既存race情報があればmerge、なければ新規
    race = d.setdefault('race', {})
    if not race.get('name') and info.get('name'): race['name'] = info['name']
    if not race.get('grade') and info.get('grade'): race['grade'] = info['grade']
    if not race.get('kind') and info.get('kind'): race['kind'] = info['kind']
    if not race.get('distance') and info.get('distance'): race['distance'] = info['distance']
    if not race.get('weather') and info.get('weather'): race['weather'] = info['weather']
    if not race.get('track') and info.get('track'): race['track'] = info['track']
    if not race.get('venue') and info.get('venue'): race['venue'] = info['venue']
    if not race.get('raceNumber') and info.get('raceNumber'): race['raceNumber'] = info['raceNumber']

    # presentation 保護
    pres = d.setdefault('presentation', {})
    pres['raceId'] = race_id
    if not pres.get('startTime') and info.get('startTime'): pres['startTime'] = info['startTime']
    if not pres.get('meta'):
        pres['meta'] = f"{info.get('venue','')}{info.get('raceNumber','')}R ／ {info.get('kind','')}{info.get('distance','')}m ／ {len(horses)}頭"

    # horses[] マージ（既存があれば優先）
    horses_top = d.setdefault('horses', [])
    by_name_top = {h.get('name'): h for h in horses_top}
    for s in horses:
        existing = by_name_top.get(s['name'])
        if existing:
            for k, v in s.items():
                if not existing.get(k) and v:
                    existing[k] = v
        else:
            horses_top.append(s)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return True, f'{race.get("name","?")} {len(horses)}頭'


def build_day(day):
    venues = VENUE_KAI.get(day)
    if not venues:
        print(f'⚠ VENUE_KAI に {day} 未定義')
        return
    total = 0; ok = 0
    for venue, (kai, day_in_kai) in venues.items():
        venue_cd = VENUE_CODE[venue]
        for r in range(1, 13):
            race_id = f'2026{venue_cd}{kai}{day_in_kai}{r:02d}'
            success, msg = build_one(day, venue, r, race_id)
            mark = '✓' if success else '✗'
            print(f'  {mark} {venue:<10} R{r:>2} ({race_id}): {msg}')
            total += 1
            if success: ok += 1
            time.sleep(0.5)  # netkeiba 負荷配慮
    print(f'\n  合計: {ok}/{total}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True, help='例: 2026-04-25')
    args = ap.parse_args()
    build_day(args.day)
