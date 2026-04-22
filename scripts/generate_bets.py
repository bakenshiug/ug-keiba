#!/usr/bin/env python3
"""
最終予想（買い目）生成スクリプト — 四神揃い版 (v2-shijin)
=====================================
使用: python3 scripts/generate_bets.py [--force]

入力:
  scripts/bet_config.json           - 点数/重み/タイブレーカー設定
  docs/data/race-notes/{race}.json  - 必須3ファクター + 任意神眼

  必須 (準備率チェック):
    🐉 relComment   (言霊・青龍)
    🐅 lapFactors   (ラップ・白虎)
    🐢 gaikyuFactor (外厩・玄武)
  任意 (スコア加点のみ、揃い率には非算入):
    🐦 shingan      (神眼・朱雀)

出力:
  docs/data/race-notes/{race}.json の race.finalBets に一括書き込み。

アルゴリズム:
  1) 総合スコア = 言霊×2.0 + 神眼×1.5 + ラップ×1.0 + 外厩×0.5
     Grade=S+5/A+3/B0/C-2/D-4 (shinganだけgrade無しでも他3つで動く)
  2) タイブレーカー: 言霊→神眼→ラップ→外厩 の重み付き得点、最後に想定OD低い方
  3) 単勝1点 (100円) = 総合1位
  4) 複勝1点 (100円) = 総合1位 (信頼補強)
  5) ワイド4頭BOX (600円=100円×6点) = 人気馬2頭 + 穴馬2頭 (理想バランス)
     - 人気プール: 想定OD<10         → 総合スコア順で上位2頭
     - 穴プール:   想定OD≥10 & score≥3 → 総合スコア順で上位2頭
     - 穴不足時は 3人気+1穴 / 4人気+0穴 にフォールバック
     - 人気不足 (稀) 時も自動で縮退
  6) 必須3ファクター揃い率 ≥ 90% で実行 (--force で強制)
"""
import json
import sys
import argparse
import itertools
from pathlib import Path
from datetime import datetime

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')

RACE_MAP = [
    ('2026-04-25-aobasho',  '2026-04-25-tokyo-11r'),
    ('2026-04-26-floras',   '2026-04-26-tokyo-11r'),
    ('2026-04-26-milers-c', '2026-04-26-kyoto-11r'),
]

# 必須ファクター (揃い率計算用)
FACTOR_KEYS_REQUIRED = ['relComment', 'lapFactors', 'gaikyuFactor']
# 全ファクター (スコア計算用) — shinganは動画なし重賞もあるため optional
FACTOR_KEYS_ALL = ['relComment', 'shingan', 'lapFactors', 'gaikyuFactor']


def load_config():
    return json.loads((BASE / 'scripts/bet_config.json').read_text(encoding='utf-8'))


def load_notes(rn):
    return json.loads((BASE / 'docs/data/race-notes' / f'{rn}.json').read_text(encoding='utf-8'))


def save_notes(rn, data):
    (BASE / 'docs/data/race-notes' / f'{rn}.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8'
    )


def has_all_required_factors(h):
    """必須3ファクター(言霊/ラップ/外厩)が揃っているか"""
    for k in FACTOR_KEYS_REQUIRED:
        v = h.get(k)
        if not v or not v.get('grade'):
            return False
    return True


def shingan_coverage(horses):
    """shingan factor を持つ頭数"""
    n = 0
    for h in horses:
        v = h.get('shingan') or {}
        if v.get('grade'):
            n += 1
    return n


def score_horse(h, cfg):
    gp = cfg['gradePoints']
    w = cfg['weights']
    total = 0.0
    bd = {}
    for k in FACTOR_KEYS_ALL:
        data = h.get(k) or {}
        grade = data.get('grade')
        pt = gp.get(grade, 0) if grade else 0
        weight = w.get(k, 1.0)
        weighted = pt * weight
        total += weighted
        bd[k] = {
            'grade': grade,
            'pt': pt,
            'weight': weight,
            'weighted': round(weighted, 2)
        }
    return round(total, 2), bd


def rank_horses(horses, cfg):
    scored = []
    for h in horses:
        total, bd = score_horse(h, cfg)
        scored.append({'h': h, 'score': total, 'breakdown': bd})
    tb = cfg.get('tiebreakerOrder', FACTOR_KEYS_ALL)
    scored.sort(key=lambda x: (
        -x['score'],
        -x['breakdown'][tb[0]]['weighted'] if len(tb) > 0 and tb[0] in x['breakdown'] else 0,
        -x['breakdown'][tb[1]]['weighted'] if len(tb) > 1 and tb[1] in x['breakdown'] else 0,
        -x['breakdown'][tb[2]]['weighted'] if len(tb) > 2 and tb[2] in x['breakdown'] else 0,
        -x['breakdown'][tb[3]]['weighted'] if len(tb) > 3 and tb[3] in x['breakdown'] else 0,
        x['h'].get('expectedOdds') if x['h'].get('expectedOdds') is not None else 9999,
    ))
    for i, s in enumerate(scored, 1):
        s['rank'] = i
    return scored


def pick_wide4_balanced(ranked, cfg):
    """
    目標: 人気馬2頭 + 穴馬2頭 の4頭BOX (バランス重視)
      人気プール: 想定OD<minOdds
      穴プール:   想定OD≥minOdds AND score≥minScore
    各プール内は ranked の並び (スコア+タイブレーカー) をそのまま使い上位2頭を取る。
    プールが埋まらないときは自動で縮退:
      穴1 → 3人気+1穴 / 穴0 → 4人気+0穴
      (人気<2は稀だが同様に穴で補う)
    return: (picks_sorted_by_rank, meta_dict)
    """
    if len(ranked) < 4:
        return ranked[:], {
            'composition':    'short',
            'ninkiCount':     0,
            'anaCount':       0,
            'fallback':       False,
            'note':           'horses<4',
        }

    ana_cfg = cfg.get('anaSlot', {})
    if not ana_cfg.get('enabled', True):
        top4 = ranked[:4]
        return top4, {
            'composition':    'top4-raw',
            'ninkiCount':     0,
            'anaCount':       0,
            'fallback':       False,
            'note':           'ana-logic-disabled',
        }

    min_odds = ana_cfg.get('minOdds', 10.0)
    min_score = ana_cfg.get('minScore', 3.0)

    # プール分離 (rank順は維持)
    ninki_pool = []
    ana_pool = []
    for s in ranked:
        od = s['h'].get('expectedOdds') or 0
        if od >= min_odds:
            if s['score'] >= min_score:
                ana_pool.append(s)
            # OD≥10 だが score 不足は選外 (両プールから除外)
        else:
            ninki_pool.append(s)

    target_ninki = 2
    target_ana = 2

    # 穴不足: 3+1 / 4+0 へ縮退
    if len(ana_pool) < target_ana:
        target_ana = len(ana_pool)
        target_ninki = min(len(ninki_pool), 4 - target_ana)
    # 人気不足 (稀): 穴で埋める
    if len(ninki_pool) < target_ninki:
        target_ninki = len(ninki_pool)
        target_ana = min(len(ana_pool), 4 - target_ninki)

    picks = ninki_pool[:target_ninki] + ana_pool[:target_ana]
    picks.sort(key=lambda s: s['rank'])

    composition = f'{target_ninki}ninki+{target_ana}ana'
    fallback = (target_ninki != 2 or target_ana != 2)

    return picks, {
        'composition':   composition,
        'ninkiCount':    target_ninki,
        'anaCount':      target_ana,
        'fallback':      fallback,
        'ninkiPoolSize': len(ninki_pool),
        'anaPoolSize':   len(ana_pool),
        'minOdds':       min_odds,
        'minScore':      min_score,
    }


def build_scoreboard(ranked):
    return [{
        'rank': s['rank'],
        'num': s['h'].get('num'),
        'name': s['h'].get('name'),
        'score': s['score'],
        'breakdown': s['breakdown'],
        'expectedOdds': s['h'].get('expectedOdds'),
    } for s in ranked]


def build_wide_combos(four):
    combos = []
    for i, j in itertools.combinations(range(len(four)), 2):
        a, b = four[i]['h'], four[j]['h']
        combos.append({
            'pair': [a.get('num'), b.get('num')],
            'names': [a.get('name'), b.get('name')],
        })
    return combos


def generate_for_race(rd_name, rn_name, cfg, force=False):
    notes = load_notes(rn_name)
    horses = notes.get('horses', [])
    if not horses:
        print(f'{rn_name}: no horses, skip')
        return
    if not isinstance(horses, list):
        print(f'{rn_name}: 旧SABCスキーマ(dict)のため skip')
        return
    ready = sum(1 for h in horses if has_all_required_factors(h))
    total = len(horses)
    readiness = ready / total
    shingan_n = shingan_coverage(horses)
    shingan_pct = (shingan_n / total * 100) if total else 0
    print(f'\n=== {rd_name} ({total}頭) === 必須3ファクター揃い率: {ready}/{total} ({readiness*100:.0f}%)  神眼: {shingan_n}/{total} ({shingan_pct:.0f}%)')
    threshold = cfg.get('readinessThreshold', 0.9)
    if readiness < threshold and not force:
        print(f'  → skip (readiness < {threshold*100:.0f}%)。--force で強制実行可')
        return

    ranked = rank_horses(horses, cfg)
    four, wmeta = pick_wide4_balanced(ranked, cfg)
    top1 = ranked[0]
    budget = cfg['budget']
    min_odds = cfg['anaSlot']['minOdds']

    wide_combos = build_wide_combos(four)
    wide_amount = budget['wideBoxPerCombo'] * len(wide_combos)

    final_bets = {
        'generatedAt':  datetime.now().isoformat(timespec='seconds'),
        'logicVersion': 'v2-shijin-bets-1',
        'readiness':    f'{ready}/{total}',
        'readinessPct': round(readiness * 100, 1),
        'shinganCoverage': f'{shingan_n}/{total}',
        'shinganCoveragePct': round(shingan_pct, 1),
        'config': {
            'gradePoints': cfg['gradePoints'],
            'weights':     cfg['weights'],
            'anaSlot':     cfg['anaSlot'],
        },
        'scoreboard': build_scoreboard(ranked),
        'tan': {
            'rank':   top1['rank'],
            'num':    top1['h'].get('num'),
            'name':   top1['h'].get('name'),
            'amount': budget['tan'],
        },
        'fuku': {
            'rank':   top1['rank'],
            'num':    top1['h'].get('num'),
            'name':   top1['h'].get('name'),
            'amount': budget['fuku'],
        },
        'wide4box': {
            'horses': [{
                'rank':  s['rank'],
                'num':   s['h'].get('num'),
                'name':  s['h'].get('name'),
                'score': s['score'],
                'isAna': (s['h'].get('expectedOdds') or 0) >= min_odds,
                'tag':   'ana' if (s['h'].get('expectedOdds') or 0) >= min_odds else 'ninki',
            } for s in four],
            'combos':      wide_combos,
            'comboCount':  len(wide_combos),
            'amount':      wide_amount,
            'composition': wmeta['composition'],
            'fallback':    wmeta['fallback'],
            'meta':        wmeta,
        },
        'totalSpend': budget['tan'] + budget['fuku'] + wide_amount,
    }
    notes['finalBets'] = final_bets
    if readiness >= threshold:
        notes['dataStatus'] = 'final'
    save_notes(rn_name, notes)

    # Print summary
    print(f'  単勝: rank{top1["rank"]} {top1["h"].get("name")} / score {top1["score"]}')
    print(f'  複勝: rank{top1["rank"]} {top1["h"].get("name")}')
    fb_mark = ' ⚠ フォールバック' if wmeta['fallback'] else ''
    print(f'  ワイド4頭BOX [{wmeta["composition"]}]{fb_mark}  (人気プール={wmeta.get("ninkiPoolSize","?")}/穴プール={wmeta.get("anaPoolSize","?")})')
    for s in four:
        od = s['h'].get('expectedOdds') or 0
        tag = '🔥穴' if od >= min_odds else '⭐人気'
        print(f'    rank{s["rank"]:>2} {s["h"].get("name"):<14} score={s["score"]:>6.2f} OD={od or "?"}  {tag}')
    print(f'  計 {final_bets["totalSpend"]}円')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='3ファクター揃い率が閾値未満でも強制実行')
    args = ap.parse_args()
    cfg = load_config()
    for rd, rn in RACE_MAP:
        generate_for_race(rd, rn, cfg, force=args.force)


if __name__ == '__main__':
    main()
