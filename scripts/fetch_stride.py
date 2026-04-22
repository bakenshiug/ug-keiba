#!/usr/bin/env python3
"""
ストライドHTML → 構造化JSON 変換スクリプト
============================================
公式データビュアー(https://stride.get-luck.jp/member/race_viewer_test.php)
のレースページをHTTP取得し、1レース分の全データを8テーブルから構造化して
JSONに保存する。TSV手打ちで入力していた lapFactors や JRDB PDFで取っていた
gaikyuFactor をこれ1本でカバーする。

使用:
  # ローカルHTMLでテスト (皐月賞HTML=DL済み)
  python3 scripts/fetch_stride.py --html /tmp/stride_satsuki.html \
      --out scripts/stride_cache/20260419-nakayama-11r.json

  # 単一レース取得
  python3 scripts/fetch_stride.py --date 20260425 --racekey 05260411 --jo 0 \
      --idpm QcoyS7VNzhBMU

  # 当日全レース取得 (最初に1ページ取って場一覧を把握 → 全場・全Rループ)
  python3 scripts/fetch_stride.py --date 20260425 --idpm QcoyS7VNzhBMU --all

出力:
  scripts/stride_cache/{racedate}-{venue}-{R}r.json
  {
    "meta": {
      "racedate": "20260419", "racekey": "06263811",
      "venue": "中山", "r": 11,
      "url": "...", "fetchedAt": "2026-04-22T19:30:00"
    },
    "horses": [
      {
        "num": 1, "name": "...", "jockey": "...", "expectedOdds": 8.5,
        "lapFactors": { strideLapChar, paperVerdict, SAV, reliability, taste,
                        STindex, shiagari, totalRank, ... },
        "strideTenkai": { delayPct, sensoryoku, tsuisoroku, ... },
        "strideJockey": { type, index, comment, courseHit, ... },
        "gaikyuFactor": { stable, bokujo, visit, bokujoHit, ... },
        "body":    { sex, age, specialTraits[], sire, sireHit, ... },
        "training":{ weekBeforeOi, finalOi, shiagari, pattern, ... },
        "paddock": { ... },   # Table 6
        "result":  { ... }    # Table 7 (レース後のみ)
      },
      ...
    ]
  }
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')
CACHE_DIR = BASE / 'scripts/stride_cache'
BASE_URL = 'https://stride.get-luck.jp/member/race_viewer_test.php'

# racekey 先頭2桁 → 場名
VENUE_CODE = {
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
    '05': '東京', '06': '中山', '07': '中京', '08': '京都',
    '09': '阪神', '10': '小倉',
}
VENUE_SLUG = {
    '札幌': 'sapporo', '函館': 'hakodate', '福島': 'fukushima', '新潟': 'niigata',
    '東京': 'tokyo',   '中山': 'nakayama',  '中京': 'chukyo',    '京都': 'kyoto',
    '阪神': 'hanshin', '小倉': 'kokura',
}

# 8テーブルの section 名
SECTION_NAMES = ['general', 'tenkai', 'jockey', 'gaikyu',
                 'body', 'training', 'paddock', 'result']


# ── HTTP ────────────────────────────────────────────────

def build_url(racedate, racekey, jo, idpm):
    q = {'racedate': racedate, 'racekey': racekey, 'jo': jo, 'idpm': idpm}
    return f'{BASE_URL}?{urlencode(q)}'


def fetch_html(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; ug-keiba/1.0)',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    # サイトは meta charset=shift_jis と宣言するが実体は UTF-8
    return raw.decode('utf-8', errors='replace')


# ── パース ──────────────────────────────────────────────

def strip_tags(html):
    t = re.sub(r'<[^>]+>', ' ', html)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def norm_header(s):
    """ヘッダー専用正規化: '前3F 順位'→'前3F順位', '騎手 タイプ'→'騎手タイプ'
    改行起因で混入したスペースを除去する。日本語は単語区切りなくてOK。
    """
    return re.sub(r'[\s　]+', '', s)


def parse_table(table_html):
    """<table>...</table> → (headers, rows)"""
    rows_html = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    parsed = []
    for row in rows_html:
        cells = re.findall(r'<(th|td)[^>]*>(.*?)</\1>', row, re.DOTALL)
        parsed.append([strip_tags(c[1]) for c in cells])
    if not parsed:
        return [], []
    return parsed[0], parsed[1:]


def parse_gate(row_html):
    """td class="waku_N" から枠番を取る"""
    m = re.search(r'class="waku_(\d+)"', row_html)
    return int(m.group(1)) if m else None


def parse_race_html(html):
    """レースHTMLから8テーブル分を抽出し、馬番→section別辞書にまとめる"""
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if len(tables) < 7:
        print(f'  warn: {len(tables)} tables found (expected 8)', file=sys.stderr)

    # 馬番→section別dict
    horses = {}
    for ti, table in enumerate(tables):
        section = SECTION_NAMES[ti] if ti < len(SECTION_NAMES) else f'table{ti}'
        headers, rows = parse_table(table)
        # rows の raw HTML も列ごとに取得 (枠番用)
        row_htmls = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL)[1:]
        for r_i, r in enumerate(rows):
            if len(r) < 2:
                continue
            num_raw = r[1].strip()
            num_clean = num_raw.lstrip('0') or num_raw
            if not num_clean.isdigit():
                continue
            num = int(num_clean)
            h = horses.setdefault(num, {'num': num})
            # 名前を最初に見つけたところで固定
            if 'name' not in h and len(r) > 3:
                h['name'] = r[3]
            # 枠番 (Table 0の waku_N クラスから)
            if ti == 0 and 'gate' not in h:
                gate = parse_gate(row_htmls[r_i])
                if gate:
                    h['gate'] = gate
            # section
            sect = h.setdefault(section, {})
            for i, v in enumerate(r):
                if i >= len(headers):
                    break
                hname = norm_header(headers[i])
                if hname and v:
                    sect[hname] = v
    return horses


# ── 値変換 ──────────────────────────────────────────────

def num(s, kind=float):
    if s is None or s == '':
        return None
    try:
        # '10 %' や '62 (3)' のような表記から先頭数値を抜く
        m = re.match(r'-?\d+\.?\d*', s.strip())
        if not m:
            return None
        return kind(m.group(0))
    except (ValueError, AttributeError):
        return None


def normalize_horse(h):
    """8テーブル生データ→race-notes互換のフラットな1馬辞書"""
    g  = h.get('general', {})
    t  = h.get('tenkai', {})
    j  = h.get('jockey', {})
    ga = h.get('gaikyu', {})
    b  = h.get('body', {})
    tr = h.get('training', {})
    p  = h.get('paddock', {})
    rs = h.get('result', {})

    traits = [b.get('特記１'), b.get('特記２'), b.get('特記３')]
    traits = [x for x in traits if x]

    out = {
        'num':          h['num'],
        'gate':         h.get('gate'),
        'name':         h.get('name', ''),
        'jockey':       g.get('騎手') or j.get('騎手'),
        'expectedOdds': num(g.get('基準オッズ'), float),
        'ninki':        num(g.get('人気'), int),

        # === ストライド総合 (現行 lapFactors を大幅拡張する元ネタ) ===
        'strideGeneral': {
            'lapAdaptation': g.get('ラップ適性'),       # 超高速持続 / 高速バランス / 中速瞬発 / ...
            'paperVerdict':  g.get('ラップキャラ'),      # ピッタリ / カスリ / V / 空
            'SAV':           num(g.get('SAV'), int),
            'reliability':   g.get('信頼度'),            # ＡＡ / Ａ / Ｂ / Ｃ / Ｄ
            'taste':         g.get('妙味度'),            # Ｓ / Ａ / Ｂ / Ｃ / Ｄ
            'tenkai':        num(g.get('展開'), int),
            'STindex':       num(g.get('ST指数'), int),
            'shiagari':      num(g.get('仕上指数'), int),
            'total':         num(g.get('合計値'), int),
            'totalRank':     num(g.get('合計値順位'), int),
        },

        # === 展開パラメータ ===
        'strideTenkai': {
            'delayPct':    t.get('出遅率'),
            'sensoryoku':  t.get('先行力'),
            'tsuisoroku':  t.get('追走力'),
            'jikyuroku':   t.get('持久力'),
            'jizokuroku':  t.get('持続力'),
            'shunpatsu':   t.get('瞬発力'),
            'f3Rank':      num(t.get('前3F順位'), int),
            'shoubuRank':  num(t.get('勝負所順位'), int),
            'gmaeRank':    num(t.get('Ｇ前順位'), int),
        },

        # === 騎手 ===
        'strideJockey': {
            'type':        j.get('騎手タイプ'),
            'index':       num(j.get('騎手指数'), int),
            'comment':     j.get('騎手コメント'),
            'courseHit':   j.get('当該コース複勝率'),
        },

        # === 外厩 (JRDB PDFから置換) ===
        'gaikyuFactor': {
            'stable':            ga.get('厩舎') or tr.get('厩舎'),
            'bokujo':            ga.get('最近放牧先'),
            'visit':             num(ga.get('何走目'), int),
            'stableBokujoHit':   ga.get('厩舎×外厩複勝率'),
            'horseBokujoHit':    ga.get('馬×外厩複勝率'),
            'source':            'stride-v1',
        },

        # === 馬体・血統 (特記3つ +父+血統成績) ===
        'body': {
            'sex':           b.get('性'),
            'age':           num(b.get('齢'), int),
            'weight':        num(b.get('斤量'), float),
            'foreleg':       b.get('前肢'),
            'hindleg':       b.get('後肢'),
            'hoof':          b.get('蹄'),
            'heavyAptitude': b.get('重適性'),
            'specialTraits': traits,               # 最大3つ (JRDBフル版より少ない)
            'sire':          b.get('父馬名'),
            'sireHit':       b.get('血統×複勝率'),
        },

        # === 調教 ===
        'training': {
            'weekBeforeOi':  tr.get('１週前追切'),
            'finalOi':       tr.get('最終追切'),
            'shiagari':      num(tr.get('仕上指数'), int),
            'pattern':       tr.get('調教パターン'),
            'courseStable':  tr.get('コース×厩舎複勝率'),
            'patternStable': tr.get('調教P×厩舎複勝率'),
        },

        # === パドック・直前 ===
        'paddock': {
            'paddock':   p.get('パドック'),
            'odds':      p.get('オッズ'),
            'body':      p.get('馬体'),
            'mood':      p.get('気配'),
            'state':     p.get('状態'),
            'leg':       p.get('脚元'),
            'gear':      p.get('馬具'),
            'turf':      p.get('馬場'),
            'style':     p.get('脚質'),
            'sumVal':    num(p.get('合算値'), int),
            'riser':     p.get('上昇馬'),
        },

        # === レース後結果 (空でもOK) ===
        'result': {
            'chakujun':   num(g.get('着順'), int),
            'time':       rs.get('タイム'),
            'chakusa':    rs.get('着差'),
            'agari':      rs.get('上がり'),
            'actualOdds': num(rs.get('オッズ'), float),
            'actualNinki':num(rs.get('人気'), int),
            'weightDelta':rs.get('馬体重'),
            'corners':    {'1C': rs.get('1C'), '2C': rs.get('2C'), '3C': rs.get('3C'), '4C': rs.get('4C')},
        },
    }
    return out


# ── 本体 ────────────────────────────────────────────────

def extract_race_meta(html, racedate, racekey, url):
    """HTML / racekey / URL からメタ情報を決定"""
    venue_code = racekey[:2]
    venue = VENUE_CODE.get(venue_code, f'?{venue_code}')
    r_num = int(racekey[-2:])
    return {
        'racedate':  racedate,
        'racekey':   racekey,
        'venue':     venue,
        'venueSlug': VENUE_SLUG.get(venue, venue_code),
        'r':         r_num,
        'url':       url,
        'fetchedAt': datetime.now().isoformat(timespec='seconds'),
    }


def extract_same_day_links(html):
    """インデックスナビから当日の全場・全レースのリンクを抽出"""
    links = re.findall(
        r'href="(race_viewer_test\.php\?[^"]+)"[^>]*>([^<]{1,40})</a>',
        html,
    )
    seen = set()
    out = []
    for url, label in links:
        if 'racekey=' not in url:
            continue
        m = re.search(r'racedate=(\d{8})&racekey=(\d{8})[^"]*jo=(\d)', url)
        if not m:
            continue
        date, key, jo = m.groups()
        if key in seen:
            continue
        seen.add(key)
        out.append({
            'racedate': date,
            'racekey':  key,
            'jo':       int(jo),
            'label':    label.strip(),
            'url':      url,
        })
    return out


def save_race(meta, horses, out_path=None):
    """構造化JSONを保存"""
    if out_path is None:
        CACHE_DIR.mkdir(exist_ok=True)
        fname = f"{meta['racedate']}-{meta['venueSlug']}-{meta['r']:02d}r.json"
        out_path = CACHE_DIR / fname
    else:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'meta':    meta,
        'horses':  horses,
    }
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return out_path


def process_html(html, racedate, racekey, url):
    raw = parse_race_html(html)
    horses = [normalize_horse(h) for num, h in sorted(raw.items())]
    meta = extract_race_meta(html, racedate, racekey, url)
    return meta, horses


def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                  description=__doc__)
    ap.add_argument('--html', help='Local HTML file (offline test)')
    ap.add_argument('--date', help='YYYYMMDD')
    ap.add_argument('--racekey', help='8桁racekey (e.g. 06263811)')
    ap.add_argument('--jo', type=int, default=0)
    ap.add_argument('--idpm', help='ストライドセッションID')
    ap.add_argument('--all', action='store_true', help='当日全場・全レース一括取得')
    ap.add_argument('--out', help='出力パス (デフォルト: stride_cache/{date}-{venue}-{r}r.json)')
    ap.add_argument('--sleep', type=float, default=1.0, help='request間スリープ秒')
    args = ap.parse_args()

    # --- Mode 1: ローカルHTMLテスト
    if args.html:
        html = Path(args.html).read_text(encoding='utf-8', errors='replace')
        # バイト読みで UTF-8 でも壊れないよう
        raw_bytes = Path(args.html).read_bytes()
        try:
            html = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            html = raw_bytes.decode('cp932', errors='replace')
        racedate = args.date or re.search(r'(\d{8})', args.html).group(1) if re.search(r'(\d{8})', args.html) else '20260419'
        racekey = args.racekey or '06263811'
        url = f'file://{args.html}'
        meta, horses = process_html(html, racedate, racekey, url)
        path = save_race(meta, horses, out_path=args.out)
        print(f'→ {path}')
        print(f'  {len(horses)} 頭 / 場={meta["venue"]}{meta["r"]}R')
        return

    # --- Mode 2: 単一レース取得
    if args.racekey and args.date and args.idpm:
        url = build_url(args.date, args.racekey, args.jo, args.idpm)
        print(f'fetching {url[:80]}...')
        html = fetch_html(url)
        meta, horses = process_html(html, args.date, args.racekey, url)
        path = save_race(meta, horses, out_path=args.out)
        print(f'→ {path}')
        print(f'  {len(horses)} 頭 / 場={meta["venue"]}{meta["r"]}R')
        return

    # --- Mode 3: 当日全レース
    if args.all and args.date and args.idpm:
        # 最初に1レース(=とりあえず中山1R)を叩いてナビから全レース一覧を取得
        seed_key = f'06{args.date[2:4]}{int(args.date[4:6])}{int(args.date[6:8]):d}01'
        # ↑ 強引な組立。失敗したら手で racekey を指定して再実行
        seed_url = build_url(args.date, seed_key, 0, args.idpm)
        try:
            seed_html = fetch_html(seed_url)
        except Exception as e:
            print(f'seed fetch failed ({e}). --racekey を直接指定してください', file=sys.stderr)
            sys.exit(1)

        races = extract_same_day_links(seed_html)
        if not races:
            print('レース一覧を抽出できず。HTML構造変更の可能性', file=sys.stderr)
            sys.exit(1)
        print(f'当日 {len(races)} レースを取得します')
        for i, r in enumerate(races, 1):
            url = build_url(r['racedate'], r['racekey'], r['jo'], args.idpm)
            try:
                html = fetch_html(url)
            except Exception as e:
                print(f'  [{i}/{len(races)}] {r["label"]} ✗ {e}')
                continue
            meta, horses = process_html(html, r['racedate'], r['racekey'], url)
            path = save_race(meta, horses)
            print(f'  [{i}/{len(races)}] {meta["venue"]}{meta["r"]:02d}R ({len(horses)}頭) → {path.name}')
            time.sleep(args.sleep)
        return

    ap.print_help()


if __name__ == '__main__':
    main()
