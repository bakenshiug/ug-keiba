#!/usr/bin/env python3
"""entries.html calcScores() を Python で完全再現して final JSON を更新する"""
import json, os

NOTES = "docs/data/race-notes/2026-04-19-nakayama-11r.json"
FINAL = "docs/data/final-satsuki-sho-2026-04-19.json"

# ── gradePoints ────────────────────────────────
GRADE_PTS = {
    '3S':12,'2S':11,'1S':10,
    '3A': 9,'2A': 8,'1A': 7,
    '3B': 6,'2B': 5,'1B': 4,
    '3C': 3,'2C': 2,'1C': 1,
    'D':  0,
    'S': 11,'A': 8,'B': 5,'C': 2,
}
def gp(g):
    if g is None: return None
    return GRADE_PTS.get(g)

GRADE_MAX = 12

# ── GRADE_MAPS ────────────────────────────────
GRADE_MAPS = {
    'zi':    {'S':('S','A'),'A':('A','A'),'B':('C','B'),'C':('D','C'),'D':('D','D')},
    'ext':   {'S':('A','S'),'A':('B','A'),'B':('C','B'),'C':('D','C')},
    'kinso': {
        '3S':('S','S'),'2S':('S','A'),'1S':('A','S'),
        '3A':('A','A'),'2A':('A','B'),'1A':('B','A'),
        '3B':('B','B'),'2B':('C','B'),'1B':('C','C'),
        '3C':('D','C'),'2C':('D','D'),'1C':('D','D'),
        'S':('S','S'),'A':('A','A'),'B':('B','A'),'C':('D','C'),'D':('D','D'),
    },
    'pace':  {'S':('S','A'),'A':('A','A'),'B':('C','B'),'C':('D','C'),'D':('D','D')},
    'body':  {'S':('A','S'),'A':('A','A'),'B':('C','B'),'C':('D','C'),'D':('D','D')},
    'course':{'S':('A','S'),'A':('A','A'),'B':('C','B'),'C':('D','C'),'D':('D','D')},
    'style': {'S':('S','A'),'A':('A','A'),'B':('C','B'),'C':('D','C'),'D':('D','D')},
    'weightChange':{'S':('S','A'),'A':('A','A'),'B':('C','B'),'C':('D','C'),'D':('D','D')},
}

def split_grade(g, key):
    if not g or g == '—': return (None, None)
    m = GRADE_MAPS.get(key, {})
    if g in m: return m[g]
    return (g, g)  # 12段階グレード(3S等)は単複同値

# ── ZI グレード ────────────────────────────────
def zi_grade(zi):
    if not zi: return 'D'
    if zi >= 120: return 'S'
    if zi >= 110: return 'A'
    if zi >= 100: return 'B'
    if zi >= 90:  return 'C'
    return 'D'

# ── 外厩グレード（芝） ─────────────────────────
def ext_grade(fac):
    if not fac or fac == '在厩調整': return 'C'
    if '天栄' in fac or 'しがらき' in fac: return 'S'
    if 'チャンピオン' in fac or '大山ヒルズ' in fac or '山元' in fac \
       or '社台ファーム' in fac or '社台F' in fac: return 'A'
    if '宇治田原' in fac or 'キャニオン' in fac: return 'B'
    if '優楽' in fac or '山岡' in fac or 'ヒイラギ' in fac: return 'C'
    return 'B'

# ── ginyoMult ────────────────────────────────
def ginyo_mult(g):
    return {'S':1.3,'A':1.15,'B':1.0,'C':0.7,'D':1.0}.get(g or 'B', 1.0)

# ── スコア計算 ────────────────────────────────
def calc_scores(h):
    ziT, ziF   = split_grade(zi_grade(h.get('sabcZI')), 'zi')
    exT, exF   = split_grade(ext_grade(h.get('extFacility')), 'ext')
    kT  = h.get('kinsoGrade')
    kF  = h.get('kinsoGrade')
    pT,  pF    = split_grade(h.get('paceGrade'),  'pace')
    bdT, bdF   = split_grade(h.get('bodyGrade'),  'body')
    cT,  cF    = split_grade(h.get('courseGrade'),'course')
    syT, syF   = split_grade(h.get('styleGrade'), 'style')
    srT  = h.get('sireGradeTan')
    srF  = h.get('sireGradeFuku')
    dsT  = h.get('damSireGradeTan')
    dsF  = h.get('damSireGradeFuku')
    sr2T = h.get('sireGrade2Tan')    or 'B'
    sr2F = h.get('sireGrade2Fuku')   or 'B'
    ds2T = h.get('damSireGrade2Tan') or 'B'
    ds2F = h.get('damSireGrade2Fuku')or 'B'
    bT   = h.get('bloodGradeTan')  if h.get('bloodGradeTan')  not in (None,'—') else None
    bF   = h.get('bloodGradeFuku') if h.get('bloodGradeFuku') not in (None,'—') else None
    stT  = h.get('stableGradeTan')
    stF  = h.get('stableGradeFuku')
    brT  = h.get('breederGradeTan')
    brF  = h.get('breederGradeFuku')
    jkT  = h.get('jockeyGradeTan')
    jkF  = h.get('jockeyGradeFuku')
    gtT  = h.get('gateGradeTan')
    gtF  = h.get('gateGradeFuku')
    hnT  = h.get('horseNumGradeTan')
    hnF  = h.get('horseNumGradeFuku')
    cbT  = h.get('comboGradeTan')
    cbF  = h.get('comboGradeFuku')
    spT  = h.get('specialGradeTan') or h.get('specialGrade')
    spF  = h.get('specialGradeFuku') or h.get('specialGrade')
    agT  = h.get('ageGradeTan')
    agF  = h.get('ageGradeFuku')
    rtT  = h.get('rotGradeTan')
    rtF  = h.get('rotGradeFuku')
    s3T  = h.get('sf3GradeTan')
    s3F  = h.get('sf3GradeFuku')
    lpT  = h.get('lapGradeTan')
    lpF  = h.get('lapGradeFuku')
    pmT  = h.get('prevMarginGradeTan')
    pmF  = h.get('prevMarginGradeFuku')
    cdT  = h.get('conditionGradeTan')
    cdF  = h.get('conditionGradeFuku')
    smT  = h.get('somaGradeTan')
    smF  = h.get('somaGradeFuku')
    tgtT = h.get('raceTargetGradeTan')
    tgtF = h.get('raceTargetGradeFuku')
    fwT  = h.get('finalWorkoutGradeTan')
    fwF  = h.get('finalWorkoutGradeFuku')
    khG  = h.get('kehaiGrade')
    hgT  = h.get('haigoGradeTan')
    hgF  = h.get('haigoGradeFuku')
    pxT  = h.get('paradoxGradeTan')
    pxF  = h.get('paradoxGradeFuku')
    coT  = h.get('commentGradeTan')
    coF  = h.get('commentGradeFuku')
    wcT, wcF = split_grade(h.get('weightChangeGrade'), 'weightChange')
    pcT  = h.get('prevCourseGradeTan')
    pcF  = h.get('prevCourseGradeFuku')
    chT  = h.get('charGradeTan')
    chF  = h.get('charGradeFuku')
    lhcT = h.get('lapHotCornerGrade')
    lhcF = h.get('lapHotCornerGrade')
    lgrT = h.get('lapGoldenRatioGrade')
    lgrF = h.get('lapGoldenRatioGrade')
    lttT = h.get('lapTotalTimeGrade')
    lttF = h.get('lapTotalTimeGrade')
    sm2T = h.get('soma2GradeTan')
    sm2F = h.get('soma2GradeFuku')
    gbT  = h.get('ginyoBonusGradeTan')
    gbF  = h.get('ginyoBonusGradeFuku')
    prT  = h.get('pastRaceGradeTan')
    prF  = h.get('pastRaceGradeFuku')
    gkT  = h.get('gekisouGradeTan')
    gkF  = h.get('gekisouGradeFuku')

    tan_factors  = [ziT,exT,srT,dsT,sr2T,ds2T,bT,kT,pT,stT,bdT,cT,syT,brT,jkT,gtT,hnT,cbT,spT,agT,rtT,s3T,cdT,smT,lpT,pmT,tgtT,fwT,hgT,pxT,coT,wcT,pcT,chT,lhcT,lgrT,lttT,sm2T,gbT,khG]
    fuku_factors = [ziF,exF,srF,dsF,sr2F,ds2F,bF,kF,pF,stF,bdF,cF,syF,brF,jkF,gtF,hnF,cbF,spF,agF,rtF,s3F,cdF,smF,lpF,pmF,tgtF,fwF,hgF,pxF,coF,wcF,pcF,chF,lhcF,lgrF,lttF,sm2F,gbF,khG]

    tanScore = tanMax = 0
    fukuScore = fukuMax = 0
    for g in tan_factors:
        p = gp(g)
        if p is not None: tanScore += p; tanMax += GRADE_MAX
    for g in fuku_factors:
        p = gp(g)
        if p is not None: fukuScore += p; fukuMax += GRADE_MAX

    # 過去走 ×3
    p = gp(prT)
    if p is not None: tanScore += p * 3; tanMax += GRADE_MAX * 3
    p = gp(prF)
    if p is not None: fukuScore += p * 3; fukuMax += GRADE_MAX * 3
    # 激走 ×2
    p = gp(gkT)
    if p is not None: tanScore += p * 2; tanMax += GRADE_MAX * 2
    p = gp(gkF)
    if p is not None: fukuScore += p * 2; fukuMax += GRADE_MAX * 2

    # ギーニョ乗算
    tanScore  *= ginyo_mult(h.get('ginyoGradeTan'))
    fukuScore *= ginyo_mult(h.get('ginyoGradeFuku'))

    # 総合スコア = (単+複) / (単Max+複Max) × 100
    total = tanMax + fukuMax
    sougou = round((tanScore + fukuScore) / total * 100, 1) if total > 0 else 0.0
    fuku_pct = round(fukuScore / fukuMax * 100, 1) if fukuMax > 0 else 0.0
    return sougou, fuku_pct


# ── メイン ────────────────────────────────────
with open(NOTES, encoding='utf-8') as f:
    notes = json.load(f)

horses_data = notes['horses']

# horseNum → horse data マッピング
by_horsenum = {}
for name, h in horses_data.items():
    hn = h.get('horseNum')
    if hn:
        by_horsenum[hn] = (name, h)

print("=== 皐月賞 スコア計算結果 ===")
print(f"{'馬番':>3} {'馬名':<20} {'単Pt':>8} {'複Pt':>8} {'差':>8}")
print("-" * 55)

scores = {}
for hn in sorted(by_horsenum.keys()):
    name, h = by_horsenum[hn]
    tan, fuku = calc_scores(h)
    scores[hn] = (name, tan, fuku)
    mark = h.get('mark', '')
    print(f"{hn:>3} {name:<20} {tan:>8.1f} {fuku:>8.1f}  {mark}")

# ── final JSON 更新 ────────────────────────────
with open(FINAL, encoding='utf-8') as f:
    final = json.load(f)

updated = 0
for horse in final['horses']:
    hn = horse['num']
    if hn in scores:
        name, tan, fuku = scores[hn]
        horse['totalPt'] = tan
        horse['fukuPt']  = fuku
        updated += 1

print(f"\n✅ {updated} 頭のスコアを更新")

with open(FINAL, 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)
print(f"Written: {FINAL}")
