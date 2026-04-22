#!/usr/bin/env python3
"""
Stride JSON → race-notes 流し込みスクリプト
===============================================
金曜20時にStrideが出揃ったら:
    python3 scripts/fetch_stride.py --all --date 20260425
    python3 scripts/apply_stride_factor.py
    python3 scripts/generate_bets.py
の三連打で「最終結論」状態まで一気に進める。

入力:
  scripts/stride_cache/{YYYYMMDD}-{venueSlug}-{NN}r.json  (fetch_stride.py出力)

出力:
  docs/data/race-notes/{YYYY-MM-DD}-{venueSlug}-{N}r.json の各馬に:
    - lapFactors     (strideGeneral.paperVerdict → grade)
    - gaikyuFactor   (stableBokujoHit or horseBokujoHit → grade)
    - strideGeneral  (参考保存: 合計値順位・信頼度・脚質指数ほか)
    - strideTenkai   (参考保存: 展開・先走力・追走力ほか)
    - strideJockey   (参考保存: 騎手タイプ・騎手指数ほか)
    - strideBody     (参考保存: 体型・特記・種牡馬ヒット率ほか)
    - strideTraining (参考保存: 追い切り・坂路・仕上がりほか)
    - stridePaddock  (参考保存: パドック採点・ライザーほか)

race.dataStatus:
  preparation / bracket-fixed → lap-partial / lap-fixed

ファクター→Grade変換ルール:
  lapFactors:
    paperVerdict = ピッタリ → S
    paperVerdict = Ｖ/V     → A
    paperVerdict = カスリ   → B
    paperVerdict = 空/null  → reliability フォールバック
      reliability = ＡＡ     → A
      reliability = Ａ       → B
      reliability = Ｂ/Ｃ    → C
      reliability = Ｄ       → D
      else                   → C

  gaikyuFactor:
    horseBokujoHit (visit≥2あるとき) or stableBokujoHit:
      ≥50%  → S
      40-49 → A
      30-39 → B
      20-29 → C
      <20   → D

既存 gaikyuFactor (source='individual') は上書き前に gaikyuFactorIndividual に退避。

Usage:
  python3 scripts/apply_stride_factor.py                  # 4/25-26 三重賞を一括
  python3 scripts/apply_stride_factor.py --race 2026-04-25-tokyo-11r
  python3 scripts/apply_stride_factor.py --all-on 20260419  # 4/19全36R一括(検証用)
  python3 scripts/apply_stride_factor.py --dry-run        # 書き込みなし
"""
import json
import re
import argparse
from pathlib import Path

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')
CACHE = BASE / 'scripts/stride_cache'
NOTES = BASE / 'docs/data/race-notes'

# デフォルト対象 (4/25-26 週末三重賞)
RACE_MAP = [
    # (race_notes_slug, stride_cache_slug)
    ('2026-04-25-tokyo-11r',   '20260425-tokyo-11r'),
    ('2026-04-26-tokyo-11r',   '20260426-tokyo-11r'),
    ('2026-04-26-kyoto-11r',   '20260426-kyoto-11r'),
]


# ── Grade変換 ────────────────────────────────────────
VERDICT_TO_GRADE = {
    'ピッタリ': 'S',
    'Ｖ':      'A',
    'V':       'A',
    'カスリ':  'B',
    '':        None,
    None:      None,
}


def reliability_to_grade(s):
    if not s:
        return 'C'
    s = str(s).strip()
    # 全角優先
    if 'ＡＡ' in s or 'AA' in s:  return 'A'
    if s in ('Ａ', 'A'):          return 'B'
    if s in ('Ｂ', 'B'):          return 'C'
    if s in ('Ｃ', 'C'):          return 'C'
    if s in ('Ｄ', 'D'):          return 'D'
    return 'C'


def lap_grade(stride_general):
    if not stride_general:
        return 'C', 'no-data'
    verdict = stride_general.get('paperVerdict')
    g = VERDICT_TO_GRADE.get(verdict)
    if g is not None:
        return g, f'verdict={verdict}'
    # フォールバック: 信頼度
    rel = stride_general.get('reliability')
    return reliability_to_grade(rel), f'reliability={rel}'


def parse_pct(s):
    if s is None:
        return None
    m = re.search(r'(\d+(?:\.\d+)?)', str(s))
    return float(m.group(1)) if m else None


def pct_to_grade(pct):
    if pct is None:
        return None
    if pct >= 50: return 'S'
    if pct >= 40: return 'A'
    if pct >= 30: return 'B'
    if pct >= 20: return 'C'
    return 'D'


def gaikyu_grade(stride_gaikyu):
    """Returns (grade, source_key, pct)"""
    if not stride_gaikyu:
        return 'C', 'no-data', None
    horse = parse_pct(stride_gaikyu.get('horseBokujoHit'))
    stable = parse_pct(stride_gaikyu.get('stableBokujoHit'))
    visit = stride_gaikyu.get('visit') or 0
    # 個体ヒット率があり訪問2回以上 → 個体優先
    if horse is not None and visit >= 2:
        return (pct_to_grade(horse) or 'C'), 'horseBokujoHit', horse
    if stable is not None:
        return (pct_to_grade(stable) or 'C'), 'stableBokujoHit', stable
    return 'C', 'no-hit-data', None


# ── 馬名正規化 ────────────────────────────────────────
NAME_RE = re.compile(r'[\s　]+')


def norm_name(s):
    if not s:
        return ''
    return NAME_RE.sub('', s)


# ── メイン処理 ────────────────────────────────────────
def apply_to_race(rn_slug, cache_slug, dry_run=False):
    notes_path = NOTES / f'{rn_slug}.json'
    cache_path = CACHE / f'{cache_slug}.json'

    if not notes_path.exists():
        print(f'  ⚠ race-notes不在: {notes_path.name}')
        return None
    if not cache_path.exists():
        print(f'  ⚠ stride_cache不在: {cache_path.name}')
        return None

    notes = json.loads(notes_path.read_text(encoding='utf-8'))
    cache = json.loads(cache_path.read_text(encoding='utf-8'))

    cache_horses = {norm_name(h.get('name')): h for h in cache.get('horses', [])}
    horses = notes.get('horses', [])

    # 旧SABCスキーマ(dict)はスキップ。v2-rel-lapの新スキーマ(list)だけを処理する
    if not isinstance(horses, list):
        print(f'  ⏭ スキップ (旧SABCスキーマ dict形式): {notes_path.name}')
        return None

    hit = 0
    lap_grade_hist = {'S': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0}
    gai_grade_hist = {'S': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0}

    for h in horses:
        sh = cache_horses.get(norm_name(h.get('name')))
        if not sh:
            continue
        hit += 1

        sg = sh.get('strideGeneral') or {}
        st = sh.get('strideTenkai') or {}
        sj = sh.get('strideJockey') or {}
        sgai = sh.get('gaikyuFactor') or {}
        sbody = sh.get('body') or {}
        strn = sh.get('training') or {}
        spad = sh.get('paddock') or {}

        # ── lapFactors ──
        lgrade, lwhy = lap_grade(sg)
        h['lapFactors'] = {
            'lapChar':       sg.get('lapAdaptation'),
            'strideLapChar': sg.get('lapAdaptation'),
            'paperVerdict':  sg.get('paperVerdict'),
            'SAV':           sg.get('SAV'),
            'reliability':   sg.get('reliability'),
            'grade':         lgrade,
            'source':        'stride-v1',
            'note':          lwhy,
        }
        lap_grade_hist[lgrade] = lap_grade_hist.get(lgrade, 0) + 1

        # ── gaikyuFactor ──
        ggrade, gwhy, gpct = gaikyu_grade(sgai)
        prev = h.get('gaikyuFactor')
        # 既存の個体ベース成績は退避 (source='individual' と明示されているものだけ)
        if prev and prev.get('source') == 'individual':
            h['gaikyuFactorIndividual'] = prev
        h['gaikyuFactor'] = {
            'stable':          sgai.get('stable'),
            'bokujo':          sgai.get('bokujo'),
            'visit':           sgai.get('visit'),
            'stableBokujoHit': sgai.get('stableBokujoHit'),
            'horseBokujoHit':  sgai.get('horseBokujoHit'),
            'grade':           ggrade,
            'source':          'stride-v1',
            'note':            f'{gwhy} ({gpct}%)' if gpct is not None else gwhy,
        }
        gai_grade_hist[ggrade] = gai_grade_hist.get(ggrade, 0) + 1

        # ── 参考ブロック (Strideの生データを保持) ──
        h['strideGeneral']  = sg or None
        h['strideTenkai']   = st or None
        h['strideJockey']   = sj or None
        h['strideBody']     = sbody or None
        h['strideTraining'] = strn or None
        h['stridePaddock']  = spad or None

        # Stride由来の num/gate/expectedOdds がまだ空なら埋める
        if h.get('num') is None and sh.get('num') is not None:
            h['num'] = sh['num']
        if h.get('gate') is None and sh.get('gate') is not None:
            h['gate'] = sh['gate']
        if h.get('expectedOdds') is None and sh.get('expectedOdds') is not None:
            h['expectedOdds'] = sh['expectedOdds']
        if h.get('ninki') is None and sh.get('ninki') is not None:
            h['ninki'] = sh['ninki']

    # dataStatus更新
    ready = hit
    total = len(horses)
    ratio = ready / total if total else 0
    prev_status = notes.get('dataStatus')
    if ratio >= 0.9:
        if prev_status in ('preparation', None):
            notes['dataStatus'] = 'lap-partial'
        elif prev_status == 'bracket-fixed':
            notes['dataStatus'] = 'lap-fixed'
        # lap-partial / lap-fixed / final は据置

    # stride適用メタ
    notes['strideApplied'] = {
        'appliedAt':   cache.get('meta', {}).get('fetchedAt'),
        'cacheFile':   cache_path.name,
        'matchHorses': f'{hit}/{total}',
        'lapGrades':   lap_grade_hist,
        'gaikyuGrades': gai_grade_hist,
    }

    if not dry_run:
        notes_path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'  {rn_slug}: {hit}/{total}頭 流し込み')
    print(f'    lap grades:    S={lap_grade_hist["S"]} A={lap_grade_hist["A"]} B={lap_grade_hist["B"]} C={lap_grade_hist["C"]} D={lap_grade_hist["D"]}')
    print(f'    gaikyu grades: S={gai_grade_hist["S"]} A={gai_grade_hist["A"]} B={gai_grade_hist["B"]} C={gai_grade_hist["C"]} D={gai_grade_hist["D"]}')
    print(f'    dataStatus: {prev_status} → {notes["dataStatus"]}')

    return {'hit': hit, 'total': total, 'lap': lap_grade_hist, 'gaikyu': gai_grade_hist}


def list_cache_for_date(yyyymmdd):
    """指定日の全cacheを (rn_slug, cache_slug) ペアで返す。"""
    pairs = []
    for p in sorted(CACHE.glob(f'{yyyymmdd}-*-*r.json')):
        m = re.match(r'^(\d{8})-([a-z]+)-(\d{2})r$', p.stem)
        if not m:
            continue
        d, venue, rnn = m.group(1), m.group(2), m.group(3)
        # race-notesスラッグは R のゼロパディングを外す
        r_int = int(rnn)
        date_iso = f'{d[:4]}-{d[4:6]}-{d[6:8]}'
        rn_slug = f'{date_iso}-{venue}-{r_int}r'
        pairs.append((rn_slug, p.stem))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--race',     help='単一レース (rn_slug) だけ処理')
    ap.add_argument('--all-on',   help='指定日 (YYYYMMDD) のcache全てを処理')
    ap.add_argument('--dry-run',  action='store_true', help='書き込みスキップ')
    args = ap.parse_args()

    # 対象ペア決定
    if args.race:
        # --race だけ指定。キャッシュ側のslugはrace-notes slugから生成
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})-([a-z]+)-(\d+)r$', args.race)
        if not m:
            print(f'エラー: --race は 2026-04-25-tokyo-11r 形式で指定してください')
            return
        y, mo, d, venue, rnum = m.groups()
        cache_slug = f'{y}{mo}{d}-{venue}-{int(rnum):02d}r'
        pairs = [(args.race, cache_slug)]
    elif args.all_on:
        pairs = list_cache_for_date(args.all_on)
        if not pairs:
            print(f'⚠ {args.all_on} のキャッシュが見つかりません')
            return
    else:
        pairs = RACE_MAP

    print(f'=== apply_stride_factor.py ===')
    print(f'対象: {len(pairs)} レース')
    if args.dry_run:
        print('[DRY RUN モード: 書き込みなし]')
    print()

    results = []
    for rn, cs in pairs:
        r = apply_to_race(rn, cs, dry_run=args.dry_run)
        if r:
            results.append((rn, r))

    # サマリ
    print(f'\n=== 完了: {len(results)}/{len(pairs)} ===')
    total_hit = sum(r['hit'] for _, r in results)
    total_all = sum(r['total'] for _, r in results)
    print(f'マッチ合計: {total_hit}/{total_all}頭')


if __name__ == '__main__':
    main()
