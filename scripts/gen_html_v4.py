#!/usr/bin/env python3
"""桜花賞徹底解析 v4 — 14スライド HTML
・イラストは表紙のみ（ギーニョ小さくワンポイント）
・全スライド右上に「桜花賞解析 2026」表示
・ティザー→解説ペアで「次が見たい！」仕掛け
・買いの5ヶ条 / 消しの5ヶ条
"""
import json, os, base64, html as H

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE,'docs/data/race-notes/2026-04-12-hanshin-11r.json'),encoding='utf-8') as f:
    DATA = json.load(f)
HORSES = DATA['horses']

# ══ スコア計算 ══
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
score_map = {d['name']:d for d in horse_data}

# ══ 画像 base64 ══
def img_b64(path):
    if not os.path.exists(path): return ''
    with open(path,'rb') as f: data=f.read()
    ext='jpg' if path.endswith('.jpg') else 'png'
    return f'data:image/{ext};base64,{base64.b64encode(data).decode()}'
IMG_GINYO = img_b64(os.path.join(BASE,'ginyo.jpg'))

e = H.escape

# ══ 共通部品 ══
CORNER = '<div class="corner-label">🌸 桜花賞解析 2026</div>'

def bar_html(pct, color, height=10):
    w = min(pct * 100, 100)
    return f'<div style="background:rgba(0,0,0,0.08);border-radius:4px;height:{height}px;overflow:hidden"><div style="width:{w:.1f}%;height:100%;background:{color};border-radius:4px;transition:width .5s"></div></div>'

def grade_badge(g, size='0.72em'):
    if not g or g in ['—','']:
        return f'<span style="font-size:{size};color:#aaa">—</span>'
    color = '#dc2626' if 'S' in str(g) else '#b45309' if 'A' in str(g) else '#6b505a' if 'B' in str(g) else '#9ca3af'
    return f'<span style="font-size:{size};font-weight:700;color:{color}">{e(str(g))}</span>'

def section_block(icon, title, body_html, border_color='#e8136e', bg='rgba(232,19,110,0.04)'):
    return f'''<div style="border-left:3px solid {border_color};background:{bg};border-radius:0 6px 6px 0;padding:6px 10px;margin:5px 0">
  <div style="font-weight:700;font-size:0.75em;color:{border_color};margin-bottom:3px">{icon}　{e(title)}</div>
  <div style="font-size:0.72em;color:#2d1a22;line-height:1.55">{body_html}</div>
</div>'''

# ══ スライド生成 ══

# ─── Slide 1: 表紙 ──────────────────────────────
def s01():
    return f'''<div class="slide" id="s1">
  <div style="background:#e8136e;width:100%;height:100%;position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:4px;background:#f5b731"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:4px;background:#f5b731"></div>
    <!-- 背景テクスチャ風グラデ -->
    <div style="position:absolute;right:0;top:0;width:45%;height:100%;background:linear-gradient(135deg,transparent 0%,rgba(255,255,255,0.06) 100%)"></div>
    <!-- G1バッジ -->
    <div style="position:absolute;left:6%;top:8%;background:#f5b731;color:#0f0a0c;font-weight:900;font-size:1.3em;padding:4px 18px;border-radius:20px;letter-spacing:0.1em">G 1</div>
    <!-- メインタイトル -->
    <div style="position:absolute;left:6%;top:17%;color:white;font-family:'Hiragino Mincho ProN','Yu Mincho','Georgia',serif;font-weight:900;font-size:5.5em;line-height:1;letter-spacing:0.04em">桜花賞</div>
    <!-- ゴールドライン -->
    <div style="position:absolute;left:6%;top:57%;width:45%;height:3px;background:#f5b731"></div>
    <!-- サブタイトル -->
    <div style="position:absolute;left:6%;top:61%;color:#f5b731;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2.3em;letter-spacing:0.2em">徹 底 解 析</div>
    <!-- 日時 -->
    <div style="position:absolute;left:6%;top:77%;color:rgba(255,230,240,0.9);font-size:0.78em">2026年4月12日（日）　阪神競馬場　芝1600m外　19頭立て</div>
    <div style="position:absolute;left:6%;top:85%;color:rgba(255,210,230,0.75);font-size:0.72em;font-style:italic">ギーニョ重賞データ解析 × 血統 × 特別ファクター</div>
    <!-- ギーニョ（右下ワンポイント） -->
    <img src="{IMG_GINYO}" style="position:absolute;right:4%;bottom:8%;width:14%;object-fit:contain;opacity:0.92">
    <!-- ロゴ -->
    <div style="position:absolute;left:0;bottom:5%;background:rgba(255,255,255,0.95);padding:6px 20px 6px 6%">
      <span style="color:#b4084b;font-weight:900;font-size:0.82em">UG競馬　競馬予想チャンネル</span>
    </div>
    {CORNER}
  </div>
</div>'''

# ─── Slide 2: 大数字「2番人気 70%」────────────────
def s02():
    return f'''<div class="slide" id="s2">
  <div style="background:#fff8f0;width:100%;height:100%;position:relative;overflow:hidden">
    {CORNER}
    <div class="data-badge" style="background:#b45309">① ギーニョデータ解析</div>
    <div class="big-number" style="color:#b45309">70<span style="font-size:0.45em">%</span></div>
    <div class="big-divider" style="background:#b45309"></div>
    <div class="big-label">2番人気の複勝率</div>
    <div class="big-sub">― 1番人気（60%）を<strong style="color:#b45309">上回る</strong>「最強人気ゾーン」。軸は2番人気から ―</div>
    <div class="note-pill" style="background:#b45309">2番人気 = 過去10年で最も期待値が高い人気　複勝70% 勝率50%</div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span class="free-tag">🆓 無料　2 / 14</span></div>
  </div>
</div>'''

# ─── Slide 3: G1前走1着 100% ──────────────────────
def s03():
    return f'''<div class="slide" id="s3">
  <div style="background:#f0fdf4;width:100%;height:100%;position:relative;overflow:hidden">
    {CORNER}
    <div class="data-badge" style="background:#15803d">② ギーニョデータ解析</div>
    <div class="big-number" style="color:#15803d">100<span style="font-size:0.35em">%</span></div>
    <div class="big-divider" style="background:#15803d"></div>
    <div class="big-label">G1前走1着の複勝率</div>
    <div class="big-sub">― 阪神JFからの直行ローテ。過去10年<strong style="color:#15803d">全馬複勝圏</strong>という前代未聞のデータ ―</div>
    <div class="note-pill" style="background:#15803d">ソダシ・リバティアイランド・アスコリピチェーノ・アルマヴェローチェ　すべて連対</div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span class="free-tag">🆓 無料　3 / 14</span></div>
  </div>
</div>'''

# ─── Slide 4: G2前走1着 5% ────────────────────────
def s04():
    return f'''<div class="slide" id="s4">
  <div style="background:#fff1f2;width:100%;height:100%;position:relative;overflow:hidden">
    {CORNER}
    <div class="data-badge" style="background:#dc2626">③ ギーニョデータ解析</div>
    <div class="big-number" style="color:#dc2626">5<span style="font-size:0.45em">%</span></div>
    <div class="big-divider" style="background:#dc2626"></div>
    <div class="big-label">G2前走1着の複勝率</div>
    <div class="big-sub">― チューリップ賞・フィリーズレビューを<strong style="color:#dc2626">勝ってきた馬は消し</strong>。実力があっても割り引くのがデータの指す正解 ―</div>
    <div class="note-pill" style="background:#dc2626">G2前走1着 = 過去10年　最大の「罠データ」　※アランカール・エレガンスアスクに直結</div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span class="free-tag">🆓 無料　4 / 14</span></div>
  </div>
</div>'''

# ─── Slide 5: 買いの5ヶ条 ──────────────────────────
def s05():
    items = [
        ('#15803d', '✅', 'G1前走1着は迷わず買い',
         '複勝率100%（過去10年・全頭連対）。阪神JFからの直行ローテは最高条件。'),
        ('#b45309', '✅', '2番人気を軸にしろ',
         '複勝率70%・勝率50%。1番人気（60%複勝）を上回る驚異の数字。'),
        ('#0891b2', '✅', '上がり3F最速馬を狙え',
         '勝率40%・複勝率80%。直線で一番切れる馬が主役になるレース。'),
        ('#6d28d9', '✅', '中9週以上の直行ローテは正解',
         '複勝率34.3%。阪神JF直行はこの条件も同時に満たす。'),
        ('#0f766e', '✅', 'キャリア3戦以内×前走2着は逆説の穴',
         '複勝率38.5%。少ない戦歴で阪神マイルに挑む馬は侮れない。'),
    ]
    rows = ''.join(f'''
<div style="display:flex;align-items:flex-start;gap:10px;background:white;border-radius:8px;padding:8px 12px;margin:5px 0;border-left:4px solid {col}">
  <span style="font-size:1.2em;flex-shrink:0">{icon}</span>
  <div>
    <div style="font-weight:700;font-size:0.88em;color:{col}">{e(title)}</div>
    <div style="font-size:0.72em;color:#4a3040;margin-top:2px;line-height:1.4">{e(desc)}</div>
  </div>
</div>''' for col, icon, title, desc in items)
    return f'''<div class="slide" id="s5">
  <div style="background:#f0fdf4;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:#15803d;padding:10px 16px;flex-shrink:0">
      <span style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.5em;letter-spacing:0.15em">🏆 桜花賞　買いの5ヶ条</span>
      <span style="color:rgba(220,252,231,0.8);font-size:0.72em;margin-left:12px">過去10年データが導く「勝ち組の絞り込み」</span>
    </div>
    <div style="flex:1;padding:8px 16px;overflow:hidden">{rows}</div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span class="free-tag">🆓 無料　5 / 14</span></div>
  </div>
</div>'''

# ─── Slide 6: 消しの5ヶ条 ──────────────────────────
def s06():
    items = [
        ('G2前走1着は全消し',
         '複勝率わずか5%。チューリップ賞・フィリーズレビュー勝ちはむしろ危険。',
         'アランカール・エレガンスアスク・ショウナンカリスに直結'),
        ('10番人気以下は完全消し',
         '複勝率0%。人気薄を買う必要は一切なし。上位8番人気以内に集中。',
         'アイニードユー・ルールザウェイヴ・ロンギングセリーヌ等'),
        ('アネモネS・フラワーS・紅梅S前走は問答無用消し',
         '過去10年 複勝率0%。ディアダイヤモンド・リリージョワ・ルールザウェイヴは3重消し。',
         ''),
        ('馬体重440〜459kgは危険ゾーン',
         '複勝率4.1%（460〜479kgのベストゾーン29.4%と雲泥の差）。',
         ''),
        ('前走6番人気以下は消し準拠',
         '複勝率2.1%。前走で人気薄だった馬は一気の巻き返しが効かないレース。',
         ''),
    ]
    rows = ''.join(f'''
<div style="display:flex;align-items:flex-start;gap:10px;background:white;border-radius:8px;padding:8px 12px;margin:5px 0;border-left:4px solid #dc2626">
  <span style="font-size:1.3em;flex-shrink:0">❌</span>
  <div style="flex:1">
    <div style="font-weight:700;font-size:0.88em;color:#dc2626">{e(title)}</div>
    <div style="font-size:0.72em;color:#4a3040;margin-top:2px;line-height:1.4">{e(desc)}</div>
    {f'<div style="font-size:0.66em;color:#9ca3af;margin-top:1px">{e(eg)}</div>' if eg else ''}
  </div>
</div>''' for title, desc, eg in items)
    return f'''<div class="slide" id="s6">
  <div style="background:#fff1f2;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:#dc2626;padding:10px 16px;flex-shrink:0">
      <span style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.5em;letter-spacing:0.15em">🚫 桜花賞　消しの5ヶ条</span>
      <span style="color:rgba(254,202,202,0.85);font-size:0.72em;margin-left:12px">データが明確に示す「捨て馬」の条件</span>
    </div>
    <div style="flex:1;padding:8px 16px;overflow:hidden">{rows}</div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span class="free-tag">🆓 無料　6 / 14</span></div>
  </div>
</div>'''

# ─── Slide 7: 血統解析 ─────────────────────────────
def s07():
    sires=[('キタサンブラック','66.7','3頭','ブラックチャリス','#b45309'),
           ('エピファネイア','28.6','7頭','アランカール','#e8136e'),
           ('ロードカナロア','22.2','多数','複は○ 単は×','#6b505a')]
    dams=[('ハーツクライ','50.0','2頭','フェスティバルヒル','#b45309'),
          ('クロフネ','42.9','7頭','','#0891b2'),
          ('ディープインパクト','0.0','多数','ルールザウェイヴ 消し','#dc2626')]
    def rows(data, bg_base):
        r=[]
        for i,(nm,pct,cnt,note,col) in enumerate(data):
            bg = bg_base if i%2==0 else 'white'
            pv = float(pct)/100
            medals=['🥇','🥈','🥉']
            r.append(f'''<div style="background:{bg};border-radius:6px;margin:3px 0;padding:6px 8px;border-left:3px solid {col}">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-weight:{'700' if i==0 else '500'};font-size:0.82em">{medals[i]}　{e(nm)}</span>
    <span style="font-weight:700;font-size:0.82em;color:{col}">複勝 {pct}%</span>
  </div>
  <div style="margin:3px 0 2px">{bar_html(pv,col,6)}</div>
  <div style="font-size:0.65em;color:{col}">{e(cnt)}　{e(note)}</div>
</div>''')
        return ''.join(r)
    return f'''<div class="slide" id="s7">
  <div style="background:#fffbf5;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:#e8136e;padding:9px 16px;flex-shrink:0;text-align:center">
      <span style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.4em;letter-spacing:0.2em">🧬 血 統 解 析</span>
    </div>
    <div style="text-align:center;font-size:0.68em;color:#6b505a;padding:3px 0;font-style:italic;flex-shrink:0">
      桜花賞 父系・母父系 複勝率ランキング（過去10年）
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:6px 12px;overflow:hidden">
      <div>
        <div style="background:#b45309;color:white;font-weight:700;font-size:0.8em;padding:4px 8px;border-radius:4px 4px 0 0;text-align:center">父　系　ランキング</div>
        {rows(sires,'#fffaef')}
      </div>
      <div>
        <div style="background:#0891b2;color:white;font-weight:700;font-size:0.8em;padding:4px 8px;border-radius:4px 4px 0 0;text-align:center">母父系　ランキング</div>
        {rows(dams,'#f0faff')}
      </div>
    </div>
    <div style="margin:0 12px 4px;background:white;border-left:3px solid #f5b731;padding:5px 10px;border-radius:0 4px 4px 0;font-size:0.68em;color:#2d1a22;flex-shrink:0">
      <strong>血統総括：</strong>ブラックチャリス（父キタサン66.7%）とフェスティバルヒル（母父ハーツ50%）が血統最上位。ロードカナロア産駒は複勝○・単勝×の使い分けが合理的。
    </div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span class="free-tag">🆓 無料　7 / 14</span></div>
  </div>
</div>'''

# ─── Slide 8: ティザー「単勝キングは...」──────────────
def s08():
    sc = score_map['スターアニス']
    return f'''<div class="slide" id="s8">
  <div style="background:#1a0a10;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    {CORNER.replace('color:#e8136e','color:rgba(245,183,49,0.8)').replace('background:rgba','background:rgba')}
    <!-- 背景グロー -->
    <div style="position:absolute;top:30%;left:50%;transform:translate(-50%,-50%);width:60%;height:60%;background:radial-gradient(circle,rgba(232,19,110,0.15) 0%,transparent 70%)"></div>
    <!-- タイトル -->
    <div style="color:rgba(255,210,230,0.7);font-size:0.85em;letter-spacing:0.3em;margin-bottom:10px;text-transform:uppercase">SAKURASHO 2026</div>
    <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2.4em;text-align:center;line-height:1.3">
      桜花賞<br><span style="color:#f5b731">単勝キング</span>は...
    </div>
    <!-- ヒントカード -->
    <div style="display:flex;gap:10px;margin:20px 0">
      <div class="hint-card">ZI 全馬最上位<br><strong style="font-size:1.4em;color:#f5b731">132</strong></div>
      <div class="hint-card">前走<br><strong style="font-size:1.1em;color:#f5b731">G1・1着</strong></div>
      <div class="hint-card">調教評価<br><strong style="font-size:1.4em;color:#f5b731">3S</strong></div>
    </div>
    <!-- 次へ促進 -->
    <div style="color:rgba(255,255,255,0.5);font-size:0.78em;margin-top:10px;animation:pulse 2s infinite">▶　次のスライドへ</div>
    <div class="footer-bar" style="background:rgba(0,0,0,0.4);position:absolute;bottom:0;left:0;right:0">
      <span style="color:rgba(255,200,220,0.6)">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#ffe696;font-weight:700">🔒 有料　8 / 14</span>
    </div>
  </div>
</div>'''

# ─── Slide 9: スターアニス 単勝解説 ──────────────────
def s09():
    sc = score_map['スターアニス']
    h = sc['h']
    sp_note = h.get('specialNote','')
    return f'''<div class="slide" id="s9">
  <div style="background:#fffbf5;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#b45309,#92400e);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,237,213,0.75);font-size:0.68em;letter-spacing:0.2em">🏆 TANSHO KING</div>
        <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.7em;letter-spacing:0.05em">スターアニス</div>
      </div>
      <div style="text-align:right">
        <div style="color:#fcd34d;font-weight:700;font-size:1.1em">{e(str(sc["odds"]))}倍</div>
        <div style="color:rgba(255,237,213,0.75);font-size:0.68em">単勝スコア　#{sc["tanRank"]}位　/　複勝　#{sc["fukuRank"]}位</div>
      </div>
    </div>
    <!-- 2カラム -->
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.55fr;gap:8px;padding:8px;overflow:hidden">
      <!-- 左: スコア + キーデータ -->
      <div style="display:flex;flex-direction:column;gap:6px">
        <!-- スコアカード -->
        <div style="background:white;border-radius:8px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
          <div style="font-size:0.68em;color:#6b505a;margin-bottom:4px">単勝スコア</div>
          <div style="font-size:2em;font-weight:900;color:#b45309;font-family:'Hiragino Mincho ProN',serif;line-height:1">{sc["tanPct"]*100:.1f}<span style="font-size:0.4em">%</span></div>
          <div style="margin-top:4px">{bar_html(sc["tanPct"],"#b45309",8)}</div>
          <div style="display:flex;justify-content:space-between;margin-top:6px">
            <span style="font-size:0.65em;color:#6b505a">複勝</span>
            <span style="font-size:0.65em;font-weight:700;color:#15803d">{sc["fukuPct"]*100:.1f}%　#{sc["fukuRank"]}</span>
          </div>
          <div style="margin-top:2px">{bar_html(sc["fukuPct"],"#15803d",5)}</div>
        </div>
        <!-- キーバッジ -->
        <div style="background:white;border-radius:8px;padding:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
          <div style="font-size:0.65em;color:#6b505a;margin-bottom:4px;font-weight:700">KEY FACTOR</div>
          {''.join(f'<div style="background:#fffbf0;border-radius:4px;padding:3px 6px;margin:2px 0;font-size:0.68em;color:#92400e;font-weight:600">✦ {e(kf)}</div>' for kf in [
              f'前走 G1・1着（阪神JF）',
              f'ZI {h.get("sabcZI","")}　全馬最上位',
              f'調教評価 {h.get("conditionGradeTan","")}　三冠仕上げ',
              f'コース適性 {h.get("courseGrade","")}　阪神外マイル最適',
              f'外厩 {h.get("extFacility","")}',
          ])}
        </div>
        {f'<div style="background:#fffbf0;border-left:2px solid #f5b731;padding:5px 7px;border-radius:0 4px 4px 0;font-size:0.65em;color:#92400e;line-height:1.4">⭐ {e(sp_note)}</div>' if sp_note else ''}
      </div>
      <!-- 右: 分析テキスト -->
      <div style="display:flex;flex-direction:column;gap:5px;overflow:hidden">
        {section_block('📍','前走・ローテ',f'<strong>阪神JF（G1）1着</strong>　→　桜花賞直行（中9週）<br>{e(h.get("prevRaceNote","")[:90])}…','#b45309','#fffbf0')}
        {section_block('🏇','騎手ジャッジ（前走）',e(h.get("prevJockeyComment","")[:120])+'…','#b45309','#fffbf0')}
        {section_block('🥇','単勝評価',f'<strong>kinso {h.get("kinsoGrade","")} × pace {h.get("paceGrade","")} × G1前走1着×中9週</strong>　→　複勝100%データが三位一体。HペースのG1で後半345を安定して刻む能力は本物。','#b45309','#fffbf0')}
        {section_block('🏋️','調教・気配',e(h.get("conditionNote","")[:110])+'…','#6d28d9','rgba(109,40,217,0.04)')}
        {section_block('🧬','血統配合',e(h.get("bloodNote","")),'#0891b2','rgba(8,145,178,0.04)')}
      </div>
    </div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span style="color:#ffe696;font-weight:700">🔒 有料　9 / 14</span></div>
  </div>
</div>'''

# ─── Slide 10: ティザー「複勝キングは...」────────────
def s10():
    sc = score_map['スターアニス']
    return f'''<div class="slide" id="s10">
  <div style="background:#0d1f12;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    {CORNER}
    <div style="position:absolute;top:30%;left:50%;transform:translate(-50%,-50%);width:60%;height:60%;background:radial-gradient(circle,rgba(21,128,61,0.18) 0%,transparent 70%)"></div>
    <div style="color:rgba(187,247,208,0.6);font-size:0.85em;letter-spacing:0.3em;margin-bottom:10px">SAKURASHO 2026</div>
    <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2.4em;text-align:center;line-height:1.3">
      桜花賞<br><span style="color:#4ade80">複勝キング</span>は...
    </div>
    <div style="display:flex;gap:10px;margin:20px 0">
      <div class="hint-card" style="border-color:rgba(74,222,128,0.3)">G1前走<br><strong style="font-size:1.1em;color:#4ade80">複勝率100%</strong></div>
      <div class="hint-card" style="border-color:rgba(74,222,128,0.3)">複勝スコア<br><strong style="font-size:1.4em;color:#4ade80">#{sc["fukuRank"]}位</strong></div>
      <div class="hint-card" style="border-color:rgba(74,222,128,0.3)">外厩<br><strong style="font-size:0.9em;color:#4ade80">しがらき</strong></div>
    </div>
    <div style="color:rgba(255,255,255,0.5);font-size:0.78em;margin-top:10px">▶　次のスライドへ</div>
    <div class="footer-bar" style="background:rgba(0,0,0,0.4);position:absolute;bottom:0;left:0;right:0">
      <span style="color:rgba(187,247,208,0.5)">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#ffe696;font-weight:700">🔒 有料　10 / 14</span>
    </div>
  </div>
</div>'''

# ─── Slide 11: スターアニス 複勝解説 ──────────────────
def s11():
    sc = score_map['スターアニス']
    h = sc['h']
    sp_note = h.get('specialNote','')
    ana_note = h.get('raceAnaNote','')
    return f'''<div class="slide" id="s11">
  <div style="background:#f0fdf4;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:linear-gradient(135deg,#15803d,#166534);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(187,247,208,0.75);font-size:0.68em;letter-spacing:0.2em">🎯 FUKU KING</div>
        <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.7em;letter-spacing:0.05em">スターアニス</div>
      </div>
      <div style="text-align:right">
        <div style="color:#86efac;font-weight:700;font-size:1.1em">{e(str(sc["odds"]))}倍</div>
        <div style="color:rgba(187,247,208,0.75);font-size:0.68em">複勝スコア　#{sc["fukuRank"]}位</div>
      </div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.55fr;gap:8px;padding:8px;overflow:hidden">
      <div style="display:flex;flex-direction:column;gap:6px">
        <div style="background:white;border-radius:8px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
          <div style="font-size:0.68em;color:#6b505a;margin-bottom:4px">複勝スコア</div>
          <div style="font-size:2em;font-weight:900;color:#15803d;font-family:'Hiragino Mincho ProN',serif;line-height:1">{sc["fukuPct"]*100:.1f}<span style="font-size:0.4em">%</span></div>
          <div style="margin-top:4px">{bar_html(sc["fukuPct"],"#15803d",8)}</div>
          <div style="display:flex;justify-content:space-between;margin-top:6px">
            <span style="font-size:0.65em;color:#6b505a">単勝</span>
            <span style="font-size:0.65em;font-weight:700;color:#b45309">{sc["tanPct"]*100:.1f}%　#{sc["tanRank"]}</span>
          </div>
          <div style="margin-top:2px">{bar_html(sc["tanPct"],"#b45309",5)}</div>
        </div>
        <div style="background:white;border-radius:8px;padding:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
          <div style="font-size:0.65em;color:#6b505a;margin-bottom:4px;font-weight:700">複勝根拠</div>
          {''.join(f'<div style="background:#f0fdf4;border-radius:4px;padding:3px 6px;margin:2px 0;font-size:0.68em;color:#166534;font-weight:600">✦ {e(kf)}</div>' for kf in [
              'G1前走1着 × 中9週 = 複勝100%',
              f'pace {h.get("paceGrade","")}　Hペース対応済み',
              f'kinso {h.get("kinsoGrade","")}　近走最高評価',
              f'条件 {h.get("conditionGradeFuku","")}　複勝仕上げ◎',
              f'{ana_note}' if ana_note else '',
          ] if kf)}
        </div>
        {f'<div style="background:#f0fdf4;border-left:2px solid #4ade80;padding:5px 7px;font-size:0.65em;color:#166534;line-height:1.4">⭐ {e(sp_note[:120])}</div>' if sp_note else ''}
      </div>
      <div style="display:flex;flex-direction:column;gap:5px;overflow:hidden">
        {section_block('📍','前走・ローテ（複勝視点）',f'<strong>阪神JF（G1）1着</strong>　→　桜花賞直行｜ <strong>中9週 = 複勝率34.3%の好条件</strong>も同時クリア。','#15803d','rgba(21,128,61,0.04)')}
        {section_block('🎯','複勝評価',f'<strong>pace {h.get("paceGrade","")}（後半345/Hペース対応）× kinso {h.get("kinsoGrade","")}（近走S評価）× G1前走1着×中9週=複勝100%</strong>で複勝首位は盤石。HペースのG1でも後半345を安定して刻む能力が複勝最高確率を保証する。','#15803d','rgba(21,128,61,0.04)')}
        {section_block('💰','穴馬評価（3F統計）',f'0.8差 [0.8-0.9] 単回31 × 前走上がり2位（複勝率32.9%） × {sc["odds"]}倍　→　スコア0.15（△ 穴スコア低め）','#6d28d9','rgba(109,40,217,0.04)')}
        {section_block('🏋️','調教・気配評価',e(h.get("conditionNote","")[:130])+'…','#0891b2','rgba(8,145,178,0.04)')}
      </div>
    </div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span style="color:#ffe696;font-weight:700">🔒 有料　11 / 14</span></div>
  </div>
</div>'''

# ─── Slide 12: ティザー「穴馬キングは...」────────────
def s12():
    return f'''<div class="slide" id="s12">
  <div style="background:#12061e;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    {CORNER}
    <div style="position:absolute;top:30%;left:50%;transform:translate(-50%,-50%);width:60%;height:60%;background:radial-gradient(circle,rgba(109,40,217,0.2) 0%,transparent 70%)"></div>
    <div style="color:rgba(221,214,254,0.6);font-size:0.85em;letter-spacing:0.3em;margin-bottom:10px">SAKURASHO 2026</div>
    <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:2.4em;text-align:center;line-height:1.3">
      桜花賞<br><span style="color:#c084fc">穴馬キング</span>は...
    </div>
    <div style="display:flex;gap:10px;margin:20px 0">
      <div class="hint-card" style="border-color:rgba(192,132,252,0.3)">想定オッズ<br><strong style="font-size:1.4em;color:#c084fc">27.7倍</strong></div>
      <div class="hint-card" style="border-color:rgba(192,132,252,0.3)">父系複勝率<br><strong style="font-size:1.4em;color:#c084fc">66.7%</strong></div>
      <div class="hint-card" style="border-color:rgba(192,132,252,0.3)">外厩<br><strong style="font-size:0.9em;color:#c084fc">しがらき</strong></div>
    </div>
    <div style="color:rgba(255,255,255,0.4);font-size:0.72em;margin-top:6px">キタサンブラック産駒　／　フェアリーS G3 前走1着</div>
    <div style="color:rgba(255,255,255,0.5);font-size:0.78em;margin-top:12px">▶　次のスライドへ</div>
    <div class="footer-bar" style="background:rgba(0,0,0,0.4);position:absolute;bottom:0;left:0;right:0">
      <span style="color:rgba(221,214,254,0.5)">UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span>
      <span style="color:#ffe696;font-weight:700">🔒 有料　12 / 14</span>
    </div>
  </div>
</div>'''

# ─── Slide 13: ブラックチャリス 穴馬解説 ─────────────
def s13():
    sc = score_map['ブラックチャリス']
    h = sc['h']
    sp_note = h.get('specialNote','')
    ana_note = h.get('raceAnaNote','')
    return f'''<div class="slide" id="s13">
  <div style="background:#faf5ff;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column">
    {CORNER}
    <div style="background:linear-gradient(135deg,#6d28d9,#5b21b6);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(221,214,254,0.75);font-size:0.68em;letter-spacing:0.2em">⚡ ANA KING　データの相克</div>
        <div style="color:white;font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.7em;letter-spacing:0.05em">ブラックチャリス</div>
      </div>
      <div style="text-align:right">
        <div style="color:#d8b4fe;font-weight:700;font-size:1.1em">{e(str(sc["odds"]))}倍</div>
        <div style="color:rgba(221,214,254,0.75);font-size:0.68em">穴スコア　#{sc["anaRank"]}位　/　単 #{sc["tanRank"]}位</div>
      </div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.55fr;gap:8px;padding:8px;overflow:hidden">
      <!-- 左 -->
      <div style="display:flex;flex-direction:column;gap:6px">
        <div style="background:white;border-radius:8px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
          <div style="font-size:0.68em;color:#6b505a;margin-bottom:4px">穴馬スコア</div>
          <div style="font-size:1.8em;font-weight:900;color:#6d28d9;font-family:'Hiragino Mincho ProN',serif;line-height:1">{sc["anaScore"]:.2f}<span style="font-size:0.4em">pt</span></div>
          <div style="margin-top:4px">{bar_html(min(sc["anaScore"]/3.0,1.0),"#6d28d9",8)}</div>
          <div style="display:flex;justify-content:space-between;margin-top:6px">
            <span style="font-size:0.65em;color:#6b505a">単勝</span>
            <span style="font-size:0.65em;color:#b45309">{sc["tanPct"]*100:.1f}%　#{sc["tanRank"]}</span>
          </div>
          {bar_html(sc["tanPct"],"#b45309",5)}
          <div style="display:flex;justify-content:space-between;margin-top:4px">
            <span style="font-size:0.65em;color:#6b505a">複勝</span>
            <span style="font-size:0.65em;color:#15803d">{sc["fukuPct"]*100:.1f}%　#{sc["fukuRank"]}</span>
          </div>
          {bar_html(sc["fukuPct"],"#15803d",5)}
        </div>
        <!-- 相克カード -->
        <div style="background:#fffbf0;border-radius:8px;padding:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
          <div style="font-size:0.65em;font-weight:700;color:#6d28d9;margin-bottom:4px">データの相克</div>
          <div style="background:#f0fdf4;border-left:3px solid #15803d;padding:4px 7px;border-radius:0 4px 4px 0;margin-bottom:4px">
            <div style="font-size:0.68em;font-weight:700;color:#15803d">🧬 血統　最高評価</div>
            <div style="font-size:0.63em;color:#166534">父キタサン 複勝率66.7%</div>
          </div>
          <div style="background:#fff1f2;border-left:3px solid #dc2626;padding:4px 7px;border-radius:0 4px 4px 0">
            <div style="font-size:0.68em;font-weight:700;color:#dc2626">📊 レースデータ　消し根拠</div>
            <div style="font-size:0.63em;color:#991b1b">{e(ana_note or 'G3前走 ローテ減点')}</div>
          </div>
        </div>
        <div style="background:#f3e8ff;border-left:3px solid #6d28d9;padding:5px 7px;border-radius:0 4px 4px 0;font-size:0.65em;color:#5b21b6;line-height:1.4">
          💡 <strong>結論：</strong>複勝で少額バック推奨。血統最高 × データ消し = 複勝狙い一択
        </div>
      </div>
      <!-- 右 -->
      <div style="display:flex;flex-direction:column;gap:5px;overflow:hidden">
        {section_block('📍','前走・ローテ',f'<strong>フェアリーS（G3）1着</strong>（中山マイル）　→　桜花賞（阪神外回り）<br>{e(h.get("prevRaceNote","")[:90])}…','#6d28d9','rgba(109,40,217,0.04)')}
        {section_block('🏇','騎手ジャッジ（前走）',e(h.get("prevJockeyComment","")[:130])+'…','#6d28d9','rgba(109,40,217,0.04)')}
        {section_block('⚡','穴馬評価（3F統計）',f'前走上がり1位（0.5差）× フェアリーSG3前走1着 +0.8 × {sc["odds"]}倍<br>穴スコア{sc["anaScore"]:.2f}pt　→　<strong style="color:#6d28d9">穴馬キング</strong>認定','#6d28d9','rgba(109,40,217,0.04)')}
        {section_block('🏋️','調教・気配評価',e(h.get("conditionNote","")[:130])+'…','#0891b2','rgba(8,145,178,0.04)')}
        {section_block('🧬','血統配合ジャッジ',e(h.get("bloodNote","")),'#b45309','rgba(180,83,9,0.04)')}
      </div>
    </div>
    <div class="footer-bar"><span>UG競馬 競馬予想チャンネル　／　桜花賞徹底解析 2026</span><span style="color:#ffe696;font-weight:700">🔒 有料　13 / 14</span></div>
  </div>
</div>'''

# ─── Slide 14: 続きは... ────────────────────────────
def s14():
    return f'''<div class="slide" id="s14">
  <div style="background:#e8136e;width:100%;height:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    <div style="position:absolute;top:0;left:0;right:0;height:4px;background:#f5b731"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:4px;background:#f5b731"></div>
    <div style="position:absolute;inset:0;background:repeating-linear-gradient(45deg,transparent,transparent 40px,rgba(255,255,255,0.02) 40px,rgba(255,255,255,0.02) 80px)"></div>
    {CORNER}
    <div style="background:rgba(255,255,255,0.15);backdrop-filter:blur(4px);color:white;font-weight:700;font-size:0.82em;padding:5px 24px;border-radius:20px;margin-bottom:12px">◆　前半ブロック　ここまで　◆</div>
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:5.2em;color:white;letter-spacing:0.08em;line-height:1;margin-bottom:8px">続 き は...</div>
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-weight:900;font-size:1.7em;color:#f5b731;margin-bottom:14px">有料メンバーシップ　限定公開</div>
    <div style="display:flex;flex-direction:column;gap:6px;width:60%">
      {''.join(f'<div style="background:rgba(180,8,75,0.55);backdrop-filter:blur(4px);border-radius:24px;padding:7px 20px;color:white;font-size:0.8em;text-align:center">{e(p)}</div>' for p in [
          '▶ 全馬スコアランキング完全版（19頭）',
          '▶ 対抗馬・注意馬 詳細ファクター解説',
          '▶ 完全買い目提案（単勝〜3連単まで）',
      ])}
    </div>
    <div style="background:#f5b731;color:#0f0a0c;font-weight:900;font-size:0.88em;padding:10px 30px;border-radius:25px;margin-top:16px">▶　チャンネル登録・メンバーシップはこちら</div>
    <div style="position:absolute;bottom:8%;left:0;right:0;text-align:center;color:rgba(255,210,230,0.6);font-size:0.65em;font-style:italic">[チャンネルURL / QRコードをここに挿入]</div>
  </div>
</div>'''

# ══ 全スライド組み立て ══════════════════════════════
all_slides = [s01(),s02(),s03(),s04(),s05(),s06(),s07(),
              s08(),s09(),s10(),s11(),s12(),s13(),s14()]
N = len(all_slides)

HTML = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>桜花賞徹底解析 2026</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#111;font-family:"Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif;overflow:hidden}}
#viewer{{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}}
#sc{{position:relative;font-size:16px}}
.slide{{display:none;width:100%;height:100%}}
.slide.active{{display:block}}

/* コーナーラベル */
.corner-label{{position:absolute;top:6px;right:8px;background:rgba(232,19,110,0.12);color:#e8136e;
  font-size:0.58em;font-weight:700;padding:2px 8px;border-radius:10px;letter-spacing:0.05em;z-index:10}}

/* 大数字スライド共通 */
.data-badge{{position:absolute;left:3.5%;top:6%;color:white;font-weight:700;font-size:0.82em;padding:4px 18px;border-radius:20px}}
.big-number{{position:absolute;left:0;top:13%;width:75%;text-align:center;
  font-family:"Hiragino Mincho ProN","Yu Mincho","Georgia",serif;
  font-weight:900;font-size:8em;line-height:1}}
.big-divider{{position:absolute;left:12%;top:74%;width:50%;height:4px}}
.big-label{{position:absolute;left:0;top:78%;width:75%;text-align:center;
  font-family:"Hiragino Mincho ProN","Yu Mincho",serif;font-weight:900;font-size:1.45em;color:#1a0a10}}
.big-sub{{position:absolute;left:3%;top:87%;width:70%;text-align:center;font-size:0.73em;color:#6b505a}}
.note-pill{{position:absolute;left:50%;bottom:9%;transform:translateX(-50%);
  color:white;font-weight:700;font-size:0.65em;padding:4px 18px;border-radius:20px;white-space:nowrap}}

/* フッター */
.footer-bar{{background:#b4084b;height:5.5%;display:flex;align-items:center;
  justify-content:space-between;padding:0 2%;flex-shrink:0;font-size:0.6em}}
.footer-bar>span:first-child{{color:rgba(255,210,230,0.85)}}
.free-tag{{color:#f5b731;font-weight:700}}

/* ティザーヒントカード */
.hint-card{{background:rgba(255,255,255,0.06);border:1px solid rgba(245,183,49,0.25);
  border-radius:10px;padding:8px 16px;text-align:center;color:rgba(255,255,255,0.7);
  font-size:0.72em;line-height:1.6;min-width:100px;backdrop-filter:blur(4px)}}

/* ナビ */
#nav{{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
  display:flex;gap:10px;align-items:center;z-index:200}}
#nav button{{background:rgba(255,255,255,0.12);color:white;border:1px solid rgba(255,255,255,0.25);
  padding:6px 18px;border-radius:18px;cursor:pointer;font-size:0.85em;
  backdrop-filter:blur(6px);transition:background .2s}}
#nav button:hover{{background:rgba(255,255,255,0.25)}}
#counter{{color:rgba(255,255,255,0.6);font-size:0.82em;min-width:55px;text-align:center}}
#progress{{position:fixed;top:0;left:0;height:3px;background:#e8136e;transition:width .35s;z-index:300}}

@keyframes pulse{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}

@media print{{
  body{{background:white;overflow:visible}}
  #nav,#progress{{display:none !important}}
  #viewer{{width:auto;height:auto;display:block}}
  #sc{{width:277mm !important;height:155.8mm !important;font-size:16.5px !important;page-break-after:always}}
  .slide{{display:block !important}}
  .corner-label{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
}}
</style>
</head>
<body>
<div id="progress"></div>
<div id="viewer">
  <div id="sc">
{''.join(all_slides)}
  </div>
</div>
<div id="nav">
  <button onclick="go(-1)">◀ 前へ</button>
  <span id="counter">1 / {N}</span>
  <button onclick="go(1)">次へ ▶</button>
  <button onclick="window.print()" style="background:rgba(232,19,110,0.35)">🖨 PDF</button>
</div>
<script>
let cur=0;
const slides=document.querySelectorAll('.slide'), N={N};
function show(n){{
  slides[cur].classList.remove('active');
  cur=(n+N)%N;
  slides[cur].classList.add('active');
  document.getElementById('counter').textContent=(cur+1)+' / '+N;
  document.getElementById('progress').style.width=((cur+1)/N*100)+'%';
}}
function go(d){{show(cur+d)}}
document.addEventListener('keydown',e=>{{
  if(['ArrowRight','ArrowDown',' '].includes(e.key))go(1);
  if(['ArrowLeft','ArrowUp'].includes(e.key))go(-1);
}});
function resize(){{
  const vw=window.innerWidth,vh=window.innerHeight-50;
  const sc=document.getElementById('sc'),r=16/9;
  let w=vw,h=vw/r;
  if(h>vh){{h=vh;w=vh*r;}}
  sc.style.width=w+'px';sc.style.height=h+'px';
  sc.style.fontSize=(w/960)+'em';
}}
window.addEventListener('resize',resize);
resize();show(0);
</script>
</body>
</html>'''

out = os.path.join(BASE, '桜花賞徹底解析2026_v4.html')
with open(out,'w',encoding='utf-8') as f:
    f.write(HTML)
print(f'✅ 完成: {out}')
print(f'   スライド数: {N}枚')
print(f'   ファイルサイズ: {os.path.getsize(out)//1024} KB')
