#!/usr/bin/env python3
"""
\u56db\u795e\u306e\u5fa1\u795e\u8a17 \u30d7\u30ec\u30bc\u30f3\u30c6\u30fc\u30b7\u30e7\u30f3\u30c7\u30fc\u30bf\u81ea\u52d5\u751f\u6210
====================================================
\u4f7f\u7528: python3 scripts/gen_presentation.py [--force]

\u5165\u529b:
  docs/data/race-notes/{race}.json \u306e finalBets

\u51fa\u529b:
  finalBets.presentation \u306b\u4ee5\u4e0b\u3092\u8ffd\u52a0:
    horses[]  - \u9078\u629c4\u982d\u306e\u8a73\u7d30\u30d7\u30ec\u30bc\u30f3\u30c6\u30fc\u30b7\u30e7\u30f3\u30c7\u30fc\u30bf
    dropped[] - \u843d\u9078\u99ac\u306e\u4e00\u884c\u30b3\u30e1\u30f3\u30c8

\u30c7\u30b6\u30a4\u30f3\u601d\u60f3:
  - \u30c6\u30f3\u30d7\u30ec\u30fc\u30c8\u81ea\u52d5\u751f\u6210\u3060\u304c\u3001\u30cb\u30c3\u30af\u304c\u5f8c\u3067 JSON \u306b\u624b\u3092\u5165\u308c\u3066\u8abf\u6574\u3067\u304d\u308b
  - comment \u306f 150-200\u5b57\u76ee\u5b89
  - reasons 3\u9805 / risks 1-2\u9805
"""
import json
import argparse
from pathlib import Path
from datetime import datetime

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')

RACE_MAP = [
    ('2026-04-25-aobasho',  '2026-04-25-tokyo-11r'),
    ('2026-04-26-floras',   '2026-04-26-tokyo-11r'),
    ('2026-04-26-milers-c', '2026-04-26-kyoto-11r'),
]

# \u8a00\u53f6 \u30b3\u30e1\u30f3\u30c8\u30ad\u30fc\u30ef\u30fc\u30c9\u3092\u7269\u8a9e\u7247\u306b\u8ee2\u63db
KEYWORD_NARRATIVE = {
    # S-tier\u5178\u578b
    '\u7121\u6557\u306e\u5148\u884c\u529b':     '\u30b9\u30bf\u30fc\u30c8\u5f62\u306e\u826f\u3055\u3068\u81ea\u30da\u30fc\u30b9\u3067\u8fbc\u3081\u308b\u69cb\u3048',
    '\u7121\u6557\u306e\u6dbf\u3044':           '\u30d4\u30fc\u30af\u7ef4\u6301\u529b\u3068\u3044\u3046\u6700\u5927\u6b66\u5668',
    '\u597d\u4f4d\u7acb\u3061\u56de\u308a\u25ce': '\u6a5f\u654f\u306b\u52dd\u3061\u306b\u884c\u3051\u308b\u7acb\u3061\u56de\u308a',
    '\u5148\u884c\u6301\u7d9a\u529b\u25ce':     '\u9038\u8131\u6280\u3067\u81ea\u30fb\u76f8\u624b\u3068\u3082\u5316\u304b\u3059\u7c4d',
    '\u30b9\u30bf\u30df\u30ca\u8ddd\u96e2\u25ce': '\u9577\u3051\u308b\u3050\u3089\u3044\u3092\u671b\u3080\u80fd\u529b',
    '2400\u9069\u6027\u629c\u7fa4':             '\u99ac\u8eab\u306e\u6df7\u4e71\u3057\u306a\u3044\u9577\u8ddd\u96e2\u9069\u6027',
    '\u4e0a\u304c\u308a\u9054\u8005':           '\u7d42\u3044\u306b\u78ba\u56fa\u3068\u3057\u305f\u5224\u65ad\u6750\u6599',
    '\u6c7a\u3081\u624b\u5805\u5b9f':           '\u6700\u5f8c\u306e\u30d5\u30a3\u30cb\u30c3\u30b7\u30e5\u3067\u4ed6\u3092\u5727\u5012\u3059\u308b\u8cc7\u8cea',
    '\u8ddd\u96e2\u77ed\u7e2e\u30d7\u30e9\u30b9': '1F\u77ed\u3044\u8a2d\u5b9a\u306e\u3072\u3068\u71b1',
    '\u30ec\u30b3\u30fc\u30c9\u64ae\u3093\u3067': '\u30de\u30a4\u30ca\u30b9\u30ec\u30b3\u30fc\u30c9\u306e\u6642\u8a08\u3092\u81a8\u3089\u307e\u305b\u305f\u4e00\u6230',
}

SHIJIN_SYMBOL = {
    'seiryu':  {'emoji': '\U0001F409', 'label': '言霊',  'color': '#1F4D2E'},
    'suzaku':  {'emoji': '\U0001F426', 'label': '神眼',  'color': '#9B2D30'},
    'byakko':  {'emoji': '\U0001F405', 'label': 'ラップ', 'color': '#C9A961'},
    'genbu':   {'emoji': '\U0001F422', 'label': '外厩',  'color': '#1A1A1A'},
}


def load_notes(rn):
    return json.loads((BASE / 'docs/data/race-notes' / f'{rn}.json').read_text(encoding='utf-8'))


def save_notes(rn, data):
    (BASE / 'docs/data/race-notes' / f'{rn}.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8'
    )


def find_horse(horses, name):
    return next((h for h in horses if h.get('name') == name), None)


def grade_symbol(g):
    return g if g else '\u2014'


def shijin_bar(h):
    """\u99ac\u306e 4\u30d5\u30a1\u30af\u30bf\u30fc\u30b0\u30ec\u30fc\u30c9\u3092\u6291\u3048\u308b"""
    rc = h.get('relComment') or {}
    sg = h.get('shingan') or {}
    lf = h.get('lapFactors') or {}
    gk = h.get('gaikyuFactor') or {}
    return {
        'seiryu':  rc.get('grade'),
        'suzaku':  sg.get('grade'),
        'byakko':  lf.get('grade'),
        'genbu':   gk.get('grade'),
    }


def derive_role(rank, is_ana, total):
    """\u5f79\u5272\u30e9\u30d9\u30eb\u3092\u6c7a\u3081\u308b"""
    if rank == 1:
        return {'label': '\u672c\u547d', 'tag': 'main',    'buy': '\u5358\u52dd\u8ef8\u30fb\u8907\u52dd\u8ef8\u30fb\u30ef\u30a4\u30c9\u6838'}
    if rank == 2:
        return {'label': '\u5bfe\u6297', 'tag': 'counter', 'buy': '\u30ef\u30a4\u30c9\u6838\u306e\u76f8\u624b'}
    if rank == 3:
        return {'label': '\u5358\u7a74', 'tag': 'hole',    'buy': '\u30ef\u30a4\u30c9\u7a74\u67a0'} if is_ana else \
               {'label': '\u62bc\u3055\u3048', 'tag': 'support', 'buy': '\u30ef\u30a4\u30c9\u8a08\u7b97\u5185'}
    if rank == 4:
        return {'label': '\u7a74\u67a0', 'tag': 'hole',    'buy': '\u30ef\u30a4\u30c9\u7a74\u67a0'} if is_ana else \
               {'label': '\u8a08\u7b97\u5185', 'tag': 'support', 'buy': '\u30ef\u30a4\u30c9\u8fd1\u3044\u6240'}
    return {'label': '\u5019\u88dc', 'tag': 'support', 'buy': '\u30ef\u30a4\u30c9\u8a08\u7b97\u5185'}


def compose_comment(h, role_tag, odds):
    """150-200\u5b57\u7a0b\u5ea6\u306e\u898b\u89e3\u30b3\u30e1\u30f3\u30c8\u81ea\u52d5\u751f\u6210"""
    rc = h.get('relComment') or {}
    gk = h.get('gaikyuFactor') or {}
    lf = h.get('lapFactors') or {}
    sg = h.get('shingan') or {}

    parts = []

    # \u51b2\u982d: \u8a00\u970a\u30b0\u30ec\u30fc\u30c9\u3068\u30ad\u30fc\u30ef\u30fc\u30c9
    kw = rc.get('keyword')
    rc_grade = rc.get('grade')
    if kw:
        # narrative \u304c kw \u3068\u540c\u3058\u306a\u3089\u8a00\u8449\u304c\u91cd\u8907\u3059\u308b\u306e\u3067\u6587\u5f62\u3092\u5207\u308a\u66ff\u3048\u308b
        narrative = KEYWORD_NARRATIVE.get(kw)
        has_narrative = narrative is not None
        if rc_grade == 'S':
            if has_narrative:
                parts.append(f'\u95a2\u4fc2\u8005\u304b\u3089\u306f\u300c{kw}\u300d\u306e\u58f0\u304c\u4e0a\u304c\u308a\u3001{narrative}\u306f\u3053\u306e\u99ac\u306e\u6700\u5927\u306e\u6b66\u5668\u3002')
            else:
                parts.append(f'\u95a2\u4fc2\u8005\u304b\u3089\u306f\u300c{kw}\u300d\u3068\u7d76\u8cdb\u306e\u58f0\u3002\u4eca\u56de\u306e\u6700\u5927\u306e\u6b66\u5668\u306b\u306a\u308b\u3002')
        elif rc_grade == 'A':
            if has_narrative:
                parts.append(f'\u95a2\u4fc2\u8005\u30b3\u30e1\u30f3\u30c8\u306f\u300c{kw}\u300d\u3002{narrative}\u306f\u4eca\u56de\u3082\u671f\u5f85\u3067\u304d\u308b\u8cc7\u8cea\u3002')
            else:
                parts.append(f'\u95a2\u4fc2\u8005\u30b3\u30e1\u30f3\u30c8\u306f\u300c{kw}\u300d\u3002\u4eca\u56de\u3082\u5341\u5206\u306b\u671f\u5f85\u3067\u304d\u308b\u8cc7\u8cea\u3002')
        else:
            parts.append(f'\u300c{kw}\u300d\u3068\u3044\u3046\u95a2\u4fc2\u8005\u30b3\u30e1\u30f3\u30c8\u3092\u7c21\u5358\u306b\u30b9\u30eb\u30fc\u3057\u306a\u3044\u3002')

    # \u5916\u53a9
    gk_canon = gk.get('canonical')
    gk_grade = gk.get('grade')
    gk_rec   = gk.get('recordStr')
    if gk_canon and gk_canon != '\u5728\u53a9\u8abf\u6574':
        if gk_grade == 'A' and gk_rec:
            parts.append(f'\u5916\u53a9\u306f{gk_canon}\u3067\u5b9f\u7e3e{gk_rec}\u3068\u76f8\u6027\u25ce\u3001\u4eca\u56de\u3082\u72b6\u614b\u306f\u4fe1\u983c\u3067\u304d\u308b\u3002')
        elif gk_grade == 'S':
            parts.append(f'\u5916\u53a9{gk_canon}\u3067\u8d85\u4e00\u7d1a\u306e\u30c7\u30fc\u30bf\u3002\u4eca\u56de\u3082\u4ed5\u4e0a\u304c\u308a\u6e80\u70b9\u3002')
        else:
            parts.append(f'\u5916\u53a9{gk_canon}\u3067\u8abf\u6574\u3002')
    elif gk_canon == '\u5728\u53a9\u8abf\u6574':
        parts.append('\u5728\u53a9\u4ed5\u4e0a\u3052\u3002\u5909\u308f\u3089\u305a\u306e\u8abf\u6574\u3067\u4eca\u56de\u306b\u81e8\u3080\u3002')

    # \u30e9\u30c3\u30d7
    lf_char  = lf.get('lapChar')
    lf_grade = lf.get('grade')
    if lf_char and lf_grade:
        parts.append(f'\u30e9\u30c3\u30d7\u89e3\u6790\u3067\u306f\u300c{lf_char}\u300d({lf_grade}\u5224\u5b9a)\u3002')

    # \u795e\u773c (shingan)
    sg_kw    = sg.get('keyword') or sg.get('quoteSummary')
    sg_grade = sg.get('grade')
    if sg_kw and sg_grade:
        if sg_grade == 'S':
            parts.append(f'\u4e88\u60f3\u5bb6\u30b3\u30e1\u30f3\u30c8\u306f\u300c{sg_kw}\u300d\u3068\u4e07\u96f7\u3002')
        elif sg_grade == 'A':
            parts.append(f'\u795e\u773c\u767a\u898b\u306f\u300c{sg_kw}\u300d\u3068\u597d\u8a00\u53f6\u3002')

    # \u8ef8/\u7a74/\u62bc\u3055\u3048\u306b\u5fdc\u3058\u305f\u7de0\u3081
    if role_tag == 'main':
        if odds and odds < 5:
            parts.append('\u4eba\u6c17\u306b\u306a\u308b\u306e\u306f\u5f53\u7136\u306e\u5b58\u5728\u611f\u3002\u7d20\u76f4\u306b\u8ef8\u3067\u52dd\u8ca0\u3002')
        else:
            parts.append('\u8ef8\u3068\u3057\u3066\u52dd\u8ca0\u3067\u304d\u308b\u4e00\u982d\u3002')
    elif role_tag == 'counter':
        parts.append('\u5bfe\u6297\u3068\u3057\u3066\u56fa\u304f\u6291\u3048\u308b\u3002')
    elif role_tag == 'hole':
        if odds and odds >= 15:
            parts.append(f'\u60f3\u5b9aOD{odds}\u500d\u306e\u7a74\u67a0\u3068\u3057\u3066\u5473\u308f\u3044\u6df1\u3044\u4e00\u982d\u3002')
        else:
            parts.append('\u4eba\u6c17\u3068\u7a74\u306e\u7e1d\u76ee\u3001\u904a\u3073\u309e\u3053\u308d\u306b\u79c0\u51fa\u305f\u8cc7\u8cea\u3002')
    else:
        parts.append('\u30ef\u30a4\u30c9\u306e\u8a08\u7b97\u5185\u3002\u9023\u306b\u4ed8\u3051\u305f\u3044\u4e00\u982d\u3002')

    # \u6587\u5b57\u6570\u8abf\u6574 (\u95a2\u4fc2\u306a\u304f\u5168\u90e8\u9023\u7d50\u3057\u3066\u8fd4\u3059)
    text = ''.join(parts)
    return text


def compose_reasons(h):
    """\u63a8\u3057\u7406\u7531 3\u9805\u76ee\u5b89"""
    rc = h.get('relComment') or {}
    gk = h.get('gaikyuFactor') or {}
    lf = h.get('lapFactors') or {}
    sg = h.get('shingan') or {}

    reasons = []

    kw = rc.get('keyword')
    rc_grade = rc.get('grade')
    if kw and rc_grade:
        reasons.append(f'\U0001F409 \u8a00\u970a {rc_grade}\uff1a\u95a2\u4fc2\u8005\u8a3c\u8a00\u300c{kw}\u300d')

    sg_kw    = sg.get('keyword') or sg.get('quoteSummary')
    sg_grade = sg.get('grade')
    if sg_kw and sg_grade:
        reasons.append(f'\U0001F426 \u795e\u773c {sg_grade}\uff1a\u4e88\u60f3\u5bb6\u58f0\u300c{sg_kw}\u300d')

    lf_char  = lf.get('lapChar')
    lf_grade = lf.get('grade')
    if lf_char and lf_grade:
        pace = lf.get('paceForecast')
        tail = f'\u00d7{pace}\u60f3\u5b9a' if pace else ''
        reasons.append(f'\U0001F405 \u30e9\u30c3\u30d7 {lf_grade}\uff1a{lf_char}{tail}')

    gk_canon = gk.get('canonical')
    gk_grade = gk.get('grade')
    gk_rec   = gk.get('recordStr')
    if gk_canon and gk_grade and gk_canon != '\u5728\u53a9\u8abf\u6574':
        rec_suffix = f' ({gk_rec})' if gk_rec else ''
        reasons.append(f'\U0001F422 \u5916\u53a9 {gk_grade}\uff1a{gk_canon}{rec_suffix}')

    # \u8840\u7d71\u88dc\u52a9\u7406\u7531 (\u76ee\u5b89\u304c3\u672a\u6e80\u306a\u3089\u8ffd\u52a0)
    sire = h.get('sire')
    bms  = h.get('broodmareSire')
    if len(reasons) < 3 and sire:
        line = f'\u8840\u7d71\uff1a\u7236{sire}'
        if bms:
            line += f' / \u6bcd\u7236{bms}'
        reasons.append(line)

    # \u9a0e\u624b\u88dc\u52a9
    joc = h.get('jockey')
    if len(reasons) < 3 and joc:
        reasons.append(f'\u9a0e\u624b\uff1a{joc}')

    return reasons[:3]


def compose_risks(h, role_tag, odds):
    """\u30ea\u30b9\u30af 1-2\u9805"""
    risks = []

    rc_grade = (h.get('relComment') or {}).get('grade')
    sg_grade = (h.get('shingan') or {}).get('grade')
    lf_grade = (h.get('lapFactors') or {}).get('grade')
    gk = h.get('gaikyuFactor') or {}
    gk_grade = gk.get('grade')
    gk_canon = gk.get('canonical')

    # \u4eba\u6c17\u30ea\u30b9\u30af
    if role_tag == 'main' and odds and odds < 3.5:
        risks.append('\u4eba\u6c17\u5148\u884c\u3001\u914d\u5f53\u5473\u308f\u3044\u306f\u8584\u3044')
    elif role_tag == 'hole' and odds and odds > 30:
        risks.append('\u5927\u7a74\u6c34\u6e96\u3001\u5b9f\u7e3e\u3088\u308a\u52e2\u3044\u4f9d\u5b58\u3067\u8cc7\u91d1\u5206\u914d\u306b\u8981\u6ce8\u610f')

    # \u5728\u53a9\u30ea\u30b9\u30af
    if gk_canon == '\u5728\u53a9\u8abf\u6574':
        risks.append('\u5916\u53a9\u30c7\u30fc\u30bf\u7121\u3001\u5728\u53a9\u4ed5\u4e0a\u3052\u306e\u4e0a\u632f\u308c\u4e0d\u5b89\u4f5c\u308b')

    # \u8cc7\u6599\u6b20\u843d
    missing = []
    if not rc_grade: missing.append('\u8a00\u970a')
    if not lf_grade: missing.append('\u30e9\u30c3\u30d7')
    if not sg_grade: missing.append('\u795e\u773c')
    if not gk_grade: missing.append('\u5916\u53a9')
    if len(missing) >= 2:
        risks.append('\u56db\u795e\u63c3\u3044\u7387\u4f4e\u3001\u30b9\u30b3\u30a2\u306f\u6697\u5024\u63a8\u5b9a')

    # D\u30b0\u30ec\u30fc\u30c9\u6709\u308a
    for gr in [rc_grade, lf_grade, sg_grade, gk_grade]:
        if gr == 'D':
            risks.append('4\u30d5\u30a1\u30af\u30bf\u30fc\u5185\u306bD\u5224\u5b9a\u3042\u308a\u3001\u4e00\u90e8\u306b\u610f\u898b\u4e0d\u4e00\u81f4')
            break

    return risks[:2] if risks else ['\u663e\u8457\u306a\u30ea\u30b9\u30af\u306f\u898b\u5f53\u305f\u3089\u305a']


def compose_dropped_note(h):
    """\u843d\u9078\u99ac\u306e 20-30\u5b57\u30b3\u30e1\u30f3\u30c8"""
    rc_grade = (h.get('relComment') or {}).get('grade')
    sg_grade = (h.get('shingan') or {}).get('grade')
    lf_grade = (h.get('lapFactors') or {}).get('grade')
    gk_grade = (h.get('gaikyuFactor') or {}).get('grade')

    grades = [g for g in [rc_grade, sg_grade, lf_grade, gk_grade] if g]
    d_count = grades.count('D')
    c_count = grades.count('C')

    if d_count >= 2:
        return '\u8907\u6570D\u5224\u5b9a\u3001\u7d20\u76f4\u306b\u6d88\u3057\u3002'
    if rc_grade == 'D':
        return '\u95a2\u4fc2\u8005\u30b3\u30e1\u30f3\u30c8\u304c\u9996\u3092\u6a2a\u306b\u3001\u6d88\u3057\u3002'
    if sg_grade == 'D':
        return '\u4e88\u60f3\u5bb6\u306e\u8a55\u4fa1\u8584\u304f\u3001\u6d88\u3057\u3002'
    if d_count == 1:
        return '\u4e00\u56e0\u5b50D\u3067\u7dcf\u5408\u5c4a\u304b\u305a\u3001\u6d88\u3057\u3002'
    if c_count >= 3:
        return '\u4f8b\u5916\u306a\u304f\u7279\u81f4\u70b9\u7121\u3057\u3001\u30b9\u30ad\u30c3\u30d7\u3002'
    if c_count >= 1:
        return 'C\u5224\u5b9a\u591a\u304f\u7a4d\u7b97\u4f38\u3073\u305a\u3001\u30b9\u30ad\u30c3\u30d7\u3002'
    if not grades:
        return '\u8cc7\u6599\u63c3\u308f\u305a\u3001\u4eca\u56de\u306f\u30d1\u30b9\u3002'
    return '\u76ee\u7acb\u3063\u305f\u8a55\u4fa1\u306a\u304f\u3001\u4eca\u56de\u306f\u30d1\u30b9\u3002'


def build_presentation(data):
    fb = data.get('finalBets')
    if not fb:
        return None
    horses = data.get('horses') or []
    wb = fb.get('wide4box') or {}
    picked = wb.get('horses') or []
    scoreboard = fb.get('scoreboard') or []
    total_horses = len(horses)

    # \u5fa1\u795e\u8a17 4\u982d
    pres_horses = []
    for i, p in enumerate(picked):
        name = p.get('name')
        h = find_horse(horses, name) or {}
        rank = p.get('rank')                 # \u3053\u308c\u306f scoreboard \u5185\u306e\u9806\u4f4d
        pos = i + 1                          # wide4box \u5185\u306e\u30dd\u30b8\u30b7\u30e7\u30f3 (1-4)
        is_ana = bool(p.get('isAna'))
        odds = p.get('expectedOdds') or h.get('expectedOdds')
        role = derive_role(pos, is_ana, total_horses)
        pres_horses.append({
            'rank':           rank,
            'pickOrder':      pos,
            'num':            p.get('num'),
            'name':           name,
            'role':           role['label'],
            'roleTag':        role['tag'],
            'buyRole':        role['buy'],
            'popularity':     'hole' if is_ana else 'popular',
            'shijinGrades':   shijin_bar(h),
            'score':          p.get('score'),
            'expectedOdds':   odds,
            'jockey':         h.get('jockey'),
            'trainer':        h.get('trainer'),
            'sire':           h.get('sire'),
            'broodmareSire':  h.get('broodmareSire'),
            'gaikyuLabel':    (h.get('gaikyuFactor') or {}).get('canonical') or h.get('gaikyu'),
            'relKeyword':     (h.get('relComment') or {}).get('keyword'),
            'shinganKeyword': (h.get('shingan') or {}).get('keyword') or (h.get('shingan') or {}).get('quoteSummary'),
            'lapChar':        (h.get('lapFactors') or {}).get('lapChar'),
            'comment':        compose_comment(h, role['tag'], odds),
            'reasons':        compose_reasons(h),
            'risks':          compose_risks(h, role['tag'], odds),
        })

    # \u843d\u9078\u306e\u5100 (scoreboard\u7b2c5\u4ee5\u4e0b)
    picked_names = {p.get('name') for p in picked}
    dropped = []
    for s in scoreboard:
        n = s.get('name')
        if n in picked_names:
            continue
        h = find_horse(horses, n) or {}
        dropped.append({
            'name':         n,
            'num':          s.get('num'),
            'rank':         s.get('rank'),
            'score':        s.get('score'),
            'expectedOdds': s.get('expectedOdds'),
            'note':         compose_dropped_note(h),
        })

    return {
        'generatedAt': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'style':       'shijin-oracle-v1',
        'horses':      pres_horses,
        'dropped':     dropped,
    }


def process(rn):
    data = load_notes(rn)
    fb = data.get('finalBets')
    if not fb:
        print(f'[skip] {rn}: finalBets \u672a\u751f\u6210')
        return False
    pres = build_presentation(data)
    if not pres:
        print(f'[skip] {rn}: presentation \u751f\u6210\u4e0d\u53ef')
        return False
    fb['presentation'] = pres
    save_notes(rn, data)
    print(f'[ok]   {rn}: presentation {len(pres["horses"])}\u982d + \u843d\u9078 {len(pres["dropped"])}\u982d')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='\u7279\u5b9a\u30ec\u30fc\u30b9\u540d\u3060\u3051 (2026-04-25-aobasho etc)')
    args = ap.parse_args()

    targets = [(label, rn) for label, rn in RACE_MAP if not args.only or label == args.only]
    print(f'=== \u56db\u795e\u306e\u5fa1\u795e\u8a17 \u30d7\u30ec\u30bc\u30f3\u30c6\u30fc\u30b7\u30e7\u30f3\u81ea\u52d5\u751f\u6210 ===')
    for label, rn in targets:
        print(f'  \u25b6 {label} -> {rn}')
        process(rn)


if __name__ == '__main__':
    main()
