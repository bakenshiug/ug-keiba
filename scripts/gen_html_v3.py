#!/usr/bin/env python3
"""桜花賞徹底解析 v3 — HTML スライドショー生成
スライド12枚・スタンドアロンHTML・ブラウザでPDF変換可
"""
import json, os, base64, html as htmlmod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ══ データ読み込み ══════════════════════════════
with open(os.path.join(BASE,'docs/data/race-notes/2026-04-12-hanshin-11r.json'),encoding='utf-8') as f:
    DATA = json.load(f)
HORSES = DATA['horses']

# ══ スコア計算（gen_pptx_v3.py と同一ロジック） ══
GP = {'3S':12,'2S':11,'1S':10,'3A':9,'2A':8,'1A':7,'3B':6,'2B':5,'1B':4,
      '3C':3,'2C':2,'1C':1,'D':0,'S':11,'A':8,'B':5,'C':2}
GM = {'zi':{'S':['S','A'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'ext':{'S':['A','S'],'A':['B','A'],'B':['C','B']},
      'kinso':{'S':['S','S'],'A':['A','A'],'B':['B','A'],'C':['D','C'],'D':['D','D']},
      'pace':{'S':['S','A'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'body':{'S':['A','S'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'course':{'S':['A','S'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']},
      'style':{'S':['S','A'],'A':['A','A'],'B':['C','B'],'C':['D','C'],'D':['D','D']}}

def zi_g(v):
    if not v: return 'B'
    return 'S' if v>=130 else 'A' if v>=115 else 'B' if v>=100 else 'C' if v>=85 else 'D'
def ext_g(f):
    if not f or f=='在厩調整': return 'B'
    if '天栄' in f or 'しがらき' in f: return 'S'
    if 'チャンピオン' in f or '山元' in f or 'キャニオン' in f: return 'A'
    return 'B'
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
    ana=sf3+rab+bp
    sougou=(ts+tf)/(tm+fm) if (tm+fm)>0 else 0
    return {'tanScore':ts,'tanMax':tm,'fukuScore':tf,'fukuMax':fm,'anaScore':ana,'sougouScore':sougou}

horse_data=[]
for name,h in HORSES.items():
    sc=calc(h)
    tp=sc['tanScore']/sc['tanMax'] if sc['tanMax']>0 else 0
    fp=sc['fukuScore']/sc['fukuMax'] if sc['fukuMax']>0 else 0
    horse_data.append({**sc,'name':name,'h':h,'tanPct':tp,'fukuPct':fp,'odds':h.get('expectedOdds',999)})

by_tan    = sorted(horse_data,key=lambda x:-x['tanPct'])
by_fuku   = sorted(horse_data,key=lambda x:-x['fukuPct'])
by_ana    = sorted(horse_data,key=lambda x:-x['anaScore'])
by_sougou = sorted(horse_data,key=lambda x:-x['sougouScore'])
for i,d in enumerate(by_tan):    d['tanRank']=i+1
for i,d in enumerate(by_fuku):   d['fukuRank']=i+1
for i,d in enumerate(by_ana):    d['anaRank']=i+1
for i,d in enumerate(by_sougou): d['sougouRank']=i+1

# ══ 画像 base64 埋め込み ═══════════════════════
def img_b64(path):
    if not os.path.exists(path): return ''
    with open(path,'rb') as f: data=f.read()
    ext='jpg' if path.endswith('.jpg') else 'png'
    return f'data:image/{ext};base64,{base64.b64encode(data).decode()}'

IMG_BRAIN = img_b64(os.path.join(BASE,'brain_cover.jpg'))
IMG_GINYO = img_b64(os.path.join(BASE,'ginyo.jpg'))
IMG_GOTO  = img_b64(os.path.join(BASE,'goto.jpg'))

def e(s): return htmlmod.escape(str(s))

# ══ HTMLヘルパー ════════════════════════════════
def bar(pct, color, height=10):
    w = min(pct*100, 100)
    return f'''<div style="background:#e8d5dc;border-radius:4px;height:{height}px;overflow:hidden">
  <div style="width:{w:.1f}%;height:100%;background:{color};border-radius:4px"></div>
</div>'''

# ══ スライド HTML 生成 ════════════════════════════

def s01():
    return f'''
<div class="slide" id="s1">
  <div style="background:#e8136e;width:100%;height:100%;position:relative;overflow:hidden">
    <!-- 脳画像 -->
    <img src="{IMG_BRAIN}" style="position:absolute;right:-2%;top:-1%;width:62%;height:103%;object-fit:cover;opacity:0.9">
    <!-- 左オーバーレイ -->
    <div style="position:absolute;left:0;top:0;width:47%;height:100%;background:#e8136e"></div>
    <!-- グラデオーバーレイ -->
    <div style="position:absolute;left:40%;top:0;width:15%;height:100%;background:linear-gradient(to right,#e8136e,transparent)"></div>
    <!-- 上下ゴールドライン -->
    <div style="position:absolute;top:0;left:0;right:0;height:5px;background:#f5b731"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:5px;background:#f5b731"></div>
    <!-- G1バッジ -->
    <div style="position:absolute;left:3.5%;top:7%;background:#f5b731;color:#0f0a0c;font-weight:900;font-size:1.4em;padding:4px 20px;border-radius:20px;font-family:'Hiragino Mincho ProN','Yu Mincho',serif">G 1</div>
    <!-- メインタイトル -->
    <div style="position:absolute;left:3%;top:17%;color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:5.8em;line-height:1.05;letter-spacing:0.04em">桜花賞</div>
    <!-- ゴールドライン -->
    <div style="position:absolute;left:3%;top:59%;width:43%;height:4px;background:#f5b731"></div>
    <!-- サブタイトル -->
    <div style="position:absolute;left:3%;top:62%;color:#f5b731;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2.5em;letter-spacing:0.15em">徹 底 解 析</div>
    <!-- 日時 -->
    <div style="position:absolute;left:3%;top:76%;color:rgba(255,220,235,0.95);font-size:0.78em">2026年4月12日（日）　阪神競馬場　芝1600m外　19頭立て</div>
    <div style="position:absolute;left:3%;top:83%;width:43%;height:2px;background:rgba(255,180,210,0.6)"></div>
    <div style="position:absolute;left:3%;top:86%;color:rgba(255,240,248,0.85);font-size:0.75em;font-style:italic">ギーニョ重賞データ × 血統解析 × 特別ファクター</div>
    <!-- ゴトー -->
    <img src="{IMG_GOTO}" style="position:absolute;right:1%;bottom:3%;width:22%;object-fit:contain">
    <!-- ロゴ帯 -->
    <div style="position:absolute;left:0;bottom:6%;width:46%;background:white;padding:6px 20px">
      <span style="color:#b4084b;font-weight:900;font-size:0.85em">UG競馬 競馬予想チャンネル</span>
    </div>
  </div>
</div>'''

def big_num_slide(sid, badge_num, badge_text, badge_color,
                  number, num_color, main_label, sub_text,
                  note=None, char='ginyo', page=2, paid=False):
    char_img = IMG_GINYO if char=='ginyo' else IMG_GOTO
    note_html = f'<div style="position:absolute;left:50%;bottom:10%;transform:translateX(-50%);background:{badge_color};color:white;font-weight:700;font-size:0.72em;padding:5px 22px;border-radius:20px;white-space:nowrap">{e(note)}</div>' if note else ''
    tag = '🔒 メンバーシップ限定' if paid else '🆓 無料公開'
    tag_color = '#ffe696' if paid else '#f5b731'
    return f'''
<div class="slide" id="s{sid}">
  <div style="background:#fff5eb;width:100%;height:100%;position:relative;overflow:hidden">
    <!-- chevrons -->
    <div style="position:absolute;left:1%;top:1%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <div style="position:absolute;right:1%;bottom:8%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <!-- 番号バッジ -->
    <div style="position:absolute;left:3.5%;top:5%;background:{badge_color};color:white;font-weight:700;font-size:0.85em;padding:5px 22px;border-radius:20px">{e(badge_num)}　{e(badge_text)}</div>
    <!-- 巨大数字 -->
    <div style="position:absolute;left:0;top:14%;width:100%;text-align:center;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:8em;color:{num_color};line-height:1">{e(number)}</div>
    <!-- 区切り線 -->
    <div style="position:absolute;left:14%;top:75%;width:62%;height:4px;background:{badge_color}"></div>
    <!-- メインラベル -->
    <div style="position:absolute;left:0;top:78%;width:100%;text-align:center;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.5em;color:#0f0a0c">{e(main_label)}</div>
    <!-- サブテキスト -->
    <div style="position:absolute;left:5%;top:87%;width:90%;text-align:center;font-size:0.8em;color:#6b505a;font-style:italic">{e(sub_text)}</div>
    {note_html}
    <!-- キャラクター -->
    <img src="{char_img}" style="position:absolute;right:1%;bottom:8%;width:21%;object-fit:contain">
    <!-- フッター -->
    <div style="position:absolute;bottom:0;left:0;right:0;height:5.5%;background:#b4084b;display:flex;align-items:center;justify-content:space-between;padding:0 2%">
      <span style="color:rgba(255,210,230,0.9);font-size:0.6em">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:{tag_color};font-weight:700;font-size:0.6em">{tag}　{page}/12</span>
    </div>
  </div>
</div>'''

def s07():
    sires=[
        ('キタサンブラック','66.7',0.667,'#b45309','3頭','ブラックチャリス'),
        ('エピファネイア',  '28.6',0.286,'#e8136e','7頭','アランカール'),
        ('ロードカナロア',  '22.2',0.222,'#6b505a','多数','複は〇 単は✕'),
    ]
    dams=[
        ('ハーツクライ','50.0',0.5,'#b45309','2頭','フェスティバルヒル'),
        ('クロフネ','42.9',0.429,'#08919e','7頭',''),
        ('ディープインパクト','0.0',0.0,'#dc2626','多数','ルールザウェイヴ 消し'),
    ]
    medals=['🥇','🥈','🥉']
    def sire_rows():
        rows=[]
        for i,(nm,pct,pv,col,cnt,note) in enumerate(sires):
            bg='#fff9f0' if i%2==0 else 'white'
            rows.append(f'''
<div style="background:{bg};border-radius:8px;margin:4px 0;padding:8px 10px 6px;border-left:4px solid {col}">
  <div style="display:flex;align-items:center;justify-content:space-between">
    <span style="font-weight:{'900' if i==0 else '600'};font-size:0.88em">{medals[i]}　{e(nm)}</span>
    <span style="color:{col};font-weight:700;font-size:0.88em">{pct}%</span>
  </div>
  <div style="margin:3px 0">{bar(pv,col,7)}</div>
  <div style="font-size:0.7em;color:{col};font-style:italic">{e(note)}　（{e(cnt)}）</div>
</div>''')
        return ''.join(rows)
    def dam_rows():
        rows=[]
        for i,(nm,pct,pv,col,cnt,note) in enumerate(dams):
            bg='#f0faff' if i%2==0 else 'white'
            rows.append(f'''
<div style="background:{bg};border-radius:8px;margin:4px 0;padding:8px 10px 6px;border-left:4px solid {col}">
  <div style="display:flex;align-items:center;justify-content:space-between">
    <span style="font-weight:{'900' if i==0 else '600'};font-size:0.88em">{medals[i]}　{e(nm)}</span>
    <span style="color:{col};font-weight:700;font-size:0.88em">{pct}%</span>
  </div>
  <div style="margin:3px 0">{bar(pv,col,7)}</div>
  {f'<div style="font-size:0.7em;color:{col};font-style:italic">{e(note)}</div>' if note else ''}
</div>''')
        return ''.join(rows)
    return f'''
<div class="slide" id="s7">
  <div style="background:#fff5eb;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:1%;top:1%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <div style="position:absolute;right:1%;bottom:8%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <!-- タイトル -->
    <div style="background:#e8136e;text-align:center;padding:10px 0;flex-shrink:0">
      <span style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.4em;letter-spacing:0.2em">血 統 解 析</span>
    </div>
    <div style="text-align:center;font-size:0.7em;color:#6b505a;font-style:italic;padding:4px 0">ギーニョ血統データ　桜花賞 父系・母父系 複勝率ランキング</div>
    <!-- 2カラム -->
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 8px;overflow:hidden">
      <div>
        <div style="background:#b45309;color:white;text-align:center;font-weight:700;font-size:0.85em;padding:5px;border-radius:4px 4px 0 0">父　系　ランキング</div>
        {sire_rows()}
      </div>
      <div>
        <div style="background:#08919e;color:white;text-align:center;font-weight:700;font-size:0.85em;padding:5px;border-radius:4px 4px 0 0">母父系　ランキング</div>
        {dam_rows()}
      </div>
    </div>
    <!-- 血統総括 -->
    <div style="margin:4px 8px;background:white;border-left:4px solid #f5b731;padding:5px 10px;border-radius:4px;font-size:0.7em;color:#0f0a0c;flex-shrink:0">
      血統総括: ブラックチャリス（父66.7%）とフェスティバルヒル（母父50%）が血統最上位。ただしデータ相克あり。
    </div>
    <!-- ギーニョ -->
    <img src="{IMG_GINYO}" style="position:absolute;right:0%;bottom:6%;width:18%;object-fit:contain">
    <!-- フッター -->
    <div style="background:#b4084b;height:5.5%;display:flex;align-items:center;justify-content:space-between;padding:0 2%;flex-shrink:0">
      <span style="color:rgba(255,210,230,0.9);font-size:0.6em">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#f5b731;font-weight:700;font-size:0.6em">🆓 無料公開　7/12</span>
    </div>
  </div>
</div>'''

def s08():
    # 特別解析
    def make_card(col, icon, title, desc, horses):
        horse_chips = ''.join(f'<div style="background:white;color:{col};font-weight:700;font-size:0.75em;padding:3px 10px;border-radius:12px;margin:3px 0">{e(h)}</div>' for h in horses[:3])
        return f'''
<div style="background:{col};border-radius:10px;padding:12px 10px;display:flex;flex-direction:column;align-items:center;overflow:hidden">
  <div style="font-size:2em;margin-bottom:4px">{icon}</div>
  <div style="color:white;font-weight:900;font-size:0.9em;margin-bottom:6px;text-align:center;font-family:'Hiragino Mincho ProN','Yu Mincho',serif">{e(title)}</div>
  <div style="color:rgba(255,240,245,0.9);font-size:0.7em;text-align:center;margin-bottom:8px;line-height:1.4">{e(desc)}</div>
  {horse_chips}
</div>'''

    g2_trap = [n for n,h in HORSES.items() if h.get('prevRaceName','') in ['チューリップ賞','フィリーズレビュー']
               and ('1着' in (h.get('prevFinish','')) or h.get('prevFinish','')=='1')][:3]
    g1_ok   = [n for n,h in HORSES.items() if 'G1' in h.get('prevRaceName','')
               and '1着' in h.get('prevFinish','')][:3]
    ana_ok  = [n for n,h in HORSES.items() if (h.get('raceAnaBonus') or 0)>=1.0][:4]

    card1 = make_card('#b4084b','🚫','G2前走の罠',
        'チューリップ賞などG2前走1着は複勝率わずか5%。実力があっても大幅割引。', g2_trap)
    card2 = make_card('#16a34a','✅','G1前走の正解',
        'G1前走1着は複勝率100%。阪神JF直行ローテは最強条件。', g1_ok)
    card3 = make_card('#b45309','🎯','穴馬ファクター',
        'レース統計から導かれた穴馬候補。血統×ローテが揃った一発期待馬。', ana_ok)

    return f'''
<div class="slide" id="s8">
  <div style="background:#fffaeb;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:1%;top:1%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <!-- タイトル -->
    <div style="background:#e8136e;text-align:center;padding:10px 0;flex-shrink:0">
      <span style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.4em;letter-spacing:0.2em">特 別 解 析</span>
    </div>
    <div style="text-align:center;font-size:0.7em;color:#6b505a;font-style:italic;padding:4px 0">G2前走の罠　／　G1前走の正解　／　穴馬ファクター該当馬</div>
    <!-- 3カラムカード -->
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;padding:6px 12px;overflow:hidden">
      {card1}{card2}{card3}
    </div>
    <!-- フッター -->
    <div style="background:#b4084b;height:5.5%;display:flex;align-items:center;justify-content:space-between;padding:0 2%;flex-shrink:0">
      <span style="color:rgba(255,210,230,0.9);font-size:0.6em">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#f5b731;font-weight:700;font-size:0.6em">🆓 無料公開　8/12</span>
    </div>
  </div>
</div>'''

def score_slide(sid, top, header_color, score_label, score_pct, score_rank,
                score_color, sub_label, page, char='goto'):
    h = top['h']
    char_img = IMG_GINYO if char=='ginyo' else IMG_GOTO
    factors=[
        ('能力 ZI',str(h.get('sabcZI','?'))),
        ('近走グレード',str(h.get('kinsoGrade','—'))),
        ('コース適性',str(h.get('courseGrade','—'))),
        ('ローテ評価',str(h.get('rotGradeTan','—'))),
        ('厩舎',str(h.get('stableGradeTan','—'))),
        ('調教',str(h.get('conditionGradeTan','—'))),
        ('前走',str(h.get('prevRaceName','—'))[:12]),
        ('前走結果',str(h.get('prevFinish','—'))),
    ]
    factor_rows=''.join(f'''
<div style="display:flex;justify-content:space-between;padding:4px 8px;background:{'#fdf5fa' if i%2==0 else 'white'}">
  <span style="color:#6b505a;font-size:0.72em">{e(lbl)}</span>
  <span style="font-size:0.72em;font-weight:{'700' if any(v in val for v in ['S','A','1着']) else '400'};color:{'#e8136e' if any(v in val for v in ['S','A','1着']) else '#0f0a0c'}">{e(val)}</span>
</div>''' for i,(lbl,val) in enumerate(factors))

    sp = h.get('specialNote','')
    sp_html = f'<div style="background:#fff5f8;border-left:3px solid #f5b731;padding:5px 8px;margin-top:6px;font-size:0.7em;color:#0f0a0c;font-style:italic">⭐ {e(sp)}</div>' if sp else ''

    return f'''
<div class="slide" id="s{sid}">
  <div style="background:#fffaeb;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:1%;top:1%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <!-- ヘッダー -->
    <div style="background:{header_color};padding:8px 16px;flex-shrink:0">
      <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.6em">{e(score_label)}</div>
      <div style="color:rgba(255,235,245,0.9);font-size:0.72em;margin-top:2px">{e(sub_label)}　／　{e(top["name"])}　{e(top["odds"])}倍</div>
    </div>
    <!-- メインコンテンツ -->
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.1fr;gap:8px;padding:8px;overflow:hidden">
      <!-- 左: スコア -->
      <div style="background:white;border-radius:8px;padding:10px;overflow:hidden">
        <div style="color:{score_color};font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.5em;text-align:center">{e(top["name"])}</div>
        <div style="color:#6b505a;text-align:center;font-size:0.75em;margin:3px 0">想定オッズ　{e(top["odds"])}倍</div>
        <div style="margin:8px 0">
          <div style="display:flex;justify-content:space-between;margin-bottom:2px">
            <span style="font-size:0.72em;font-weight:700;color:{score_color}">{e(score_label[:2])}スコア</span>
            <span style="font-size:0.72em;font-weight:700;color:{score_color}">{score_pct*100:.1f}%　#{score_rank}</span>
          </div>
          {bar(score_pct, score_color, 10)}
        </div>
        <div style="margin:4px 0">
          <div style="display:flex;justify-content:space-between;margin-bottom:2px">
            <span style="font-size:0.7em;color:#b45309">単勝</span>
            <span style="font-size:0.7em;color:#b45309">{top["tanPct"]*100:.1f}%　#{top["tanRank"]}</span>
          </div>
          {bar(top["tanPct"], "#b45309", 7)}
        </div>
        <div style="margin:4px 0">
          <div style="display:flex;justify-content:space-between;margin-bottom:2px">
            <span style="font-size:0.7em;color:#16a34a">複勝</span>
            <span style="font-size:0.7em;color:#16a34a">{top["fukuPct"]*100:.1f}%　#{top["fukuRank"]}</span>
          </div>
          {bar(top["fukuPct"], "#16a34a", 7)}
        </div>
        {sp_html}
      </div>
      <!-- 右: ファクター -->
      <div style="background:white;border-radius:8px;overflow:hidden">
        <div style="background:{header_color};color:white;font-weight:700;font-size:0.8em;padding:6px 10px">ファクター詳細</div>
        {factor_rows}
        <img src="{char_img}" style="width:45%;float:right;margin:4px">
      </div>
    </div>
    <!-- フッター -->
    <div style="background:#b4084b;height:5.5%;display:flex;align-items:center;justify-content:space-between;padding:0 2%;flex-shrink:0">
      <span style="color:rgba(255,210,230,0.9);font-size:0.6em">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#ffe696;font-weight:700;font-size:0.6em">🔒 メンバーシップ限定　{page}/12</span>
    </div>
  </div>
</div>'''

def s11():
    top = by_ana[0]; h = top['h']
    ran = h.get('raceAnaNote',''); sp = h.get('specialNote','')
    bn = h.get('bloodNote','')
    note_text = f'穴ボーナス: {ran}' if ran else '前走クラス等でデータ消し根拠が存在'
    return f'''
<div class="slide" id="s11">
  <div style="background:#fffaeb;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:1%;top:1%;color:#f5c8aa;font-size:2em;font-weight:900;opacity:0.7">»»</div>
    <div style="background:#6d28d9;padding:8px 16px;flex-shrink:0">
      <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.6em">穴馬スコア 1 位</div>
      <div style="color:rgba(220,200,255,0.9);font-size:0.72em;margin-top:2px">穴馬スコア最上位　／　{e(top["name"])}　{e(top["odds"])}倍　（単{top["tanRank"]}位）</div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.1fr;gap:8px;padding:8px;overflow:hidden">
      <!-- 左 -->
      <div style="background:white;border-radius:8px;padding:10px;overflow:hidden">
        <div style="color:#6d28d9;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.5em;text-align:center">{e(top["name"])}</div>
        <div style="color:#6b505a;text-align:center;font-size:0.75em;margin:3px 0">{e(top["odds"])}倍　/　穴スコア {top["anaScore"]:.2f} pt</div>
        <div style="margin:6px 0">{bar(min(top["anaScore"]/3.0,1.0),"#6d28d9",9)}</div>
        <!-- 血統最高カード -->
        <div style="background:#faf5ff;border-left:3px solid #b45309;border-radius:4px;padding:7px 10px;margin:6px 0">
          <div style="font-weight:700;font-size:0.8em;color:#b45309">🧬 血統評価　最高</div>
          <div style="font-size:0.72em;color:#0f0a0c;margin-top:4px">父キタサンブラック →　複勝率 66.7%<br>全産駒複勝圏の驚異データ</div>
        </div>
        <!-- レースデータカード -->
        <div style="background:#fff5f5;border-left:3px solid #dc2626;border-radius:4px;padding:7px 10px">
          <div style="font-weight:700;font-size:0.8em;color:#dc2626">📊 レースデータ　消し根拠あり</div>
          <div style="font-size:0.72em;color:#0f0a0c;margin-top:4px">{e(note_text)}</div>
        </div>
      </div>
      <!-- 右 -->
      <div style="background:white;border-radius:8px;overflow:hidden;display:flex;flex-direction:column">
        <div style="background:#6d28d9;color:white;font-weight:700;font-size:0.8em;padding:6px 10px">⚡ データの相克　解説</div>
        <div style="padding:8px 10px;font-size:0.73em;color:#0f0a0c;line-height:1.5">血統は「最高評価」、レースデータは「消し根拠あり」という相矛盾するデータが共存。これが「データの相克」。単勝ではなく複勝での少額バックが合理的判断。</div>
        <div style="margin:0 10px;height:2px;background:rgba(180,150,255,0.5)"></div>
        <div style="padding:6px 10px">
          <div style="font-weight:700;font-size:0.8em;color:#6d28d9;margin-bottom:4px">🧬 血統コメント</div>
          <div style="font-size:0.7em;color:#0f0a0c;font-style:italic;line-height:1.4">{e((bn[:180]+'…') if len(bn)>180 else bn)}</div>
        </div>
        <div style="flex:1"></div>
        <!-- 結論ボックス -->
        <div style="background:#f0e6ff;border-left:3px solid #6d28d9;margin:6px 10px;padding:7px 10px;border-radius:4px">
          <div style="font-weight:700;font-size:0.8em;color:#6d28d9">💡 結論　→　複勝で少額バック推奨</div>
          <div style="font-size:0.72em;color:#0f0a0c;margin-top:3px">血統最高 × データ消し = 複勝狙い一択</div>
        </div>
        <img src="{IMG_GINYO}" style="width:30%;float:right;margin:4px 8px">
      </div>
    </div>
    <div style="background:#b4084b;height:5.5%;display:flex;align-items:center;justify-content:space-between;padding:0 2%;flex-shrink:0">
      <span style="color:rgba(255,210,230,0.9);font-size:0.6em">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#ffe696;font-weight:700;font-size:0.6em">🔒 メンバーシップ限定　11/12</span>
    </div>
  </div>
</div>'''

def s12():
    previews=[
        '▶ 全馬スコアランキング完全版（19頭）',
        '▶ 対抗馬・注意馬 詳細ファクター解説',
        '▶ 完全買い目提案（単勝〜3連単まで）',
    ]
    preview_html=''.join(f'<div style="background:rgba(180,8,75,0.7);border-radius:20px;padding:7px 24px;margin:5px auto;max-width:65%;color:white;font-size:0.82em">{e(p)}</div>' for p in previews)
    return f'''
<div class="slide" id="s12">
  <div style="background:#e8136e;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    <img src="{IMG_BRAIN}" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:90%;height:90%;object-fit:cover;opacity:0.12">
    <div style="position:absolute;top:0;left:0;right:0;height:5px;background:#f5b731"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:5px;background:#f5b731"></div>
    <!-- STOP バッジ -->
    <div style="background:white;color:#e8136e;font-weight:700;font-size:0.85em;padding:6px 28px;border-radius:20px;margin-bottom:10px">◆　前半ブロック　ここまで　◆</div>
    <!-- 続きは -->
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:5.5em;color:white;letter-spacing:0.1em;line-height:1">続 き は...</div>
    <!-- 有料 -->
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.8em;color:#f5b731;margin:8px 0 12px">有料メンバーシップ　限定公開</div>
    {preview_html}
    <!-- CTA -->
    <div style="background:#f5b731;color:#0f0a0c;font-weight:900;font-size:0.9em;padding:10px 32px;border-radius:25px;margin-top:14px">▶　チャンネル登録・メンバーシップはこちら</div>
    <!-- キャラクター -->
    <img src="{IMG_GINYO}" style="position:absolute;left:0%;bottom:5%;width:16%;object-fit:contain">
    <img src="{IMG_GOTO}"  style="position:absolute;right:0%;bottom:5%;width:18%;object-fit:contain">
    <div style="position:absolute;bottom:1%;left:0;right:0;text-align:center;color:rgba(255,220,235,0.7);font-size:0.6em;font-style:italic">[チャンネルURL / QRコードをここに挿入]</div>
  </div>
</div>'''

# ══ 全スライド生成 ══════════════════════════════
slides = [
    s01(),
    big_num_slide(2,'①','ギーニョデータ解析','#b45309',
        '70 %','#b45309','2番人気の複勝率',
        '― 1番人気（60%）を上回る「最強人気ゾーン」―',
        note='2番人気 = 過去10年 最も期待値が高い人気',char='ginyo',page=2),
    big_num_slide(3,'②','ギーニョデータ解析','#16a34a',
        '100 %','#16a34a','G1前走1着の複勝率',
        '― 阪神JFからの直行ローテ　過去10年 全馬複勝圏 ―',
        note='前代未聞のデータ　→　スターアニスに直結',char='ginyo',page=3),
    big_num_slide(4,'③','ギーニョデータ解析','#e8136e',
        '80 %','#e8136e','上がり3F　1位馬の複勝率',
        '― 直線で一番切れる馬が主役になるレース ―',
        note='上がり3F最速馬 → 勝率40% / 複勝率80%',char='goto',page=4),
    big_num_slide(5,'④','ギーニョデータ解析','#dc2626',
        '0 %','#dc2626','10番人気以下の複勝率',
        '― 人気薄は完全消し。上位人気に絞り込む ―',
        note='穴馬を買う必要はゼロ　→　上位8番人気内に集中',char='ginyo',page=5),
    big_num_slide(6,'⑤','ギーニョデータ解析','#ea580c',
        '5 %','#ea580c','G2前走1着の複勝率',
        '― チューリップ賞前走は見かけ上強そうでも危険ゾーン ―',
        note='G2前走1着 = 過去10年 最大の罠データ',char='goto',page=6),
    s07(),
    s08(),
    score_slide(9, by_sougou[0], '#e8136e', '総合スコア 1 位',
        by_sougou[0]['sougouScore'], by_sougou[0]['sougouRank'], '#e8136e',
        '単勝×複勝 バランス総合評価', page=9, char='goto'),
    score_slide(10, by_tan[0], '#b45309', '単勝スコア 1 位',
        by_tan[0]['tanPct'], by_tan[0]['tanRank'], '#b45309',
        '勝ち馬スコア最上位', page=10, char='ginyo'),
    s11(),
    s12(),
]

# ══ HTML テンプレート組み立て ═══════════════════
slides_html = '\n'.join(slides)
total = len(slides)

HTML = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>桜花賞徹底解析 2026</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#1a1a1a; font-family:"Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif; overflow:hidden; }}
  #viewer {{ width:100vw; height:100vh; display:flex; align-items:center; justify-content:center; }}
  .slide-container {{ position:relative; }}
  .slide {{ display:none; width:100%; height:100%; }}
  .slide.active {{ display:block; }}
  /* ナビ */
  #nav {{ position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
          display:flex; gap:12px; align-items:center; z-index:100; }}
  #nav button {{ background:rgba(255,255,255,0.15); color:white; border:1px solid rgba(255,255,255,0.3);
                 padding:8px 20px; border-radius:20px; cursor:pointer; font-size:0.9em;
                 backdrop-filter:blur(4px); transition:background 0.2s; }}
  #nav button:hover {{ background:rgba(255,255,255,0.3); }}
  #counter {{ color:rgba(255,255,255,0.7); font-size:0.85em; min-width:60px; text-align:center; }}
  #progress {{ position:fixed; top:0; left:0; height:3px; background:#e8136e; transition:width 0.3s; z-index:200; }}
  /* 印刷 */
  @media print {{
    body {{ background:white; overflow:visible; }}
    #nav, #progress {{ display:none; }}
    #viewer {{ width:auto; height:auto; display:block; overflow:visible; }}
    .slide-container {{ width:267mm; height:150.4mm; page-break-after:always; overflow:hidden; }}
    .slide {{ display:block !important; width:100%; height:100%; }}
  }}
</style>
</head>
<body>
<div id="progress"></div>
<div id="viewer">
  <div class="slide-container" id="sc">
{slides_html}
  </div>
</div>
<div id="nav">
  <button onclick="go(-1)">◀ 前へ</button>
  <span id="counter">1 / {total}</span>
  <button onclick="go(1)">次へ ▶</button>
  <button onclick="window.print()" style="background:rgba(232,19,110,0.4)">🖨 PDF保存</button>
</div>
<script>
  let cur = 0;
  const slides = document.querySelectorAll('.slide');
  const N = slides.length;
  function show(n) {{
    slides[cur].classList.remove('active');
    cur = (n + N) % N;
    slides[cur].classList.add('active');
    document.getElementById('counter').textContent = (cur+1) + ' / ' + N;
    document.getElementById('progress').style.width = ((cur+1)/N*100) + '%';
  }}
  function go(d) {{ show(cur + d); }}
  document.addEventListener('keydown', e => {{
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') go(1);
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp') go(-1);
  }});
  // スライドサイズ動的調整
  function resize() {{
    const vw = window.innerWidth, vh = window.innerHeight - 60;
    const sc = document.getElementById('sc');
    const ratio = 16/9;
    let w = vw, h = vw / ratio;
    if (h > vh) {{ h = vh; w = vh * ratio; }}
    sc.style.width = w + 'px'; sc.style.height = h + 'px';
    sc.style.fontSize = (w / 960) + 'em';
  }}
  window.addEventListener('resize', resize);
  resize();
  show(0);
</script>
</body>
</html>'''

out = os.path.join(BASE, '桜花賞徹底解析2026_v3.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'✅ 完成: {out}')
print(f'   スライド数: {total}')
print(f'   ファイルサイズ: {os.path.getsize(out)//1024} KB')
print()
print('使い方:')
print('  - Safariで開く → 矢印キーまたはボタンでスライド切り替え')
print('  - 「PDF保存」ボタン or Cmd+P → PDFとして保存（用紙:A4横）')
