#!/usr/bin/env python3
"""桜花賞徹底解析 v4 後半ブロック — 「すごい！感動！面白い！」全開版
Slides 15-21  →  前半14枚と結合して完全版21枚を出力
"""
import json, os, base64, html as H, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE,'docs/data/race-notes/2026-04-12-hanshin-11r.json'),encoding='utf-8') as f:
    DATA = json.load(f)
HORSES = DATA['horses']

GP = {'3S':12,'2S':11,'1S':10,'3A':9,'2A':8,'1A':7,'3B':6,'2B':5,'1B':4,
      '3C':3,'2C':2,'1C':1,'D':0,'S':11,'A':8,'B':5,'C':2}
GM = {'zi':{'S':['S','A'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'ext':{'S':['A','S'],'A':['B','A'],'B':['C','B']},
      'kinso':{'S':['S','S'],'A':['A','A'],'B':['B','A'],'C':['D','C'],'D':['D','D']},
      'pace':{'S':['S','A'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'body':{'S':['A','S'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'course':{'S':['A','S'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'style':{'S':['S','A'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']}}
def zi_g(v): return 'B' if not v else ('S' if v>=130 else 'A' if v>=115 else 'B' if v>=100 else 'C' if v>=85 else 'D')
def ext_g(f):
    if not f or f=='在厩調整': return 'B'
    return 'S' if '天栄' in f or 'しがらき' in f else 'A' if 'チャンピオン' in f or '山元' in f or 'キャニオン' in f else 'B'
def splt(g,k):
    if not g or g=='—': return [None,None]
    if k in GM and g in GM[k]: return list(GM[k][g])
    return [g,g] if g else [None,None]
def gp(g): return GP.get(g) if g else None
def calc(h):
    zig=zi_g(h.get('sabcZI')); exg=ext_g(h.get('extFacility'))
    zt,zf=splt(zig,'zi'); et,ef=splt(exg,'ext')
    kt,kf=splt(h.get('kinsoGrade'),'kinso'); pt,pf=splt(h.get('paceGrade'),'pace')
    bdt,bdf=splt(h.get('bodyGrade'),'body'); ct,cf=splt(h.get('courseGrade'),'course')
    syt,syf=splt(h.get('styleGrade'),'style')
    srt=h.get('sireGradeTan'); srf=h.get('sireGradeFuku')
    dst=h.get('damSireGradeTan'); dsf=h.get('damSireGradeFuku')
    sr2t=h.get('sireGrade2Tan','B'); sr2f=h.get('sireGrade2Fuku','B')
    ds2t=h.get('damSireGrade2Tan','B'); ds2f=h.get('damSireGrade2Fuku','B')
    blt=h.get('bloodGradeTan') if h.get('bloodGradeTan') and h.get('bloodGradeTan')!='—' else None
    blf=h.get('bloodGradeFuku') if h.get('bloodGradeFuku') and h.get('bloodGradeFuku')!='—' else None
    stt=h.get('stableGradeTan'); stf=h.get('stableGradeFuku')
    brt=h.get('breederGradeTan'); brf=h.get('breederGradeFuku')
    jkt=h.get('jockeyGradeTan'); jkf=h.get('jockeyGradeFuku')
    gtt=h.get('gateGradeTan'); gtf=h.get('gateGradeFuku')
    spt=h.get('specialGradeTan') or h.get('specialGrade')
    spf=h.get('specialGradeFuku') or h.get('specialGrade')
    agt=h.get('ageGradeTan'); agf=h.get('ageGradeFuku')
    rtt=h.get('rotGradeTan'); rtf=h.get('rotGradeFuku')
    s3t=h.get('sf3GradeTan'); s3f=h.get('sf3GradeFuku')
    cdt=h.get('conditionGradeTan'); cdf=h.get('conditionGradeFuku')
    smt=h.get('somaGradeTan'); smf=h.get('somaGradeFuku')
    tgs=[zt,et,srt,dst,sr2t,ds2t,blt,kt,pt,stt,bdt,ct,syt,brt,jkt,gtt,spt,agt,rtt,s3t,cdt,smt]
    fgs=[zf,ef,srf,dsf,sr2f,ds2f,blf,kf,pf,stf,bdf,cf,syf,brf,jkf,gtf,spf,agf,rtf,s3f,cdf,smf]
    ts=tf=tm=fm=0
    for g in tgs:
        p=gp(g)
        if p is not None: ts+=p; tm+=12
    for g in fgs:
        p=gp(g)
        if p is not None: tf+=p; fm+=12
    sf3=(h.get('sf3AnaScore') or 0); rab=(h.get('raceAnaBonus') or 0)
    bp=((gp(blt or 'B') or 5)+(gp(blf or 'B') or 5)-10)/24
    ana=sf3+rab+bp; sougou=(ts+tf)/(tm+fm) if (tm+fm)>0 else 0
    return {'tanScore':ts,'tanMax':tm,'fukuScore':tf,'fukuMax':fm,'anaScore':ana,'sougouScore':sougou}

horse_data=[]
for name,h in HORSES.items():
    sc=calc(h); tp=sc['tanScore']/sc['tanMax'] if sc['tanMax']>0 else 0
    fp=sc['fukuScore']/sc['fukuMax'] if sc['fukuMax']>0 else 0
    horse_data.append({**sc,'name':name,'h':h,'tanPct':tp,'fukuPct':fp,'odds':h.get('expectedOdds',999)})
by_tan=sorted(horse_data,key=lambda x:-x['tanPct'])
by_fuku=sorted(horse_data,key=lambda x:-x['fukuPct'])
by_ana=sorted(horse_data,key=lambda x:-x['anaScore'])
by_sougou=sorted(horse_data,key=lambda x:-x['sougouScore'])
for i,d in enumerate(by_tan):    d['tanRank']=i+1
for i,d in enumerate(by_fuku):   d['fukuRank']=i+1
for i,d in enumerate(by_ana):    d['anaRank']=i+1
for i,d in enumerate(by_sougou): d['sougouRank']=i+1
score_map={d['name']:d for d in horse_data}
by_num=sorted(horse_data,key=lambda x:x['h'].get('num',99))

e=H.escape
CORNER='<div class="corner-label">🌸 桜花賞解析 2026</div>'
def footer(pg,total=21):
    return f'<div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span style="color:#ffe696;font-weight:700">🔒 有料限定　{pg} / {total}</span></div>'
def bar_html(pct,color,height=8):
    w=min(pct*100,100)
    return f'<div style="background:rgba(0,0,0,0.07);border-radius:3px;height:{height}px;overflow:hidden"><div style="width:{w:.1f}%;height:100%;background:{color};border-radius:3px"></div></div>'

# ════════════════════════════════════════════════════════════
# Slide 15: 「3強の正体、すべて見せます」
# ════════════════════════════════════════════════════════════
def s15():
    tan1=by_tan[0]; fuku1=by_fuku[0]; ana1=by_ana[0]
    def king_card(title, icon, d, accent, sub):
        return f'''<div style="background:rgba(255,255,255,0.06);border:1px solid {accent};border-radius:12px;padding:12px 14px;backdrop-filter:blur(4px);text-align:center">
  <div style="font-size:1.8em;margin-bottom:2px">{icon}</div>
  <div style="color:{accent};font-weight:700;font-size:0.7em;letter-spacing:0.15em;margin-bottom:4px">{e(title)}</div>
  <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.3em;margin-bottom:3px">{e(d["name"])}</div>
  <div style="color:rgba(255,255,255,0.55);font-size:0.65em">{e(str(d["odds"]))}倍　{e(sub)}</div>
</div>'''
    return f'''<div class="slide" id="s15">
  <div style="background:#0d0514;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    {CORNER}
    <div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 50% 40%,rgba(232,19,110,0.18) 0%,transparent 70%)"></div>
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#f5b731,#e8136e,#6d28d9,transparent)"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#f5b731,#e8136e,#6d28d9,transparent)"></div>

    <div style="color:rgba(255,200,220,0.5);font-size:0.65em;letter-spacing:0.5em;margin-bottom:6px">PREMIUM MEMBERS ONLY</div>
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.1em;color:#f5b731;letter-spacing:0.15em;margin-bottom:4px">🔒 有料ブロック　開幕</div>
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2.6em;color:white;text-align:center;line-height:1.15;margin-bottom:6px">
      3強の正体<br><span style="font-size:0.55em;color:rgba(255,255,255,0.7)">すべて見せます</span>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;width:82%;margin-top:4px">
      {king_card('単勝キング','🥇',tan1,'#f5b731',f'単勝スコア {tan1["tanPct"]*100:.1f}%')}
      {king_card('複勝キング','🎯',fuku1,'#4ade80',f'複勝スコア {fuku1["fukuPct"]*100:.1f}%')}
      {king_card('穴馬キング','⚡',ana1,'#c084fc',f'穴スコア {ana1["anaScore"]:.2f}pt')}
    </div>
    <div style="color:rgba(255,200,220,0.45);font-size:0.65em;margin-top:12px">次のスライドから全19頭の完全データを公開　▶</div>
    {footer(15)}
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# Slide 16: 全馬スコアランキング完全版（「これが全てだ」）
# ════════════════════════════════════════════════════════════
def s16():
    def row(d):
        h=d['h']; num=h.get('num',''); odds=d['odds']
        tr=d['tanRank']; fr=d['fukuRank']; ar=d['anaRank']
        # 馬格付け
        if tr==1 or fr==1:      mark='◎'; mark_c='#f5b731'; bg_r='rgba(245,183,49,0.07)'
        elif tr<=3 or fr<=3:     mark='○'; mark_c='#4ade80'; bg_r='rgba(74,222,128,0.05)'
        elif tr<=6 or fr<=6:     mark='▲'; mark_c='#60a5fa'; bg_r='rgba(96,165,250,0.04)'
        elif ar==1:              mark='☆'; mark_c='#c084fc'; bg_r='rgba(192,132,252,0.06)'
        else:                    mark='△'; mark_c='rgba(255,255,255,0.25)'; bg_r='transparent'
        # 消し判定
        prn=h.get('prevRaceName','')
        is_keshi=any(x in prn for x in ['アネモネ','フラワー','紅梅']) or float(str(odds))>=80 or ('G2' in prn and h.get('prevFinish','')=='1着')
        if is_keshi: mark='✕'; mark_c='#dc2626'; bg_r='rgba(220,38,38,0.04)'

        # スコアバー（超コンパクト）
        tw=min(d['tanPct']*100,100); fw=min(d['fukuPct']*100,100)
        tbar=f'<div style="background:rgba(245,183,49,0.2);height:5px;border-radius:2px;width:52px;display:inline-block;vertical-align:middle;overflow:hidden"><div style="width:{tw:.0f}%;height:100%;background:#f5b731"></div></div>'
        fbar=f'<div style="background:rgba(74,222,128,0.2);height:5px;border-radius:2px;width:52px;display:inline-block;vertical-align:middle;overflow:hidden"><div style="width:{fw:.0f}%;height:100%;background:#4ade80"></div></div>'

        sp_badge=''
        if h.get('specialNote'): sp_badge='<span style="font-size:0.5em;background:rgba(245,183,49,0.3);color:#f5b731;padding:0 3px;border-radius:2px;margin-left:3px">特</span>'
        name_short=d['name'][:6]+('…' if len(d['name'])>6 else '')

        return f'''<tr style="background:{bg_r};border-bottom:1px solid rgba(255,255,255,0.06)">
  <td style="text-align:center;color:rgba(255,255,255,0.4);font-size:0.68em;padding:3px 5px;width:22px">{e(str(num))}</td>
  <td style="padding:3px 5px">
    <span style="font-size:1.0em;font-weight:900;color:{mark_c}">{mark}</span>
    <span style="font-size:0.72em;font-weight:{'700' if tr<=3 or fr<=3 else '400'};color:{'white' if tr<=3 or fr<=3 else 'rgba(255,255,255,0.75)'};margin-left:4px">{e(name_short)}</span>{sp_badge}
  </td>
  <td style="text-align:right;font-size:0.65em;color:rgba(255,255,255,0.5);padding:3px 5px">{e(str(odds))}倍</td>
  <td style="padding:3px 6px">{tbar}<br><span style="font-size:0.52em;color:#f5b731">#{tr}　{d["tanPct"]*100:.0f}%</span></td>
  <td style="padding:3px 6px">{fbar}<br><span style="font-size:0.52em;color:#4ade80">#{fr}　{d["fukuPct"]*100:.0f}%</span></td>
  <td style="text-align:center;padding:3px 4px;font-size:0.6em;color:{'#c084fc' if ar<=3 else 'rgba(255,255,255,0.3)'};font-weight:{'700' if ar<=3 else '400'}">{'★' if ar==1 else '◇' if ar<=3 else '·'}</td>
</tr>'''

    all_rows=''.join(row(d) for d in by_num)
    return f'''<div class="slide" id="s16">
  <div style="background:#0f0a14;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:linear-gradient(135deg,#1a0a20,#2d1040);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(245,183,49,0.3)">
      <div>
        <div style="color:rgba(245,183,49,0.6);font-size:0.58em;letter-spacing:0.25em">COMPLETE SCORE BOARD</div>
        <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.25em">全19頭　スコアランキング　完全版</div>
      </div>
      <div style="font-size:0.62em;text-align:right;line-height:1.6">
        <span style="color:#f5b731">◎</span><span style="color:rgba(255,255,255,0.5)"> 本命　</span>
        <span style="color:#4ade80">○</span><span style="color:rgba(255,255,255,0.5)"> 対抗　</span>
        <span style="color:#60a5fa">▲</span><span style="color:rgba(255,255,255,0.5)"> 注意　</span>
        <span style="color:#c084fc">☆</span><span style="color:rgba(255,255,255,0.5)"> 穴　</span>
        <span style="color:#dc2626">✕</span><span style="color:rgba(255,255,255,0.5)"> 消し</span>
      </div>
    </div>
    <div style="flex:1;overflow:hidden;padding:3px 8px">
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="border-bottom:1px solid rgba(245,183,49,0.4)">
            <th style="font-size:0.58em;color:rgba(255,255,255,0.4);padding:2px 5px;text-align:center">番</th>
            <th style="font-size:0.58em;color:rgba(255,255,255,0.4);padding:2px 5px;text-align:left">馬名</th>
            <th style="font-size:0.58em;color:rgba(255,255,255,0.4);padding:2px 5px;text-align:right">倍</th>
            <th style="font-size:0.58em;color:#f5b731;padding:2px 6px;text-align:center">単勝スコア</th>
            <th style="font-size:0.58em;color:#4ade80;padding:2px 6px;text-align:center">複勝スコア</th>
            <th style="font-size:0.58em;color:#c084fc;padding:2px 4px;text-align:center">穴</th>
          </tr>
        </thead>
        <tbody>{all_rows}</tbody>
      </table>
    </div>
    {footer(16)}
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# Slide 17: 対抗馬　深掘り（アランカール vs ドリームコア）
# ════════════════════════════════════════════════════════════
def s17():
    def card(name, accent, role, verdict_label, verdict_col, verdict_body, rank_str):
        sc=score_map[name]; h=sc['h']
        cond=h.get('conditionNote',''); blood=h.get('bloodNote','')
        joc=h.get('prevJockeyComment',''); ran=h.get('raceAnaNote','')
        sp=h.get('specialNote','')
        return f'''<div style="background:rgba(255,255,255,0.04);border:1px solid {accent}33;border-radius:10px;display:flex;flex-direction:column;overflow:hidden">
  <!-- ヘッダー -->
  <div style="background:linear-gradient(135deg,{accent}22,{accent}44);padding:8px 12px;border-bottom:1px solid {accent}44">
    <div style="color:{accent};font-size:0.6em;font-weight:700;letter-spacing:0.15em">{e(role)}</div>
    <div style="display:flex;align-items:baseline;justify-content:space-between">
      <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.3em">{e(name)}</div>
      <div style="color:rgba(255,255,255,0.6);font-size:0.68em">{e(str(sc["odds"]))}倍　{e(rank_str)}</div>
    </div>
    <!-- スコアバー -->
    <div style="display:flex;gap:8px;margin-top:5px">
      <div style="flex:1">
        <div style="font-size:0.58em;color:{accent};margin-bottom:1px">単勝 {sc["tanPct"]*100:.1f}%</div>
        {bar_html(sc["tanPct"],accent,5)}
      </div>
      <div style="flex:1">
        <div style="font-size:0.58em;color:#4ade80;margin-bottom:1px">複勝 {sc["fukuPct"]*100:.1f}%</div>
        {bar_html(sc["fukuPct"],"#4ade80",5)}
      </div>
      <div style="flex:1">
        <div style="font-size:0.58em;color:#c084fc;margin-bottom:1px">穴 {sc["anaScore"]:.2f}pt</div>
        {bar_html(min(sc["anaScore"]/3,1),"#c084fc",5)}
      </div>
    </div>
  </div>
  <!-- コンテンツ -->
  <div style="flex:1;padding:7px 10px;overflow:hidden;display:flex;flex-direction:column;gap:4px">
    {f'<div style="background:rgba(245,183,49,0.12);border-radius:4px;padding:3px 8px;font-size:0.62em;color:#fcd34d;line-height:1.4">⭐ {e(sp[:95])}</div>' if sp else ''}
    {f'<div style="background:{accent}18;border-left:2px solid {accent};padding:3px 7px;border-radius:0 4px 4px 0;font-size:0.62em;color:rgba(255,255,255,0.8);line-height:1.4">📊 {e(ran)}</div>' if ran else ''}
    <div style="font-size:0.62em;color:rgba(255,255,255,0.7);line-height:1.45"><strong style="color:{accent}">🏇</strong> {e(joc[:100])}{"…" if len(joc)>100 else ""}</div>
    <div style="font-size:0.62em;color:rgba(255,255,255,0.7);line-height:1.45"><strong style="color:{accent}">🏋️</strong> {e(cond[:95])}{"…" if len(cond)>95 else ""}</div>
    <!-- 評決バッジ -->
    <div style="background:{verdict_col}22;border:1px solid {verdict_col}55;border-radius:6px;padding:5px 8px;margin-top:2px">
      <div style="font-size:0.65em;font-weight:700;color:{verdict_col};margin-bottom:2px">{e(verdict_label)}</div>
      <div style="font-size:0.62em;color:rgba(255,255,255,0.75);line-height:1.4">{verdict_body}</div>
    </div>
  </div>
</div>'''

    c1=card('アランカール','#a78bfa','対抗　単#2 複#1 穴#2',
        '🟡 総合最上位対抗','#fbbf24',
        f'複勝スコア1位・穴スコア2位の二冠。G2前走3着→消しデータ回避済み。しがらきリフレッシュ効果＋折り合い改善。末脚の爆発力は本物。',
        '単2 複1 穴2')
    c2=card('ドリームコア','#38bdf8','注目　単#3 穴#5 特注あり',
        '🔵 スターズオンアース再現なるか','#38bdf8',
        f'クイーンC前走1着→2022スターズオンアース（7番人気1着）と完全同パターン。穴ボーナス+1.2。ただし調教は案外で割り引き必要。',
        '単3 複5 穴5')
    return f'''<div class="slide" id="s17">
  <div style="background:#0a0f1a;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:linear-gradient(135deg,#1e1040,#0a1628);padding:8px 14px;flex-shrink:0;border-bottom:1px solid rgba(167,139,250,0.3)">
      <div style="color:rgba(167,139,250,0.65);font-size:0.58em;letter-spacing:0.2em">CONTENDER DEEP DIVE</div>
      <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.25em">対抗馬　徹底解剖　—　本命に続く2頭</div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:8px;overflow:hidden">
      {c1}{c2}
    </div>
    {footer(17)}
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# Slide 18: 注意馬 & 消し馬（「これは買わなくていい」）
# ════════════════════════════════════════════════════════════
def s18():
    # 注意（複勝#3-4）
    chui=[d for d in by_fuku[2:5] if d['name'] not in [by_tan[0]['name'],by_fuku[0]['name']]][:2]
    # 消し馬
    keshi=[]
    for d in horse_data:
        h=d['h']; prn=h.get('prevRaceName',''); odds=float(str(d['odds']))
        reasons=[]
        if any(x in prn for x in ['アネモネ','フラワー','紅梅']): reasons.append(f'前走{prn}＝複勝率0%')
        if odds>=80: reasons.append(f'{odds}倍超＝データ消し')
        elif odds>=30: reasons.append(f'低人気（{odds}倍）')
        if 'G2' in prn and h.get('prevFinish','')=='1着': reasons.append('G2前走1着＝5%罠')
        if reasons: keshi.append((d['name'],d['odds'],' / '.join(reasons[:2])))
    keshi.sort(key=lambda x: float(str(x[1])))

    def chui_row(d):
        h=d['h']; ran=h.get('raceAnaNote',''); sp=h.get('specialNote','')
        return f'''<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(56,189,248,0.25);border-radius:8px;padding:8px 11px;margin-bottom:6px">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
    <div>
      <span style="background:#0891b2;color:white;font-size:0.58em;padding:1px 6px;border-radius:8px;margin-right:5px">要注目</span>
      <strong style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-size:0.9em">{e(d["name"])}</strong>
    </div>
    <span style="color:rgba(255,255,255,0.5);font-size:0.65em">{d["odds"]}倍　単#{d["tanRank"]} 複#{d["fukuRank"]}</span>
  </div>
  <div style="display:flex;gap:6px;margin-bottom:5px">
    <div style="flex:1"><div style="font-size:0.58em;color:#f5b731">単{d["tanPct"]*100:.1f}%</div>{bar_html(d["tanPct"],"#f5b731",5)}</div>
    <div style="flex:1"><div style="font-size:0.58em;color:#4ade80">複{d["fukuPct"]*100:.1f}%</div>{bar_html(d["fukuPct"],"#4ade80",5)}</div>
  </div>
  {f'<div style="font-size:0.6em;color:#fcd34d;margin-bottom:2px">⭐ {e(sp[:85])}</div>' if sp else ''}
  {f'<div style="font-size:0.6em;color:#38bdf8">📊 {e(ran)}</div>' if ran else ''}
</div>'''

    keshi_items=''.join(f'''<div style="display:flex;align-items:center;gap:6px;padding:3px 8px;border-radius:4px;background:rgba(220,38,38,0.07);margin:2px 0;border-left:2px solid #dc2626">
  <span style="color:#dc2626;font-weight:900;font-size:0.75em;flex-shrink:0">✕</span>
  <span style="color:rgba(255,255,255,0.7);font-size:0.65em;font-weight:600">{e(name)}</span>
  <span style="color:rgba(255,255,255,0.35);font-size:0.58em;flex:1;text-align:right">{e(str(odds))}倍　{e(reason)}</span>
</div>''' for name,odds,reason in keshi)

    return f'''<div class="slide" id="s18">
  <div style="background:#0f0a14;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:linear-gradient(135deg,#1a0a20,#001a2c);padding:8px 14px;flex-shrink:0;border-bottom:1px solid rgba(220,38,38,0.3)">
      <div style="color:rgba(248,113,113,0.65);font-size:0.58em;letter-spacing:0.2em">WATCH &amp; ELIMINATE</div>
      <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.25em">注意馬　&amp;　「これは買わなくていい」消し馬リスト</div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1.1fr 0.9fr;gap:10px;padding:8px;overflow:hidden">
      <div>
        <div style="color:#38bdf8;font-size:0.65em;font-weight:700;margin-bottom:5px">⚠️ 押さえ候補（複勝スコア上位の残り）</div>
        {''.join(chui_row(d) for d in chui)}
        <div style="background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.2);border-radius:6px;padding:7px 10px;margin-top:4px">
          <div style="font-size:0.62em;font-weight:700;color:#38bdf8;margin-bottom:3px">💡 注意馬の扱い方</div>
          <div style="font-size:0.6em;color:rgba(255,255,255,0.65);line-height:1.5">メイン3頭の馬券構成で余裕がある場合のみ少額で押さえる。軸にはしない。</div>
        </div>
      </div>
      <div>
        <div style="color:#dc2626;font-size:0.65em;font-weight:700;margin-bottom:5px">🚫 データ根拠ありの消し馬</div>
        {keshi_items}
        <div style="background:rgba(220,38,38,0.1);border:1px solid rgba(220,38,38,0.3);border-radius:6px;padding:7px 10px;margin-top:6px">
          <div style="font-size:0.62em;font-weight:700;color:#f87171;margin-bottom:3px">消しの黄金則</div>
          <div style="font-size:0.6em;color:rgba(255,255,255,0.6);line-height:1.5">消し馬に1円も使わないことが最大の収益最適化。浮いた資金を本命・対抗に集中投下する。</div>
        </div>
      </div>
    </div>
    {footer(18)}
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# Slide 19: 完全買い目（「馬券を買う」ドラマ）
# ════════════════════════════════════════════════════════════
def s19():
    tan1=by_tan[0]; fuku_sub=by_fuku[0]; ana1=by_ana[0]
    aite=[d for d in by_sougou if d['name']!=tan1['name']][:3]
    aite_names='・'.join(d['name'] for d in aite)

    def bet_card(icon, bet_type, pts, accent, horse_line, note):
        return f'''<div style="background:rgba(255,255,255,0.04);border:1px solid {accent}44;border-radius:10px;padding:9px 12px;position:relative;overflow:hidden">
  <div style="position:absolute;top:0;left:0;width:3px;height:100%;background:{accent}"></div>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
    <div style="display:flex;align-items:center;gap:7px">
      <span style="font-size:1.15em">{icon}</span>
      <span style="font-weight:700;font-size:0.82em;color:{accent}">{e(bet_type)}</span>
    </div>
    <span style="background:{accent};color:#0d0514;font-size:0.6em;font-weight:700;padding:1px 8px;border-radius:10px">{pts}点</span>
  </div>
  <div style="font-size:0.75em;color:white;margin-bottom:3px;font-family:'Hiragino Mincho ProN','Yu Mincho',serif">{horse_line}</div>
  <div style="font-size:0.6em;color:rgba(255,255,255,0.5);font-style:italic">{note}</div>
</div>'''

    return f'''<div class="slide" id="s19">
  <div style="background:#0a0d14;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:linear-gradient(135deg,#7c2d12,#92400e);padding:8px 14px;flex-shrink:0;border-bottom:1px solid rgba(245,183,49,0.4);display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(253,230,138,0.65);font-size:0.58em;letter-spacing:0.2em">COMPLETE BET PLAN</div>
        <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.25em">完全買い目　—　単勝 / 複勝 / 馬連 / ワイド</div>
      </div>
      <div style="background:rgba(245,183,49,0.15);border:1px solid rgba(245,183,49,0.4);border-radius:8px;padding:5px 12px;text-align:center">
        <div style="color:#fcd34d;font-size:0.6em;font-weight:700">軸馬</div>
        <div style="color:white;font-weight:900;font-size:1.0em;font-family:'Hiragino Mincho ProN',serif">{e(tan1["name"])}</div>
      </div>
    </div>
    <div style="flex:1;display:grid;grid-template-rows:1fr 1fr 1fr;gap:7px;padding:8px;overflow:hidden">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px">
        {bet_card('🎯','単勝　1点','1','#f5b731',f'→ {e(tan1["name"])}　{e(str(tan1["odds"]))}倍',f'単勝スコア{tan1["tanPct"]*100:.1f}%　G1前走1着×複勝100%データ。軸確定。迷わず1点勝負。')}
        {bet_card('💡','複勝①','1','#4ade80',f'→ {e(fuku_sub["name"])}　{e(str(fuku_sub["odds"]))}倍',f'複勝スコア#{fuku_sub["fukuRank"]}位 {fuku_sub["fukuPct"]*100:.1f}%　対抗筆頭を複勝で確保。')}
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px">
        {bet_card('⚡','複勝②（穴）','1','#c084fc',f'→ {e(ana1["name"])}　{e(str(ana1["odds"]))}倍',f'穴スコア#{ana1["anaRank"]}位 {ana1["anaScore"]:.2f}pt　父キタサン66.7%×データ相克。{ana1["odds"]}倍の複勝は大きい。')}
        {bet_card('🔗','馬連　軸流し','3点','#60a5fa',f'{e(tan1["name"])}　→　{e(aite_names)}',f'軸:{e(tan1["name"])}　相手3頭流し。対抗3頭をまとめてカバー。')}
      </div>
      {bet_card('💎','ワイド　軸流し','3点','#a78bfa',f'{e(tan1["name"])}　→　{e(aite_names)}',f'単勝より低リスクで複数的中が狙える。{e(tan1["name"])}が馬券圏内に来ればほぼ的中。消し馬を除いた相手3頭で効率最大化。')}
    </div>
    {footer(19)}
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# Slide 20: 3連複・3連単（「大勝負フォーメーション」）
# ════════════════════════════════════════════════════════════
def s20():
    jiku=by_tan[0]
    aite=[d for d in by_sougou if d['name']!=jiku['name']][:4]
    aite_n=[d['name'] for d in aite]

    def name_chip(name, color='#a78bfa'):
        sc=score_map[name]
        return f'<div style="background:rgba(255,255,255,0.06);border:1px solid {color}44;border-radius:6px;padding:4px 8px;text-align:center"><div style="font-size:0.72em;font-weight:700;color:{color};font-family:\'Hiragino Mincho ProN\',serif">{e(name)}</div><div style="font-size:0.55em;color:rgba(255,255,255,0.45)">{sc["odds"]}倍</div></div>'

    return f'''<div class="slide" id="s20">
  <div style="background:#06030f;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="position:absolute;inset:0;background:radial-gradient(ellipse 70% 50% at 50% 40%,rgba(109,40,217,0.12) 0%,transparent 65%)"></div>
    <div style="background:linear-gradient(135deg,#2e1065,#4c1d95);padding:8px 14px;flex-shrink:0;border-bottom:1px solid rgba(167,139,250,0.3)">
      <div style="color:rgba(196,181,253,0.65);font-size:0.58em;letter-spacing:0.2em">HIGH RETURN FORMATION</div>
      <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.25em">3連複 / 3連単　大勝負フォーメーション</div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:10px 14px;overflow:hidden">
      <!-- 3連複 -->
      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(167,139,250,0.25);border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px">
        <div>
          <div style="font-weight:700;font-size:0.85em;color:#a78bfa">🔺 3連複　軸1頭 × 相手4頭ボックス</div>
          <div style="font-size:0.62em;color:rgba(255,255,255,0.45);margin-top:1px">6点　C(4,2)＝全6通りカバー</div>
        </div>
        <div style="background:rgba(245,183,49,0.08);border:1px solid rgba(245,183,49,0.25);border-radius:8px;padding:8px 12px">
          <div style="font-size:0.6em;color:#fcd34d;margin-bottom:3px">🔒 軸（必ず3着以内に来る馬）</div>
          <div style="font-weight:900;font-size:1.05em;color:white;font-family:'Hiragino Mincho ProN',serif">{e(jiku["name"])}　{jiku["odds"]}倍</div>
        </div>
        <div style="background:rgba(167,139,250,0.06);border:1px solid rgba(167,139,250,0.2);border-radius:8px;padding:8px">
          <div style="font-size:0.6em;color:#a78bfa;margin-bottom:5px">相手（この4頭の中から2頭が来ればOK）</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px">
            {''.join(name_chip(n,'#a78bfa') for n in aite_n)}
          </div>
        </div>
        <div style="font-size:0.6em;color:rgba(255,255,255,0.4);font-style:italic">軸が3着以内 ＆ 相手4頭の中から2頭が来れば的中。6点で全パターン網羅。</div>
      </div>
      <!-- 3連単 -->
      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(192,132,252,0.25);border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px">
        <div>
          <div style="font-weight:700;font-size:0.85em;color:#c084fc">🔷 3連単　1着固定フォーメーション</div>
          <div style="font-size:0.62em;color:rgba(255,255,255,0.45);margin-top:1px">12点　1着固定 × 2・3着4頭マルチ</div>
        </div>
        <div style="background:rgba(245,183,49,0.08);border:1px solid rgba(245,183,49,0.25);border-radius:8px;padding:8px 12px">
          <div style="font-size:0.6em;color:#fcd34d;margin-bottom:3px">🥇 1着固定（揺るぎない理由あり）</div>
          <div style="font-weight:900;font-size:1.05em;color:white;font-family:'Hiragino Mincho ProN',serif">{e(jiku["name"])}　→　単勝スコア {jiku["tanPct"]*100:.1f}%</div>
          <div style="font-size:0.58em;color:rgba(255,255,255,0.45);margin-top:2px">ZI132 × G1前走1着 × 調教3S　三冠データが1着固定を正当化</div>
        </div>
        <div style="background:rgba(192,132,252,0.06);border:1px solid rgba(192,132,252,0.2);border-radius:8px;padding:8px">
          <div style="font-size:0.6em;color:#c084fc;margin-bottom:5px">2・3着（この4頭のボックス）</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px">
            {''.join(name_chip(n,'#c084fc') for n in aite_n)}
          </div>
        </div>
        <div style="font-size:0.6em;color:rgba(255,255,255,0.4);font-style:italic">1着を固定することで12点に圧縮。全マルチ(24点)の半分の資金で同等カバー。</div>
      </div>
    </div>
    {footer(20)}
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# Slide 21: 最終予想宣言（「これが答えだ」）
# ════════════════════════════════════════════════════════════
def s21():
    tan1=by_tan[0]; fuku_c=by_fuku[0]; ana1=by_ana[0]
    def declaration_card(icon,role,name,odds_str,score_str,reason,accent):
        return f'''<div style="background:rgba(255,255,255,0.05);border:1px solid {accent}55;border-radius:12px;padding:11px 14px;position:relative;overflow:hidden">
  <div style="position:absolute;top:-10px;right:-10px;font-size:3em;opacity:0.08">{icon}</div>
  <div style="color:{accent};font-size:0.6em;font-weight:700;letter-spacing:0.15em;margin-bottom:3px">{e(role)}</div>
  <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.35em;color:white;margin-bottom:2px">{e(name)}</div>
  <div style="color:rgba(255,255,255,0.5);font-size:0.65em;margin-bottom:6px">{e(odds_str)}　{e(score_str)}</div>
  <div style="font-size:0.63em;color:rgba(255,255,255,0.72);line-height:1.55;border-top:1px solid {accent}33;padding-top:5px">{e(reason)}</div>
</div>'''

    return f'''<div class="slide" id="s21">
  <div style="background:#050208;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <!-- 全画面グロー -->
    <div style="position:absolute;inset:0;background:radial-gradient(ellipse 90% 70% at 50% 40%,rgba(232,19,110,0.1) 0%,rgba(245,183,49,0.05) 50%,transparent 80%)"></div>
    <!-- 上下ゴールドライン -->
    <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent 0%,#f5b731 30%,#e8136e 50%,#f5b731 70%,transparent 100%)"></div>

    <!-- タイトル -->
    <div style="text-align:center;padding:10px 0 5px;flex-shrink:0">
      <div style="color:rgba(245,183,49,0.5);font-size:0.6em;letter-spacing:0.5em;margin-bottom:3px">FINAL DECLARATION</div>
      <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2em;color:white;letter-spacing:0.1em;line-height:1.1">
        最終　予想宣言
      </div>
      <div style="font-size:0.68em;color:#f5b731;margin-top:3px">ギーニョ重賞データ解析　2026桜花賞　—　これが答えだ</div>
    </div>

    <!-- 予想3頭 -->
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;padding:6px 14px;overflow:hidden">
      {declaration_card('🥇','◎ 本命　単勝1点 複勝1点',tan1['name'],f'{tan1["odds"]}倍',f'単勝{tan1["tanPct"]*100:.1f}%　単#1 複#2','ZI全馬最上位132 × G1前走1着 × 調教3S × G1前走1着複勝率100% ← 過去10年ブレなし。三冠データが揃った唯一の馬。単複ともに迷いなし。','#f5b731')}
      {declaration_card('🥈','○ 対抗　複勝1点 馬連・ワイド相手',fuku_c['name'],f'{fuku_c["odds"]}倍',f'複勝{fuku_c["fukuPct"]*100:.1f}%　複#1 穴#2','複勝スコア最上位・穴スコア2位の二冠。G2前走3着でデータ罠を回避済み。しがらきリフレッシュ後の末脚は爆発的。本命を脅かす最右翼。','#a78bfa')}
      {declaration_card('⚡','☆ 穴馬　複勝1点（少額）',ana1['name'],f'{ana1["odds"]}倍',f'穴スコア{ana1["anaScore"]:.2f}pt　穴#1','父キタサンブラック複勝率66.7%という驚異データ。レースデータは消し根拠ありの「データの相克」。単勝は不要だが複勝で少額バックが合理的。高配当時の恩恵は大きい。','#c084fc')}
    </div>

    <!-- 結論ボックス -->
    <div style="margin:0 14px 6px;background:rgba(245,183,49,0.06);border:1px solid rgba(245,183,49,0.25);border-radius:8px;padding:8px 14px;flex-shrink:0">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:1.5em">📌</div>
        <div style="font-size:0.65em;color:rgba(255,255,255,0.8);line-height:1.6;flex:1">
          <strong style="color:#f5b731">買い目まとめ：</strong>
          単勝<strong style="color:white">　{e(tan1["name"])}　</strong>1点　／　複勝<strong style="color:white">　{e(tan1["name"])}・{e(fuku_c["name"])}・{e(ana1["name"])}　</strong>3点　／　馬連・ワイド<strong style="color:white">　{e(tan1["name"])}軸流し　</strong>3点ずつ　／　3連複6点・3連単12点。
          消し馬（G2前走1着・アネモネ系・80倍超）には<strong style="color:#f87171">1円も使わない</strong>のがデータが導く最適解。
        </div>
      </div>
    </div>

    <div style="background:#b4084b;height:5.5%;display:flex;align-items:center;justify-content:space-between;padding:0 2%;flex-shrink:0;font-size:0.6em;flex-shrink:0">
      <span style="color:rgba(255,210,230,0.85)">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#f5b731;font-weight:700">🔒 有料限定　21 / 21　　ー　完　ー</span>
    </div>
  </div>
</div>'''

# ════════════════════════════════════════════════════════════
# 結合して完全版出力
# ════════════════════════════════════════════════════════════
back_slides=[s15(),s16(),s17(),s18(),s19(),s20(),s21()]
back_html='\n'.join(back_slides)
TOTAL=21

front_path=os.path.join(BASE,'桜花賞徹底解析2026_v4.html')
with open(front_path,encoding='utf-8') as f:
    front=f.read()

n_front=len(re.findall(r'<div class="slide"',front))

combined=front.replace(
    '\n  </div>\n</div>\n<div id="nav">',
    '\n'+back_html+'\n  </div>\n</div>\n<div id="nav">'
).replace(
    f'const N={n_front};', f'const N={TOTAL};'
).replace(
    f'(cur+1)+\' / \'+{n_front}', f'(cur+1)+\' / \'+{TOTAL}'
).replace(
    f'<span id="counter">1 / {n_front}</span>', f'<span id="counter">1 / {TOTAL}</span>'
).replace(
    '<title>桜花賞徹底解析 2026</title>',
    '<title>桜花賞徹底解析 2026　完全版（全21枚）</title>'
)

out=os.path.join(BASE,'桜花賞徹底解析2026_完全版.html')
with open(out,'w',encoding='utf-8') as f:
    f.write(combined)

size_kb=os.path.getsize(out)//1024
print(f'✅ 完成: {out}')
print(f'   前半 {n_front}枚 + 後半 {len(back_slides)}枚 = 計{TOTAL}枚')
print(f'   ファイルサイズ: {size_kb} KB')
