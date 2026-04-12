#!/usr/bin/env python3
"""桜花賞徹底解析 v5 — 全21スライド
デザイン：白 × ビビッドピンク × ヒラギノ角ゴシック
コピー：「どっち買う？」「ここがポイント！」「血統深掘り！」全開
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
by_num = sorted(horse_data,key=lambda x:x['h'].get('num',99))

e = H.escape

# ══ 画像 base64 ══
def img_b64(path):
    if not os.path.exists(path): return ''
    with open(path,'rb') as f: data=f.read()
    ext='jpg' if path.endswith('.jpg') else 'png'
    return f'data:image/{ext};base64,{base64.b64encode(data).decode()}'
IMG_GINYO = img_b64(os.path.join(BASE,'ginyo.jpg'))

# ══ 共通部品 ══
def corner():
    """白背景スライド用（表紙・データスライド等）右上に余白あり想定"""
    return '''<div style="position:absolute;top:8px;right:12px;text-align:right;z-index:50;background:white;border-radius:6px;padding:3px 8px;box-shadow:0 1px 4px rgba(232,19,110,0.15)">
  <div style="color:#E8136E;font-size:0.82em;font-weight:800;letter-spacing:0.04em;line-height:1.15">桜花賞</div>
  <div style="color:#E8136E;font-size:0.82em;font-weight:800;letter-spacing:0.04em;line-height:1.15">2026</div>
</div>'''

def corner_in_header():
    """ヘッダーバー内埋め込み用 — ヘッダー右端に追加"""
    return '<div style="text-align:right;flex-shrink:0;margin-left:8px"><div style="color:rgba(255,255,255,0.9);font-size:0.78em;font-weight:800;letter-spacing:0.04em;line-height:1.15">桜花賞</div><div style="color:rgba(255,255,255,0.9);font-size:0.78em;font-weight:800;letter-spacing:0.04em;line-height:1.15">2026</div></div>'

def corner_below_header(top='15%'):
    """ヘッダーバーがある場合・ヘッダー直下に配置"""
    return f'<div style="position:absolute;top:{top};right:12px;text-align:right;z-index:50"><div style="color:#E8136E;font-size:0.82em;font-weight:800;letter-spacing:0.04em;line-height:1.15">桜花賞</div><div style="color:#E8136E;font-size:0.82em;font-weight:800;letter-spacing:0.04em;line-height:1.15">2026</div></div>'

def footer(pg, total=23, is_free=True):
    tag = '🆓 無料公開' if is_free else '🔒 有料限定'
    return f'''<div style="position:absolute;bottom:0;left:0;right:0;height:5%;background:#E8136E;display:flex;align-items:center;justify-content:space-between;padding:0 3%">
  <span style="color:rgba(255,255,255,0.75);font-size:0.58em">UG競馬 競馬予想チャンネル</span>
  <span style="color:white;font-size:0.62em;font-weight:700">{tag}　{pg} / {total}</span>
</div>'''

def bar(pct, color, h=7):
    w = min(pct*100, 100)
    return f'<div style="background:rgba(0,0,0,0.08);border-radius:3px;height:{h}px;overflow:hidden"><div style="width:{w:.1f}%;height:100%;background:{color};border-radius:3px"></div></div>'

def point_badge(text, color='#E8136E'):
    return f'<span style="background:{color};color:white;font-size:0.6em;font-weight:700;padding:2px 10px;border-radius:20px;letter-spacing:0.08em">{text}</span>'

def keyword_badge(text):
    """ここがポイント！ / 血統深掘り！ etc"""
    return f'<span style="background:#FFF0F7;color:#E8136E;font-size:0.62em;font-weight:700;padding:2px 10px;border-radius:4px;border:1px solid #FFD6EA">{text}</span>'

def profile_strip(h):
    """騎手・厩舎・外厩・父・母父・年齢・前走"""
    jockey  = h.get('jockey','')
    trainer = h.get('sabcTrainer','')
    ext     = h.get('extFacility','')
    sire    = h.get('sabcSire','')
    damsire = h.get('damSire','')
    age     = h.get('age','')
    prn     = h.get('prevRaceName','')
    prf     = h.get('prevFinish','')
    ext_short = ext.replace('ノーザンF','').replace('ファーム','F')
    items = [
        ('騎手', jockey),
        ('厩舎', trainer),
        ('外厩', ext_short or '在厩'),
        ('父', sire),
        ('母父', damsire),
        ('年齢', f'{age}歳'),
        ('前走', f'{prn} {prf}'),
    ]
    chips = ''.join(f'<span style="display:inline-flex;align-items:center;gap:3px;background:#F3F4F6;border-radius:4px;padding:2px 7px;font-size:0.6em"><span style="color:#9CA3AF;font-weight:600">{k}</span><span style="color:#111111;font-weight:700">{e(str(v))}</span></span>' for k,v in items if v)
    return f'<div style="display:flex;flex-wrap:wrap;gap:4px;padding:5px 14px;background:#FAFAFA;border-bottom:1px solid #F0F0F0">{chips}</div>'

def section_block(icon, label, body_html, color='#E8136E'):
    return f'''<div style="margin:4px 0">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
    <span style="font-size:0.6em;font-weight:700;color:{color}">{icon} {label}</span>
    <div style="flex:1;height:1px;background:rgba(232,19,110,0.12)"></div>
  </div>
  <div style="font-size:0.65em;color:#333;line-height:1.6;padding-left:2px">{body_html}</div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 1: 表紙
# ══════════════════════════════════════════
def s01():
    ginyo_img = f'<img src="{IMG_GINYO}" style="position:absolute;right:3%;bottom:7%;width:13%;object-fit:contain;opacity:0.92">' if IMG_GINYO else ''
    points_data = [
        (1,'ところでみなさん、どっち買う？','血統クイズで本命を炙り出す'),
        (2,'ギーニョデータ解析 3本勝負','2番人気・G1前走・重量ゾーン'),
        (3,'買いの5ヶ条 / 消しの5ヶ条','データが導く勝ち組の絞り込み'),
        (4,'血統深掘り！父系・母父系','キタサン・エピファ・ロードカナロア'),
    ]
    points_html = ''.join(
        f'<div style="display:flex;align-items:center;gap:10px;background:#FFF0F7;border-left:3px solid #E8136E;border-radius:0 6px 6px 0;padding:7px 12px">'
        f'<span style="font-size:1.0em;font-weight:800;color:#E8136E;min-width:26px;text-align:center">{num:02d}</span>'
        f'<div style="font-size:0.68em;font-weight:500;color:#111;line-height:1.4"><strong>{e(title)}</strong><br><span style="color:#6B7280">{e(sub)}</span></div>'
        f'</div>'
        for num,title,sub in points_data
    )
    return f'''<div class="slide active" id="s1">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden">
    <!-- 上部ピンクライン -->
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:#E8136E"></div>
    <!-- 左ピンクブロック -->
    <div style="position:absolute;left:0;top:0;width:40%;height:95%;background:#E8136E;display:flex;flex-direction:column;justify-content:center;padding:0 7%">
      <div style="background:white;color:#E8136E;font-size:0.72em;font-weight:800;padding:3px 14px;border-radius:20px;letter-spacing:0.1em;margin-bottom:6%;width:fit-content">G 1</div>
      <div style="color:white;font-size:3.4em;font-weight:800;line-height:1.05;letter-spacing:-0.01em">桜花賞<br>徹底解析</div>
      <div style="color:rgba(255,255,255,0.85);font-size:1.1em;font-weight:600;letter-spacing:0.18em;margin-top:4%">2026</div>
      <div style="color:rgba(255,255,255,0.65);font-size:0.62em;font-weight:400;margin-top:5%;line-height:1.9">
        2026年4月12日（日）<br>
        阪神競馬場　芝1600m外<br>
        牝馬3歳　19頭立て
      </div>
    </div>
    <!-- 右エリア -->
    <div style="position:absolute;left:40%;top:0;width:60%;height:95%;display:flex;flex-direction:column;justify-content:center;padding:5% 6%">
      <!-- 大背景数字 -->
      <div style="position:absolute;font-size:7em;font-weight:800;color:rgba(232,19,110,0.05);line-height:1;letter-spacing:-0.03em;left:50%;transform:translateX(-50%);white-space:nowrap">2026</div>
      <!-- 内容一覧 -->
      <div style="position:relative;z-index:1;display:flex;flex-direction:column;gap:9px;width:100%">
        <div style="font-size:0.68em;color:#9CA3AF;font-weight:600;letter-spacing:0.12em;margin-bottom:2px">このスライドで全部わかる ▼</div>
        {points_html}
      </div>
    </div>
    <!-- ドットグリッド -->
    <div style="position:absolute;right:4%;bottom:8%;display:grid;grid-template-columns:repeat(5,7px);gap:6px">
      {'<div style="width:7px;height:7px;border-radius:50%;background:rgba(232,19,110,0.15)"></div>'*20}
    </div>
    {ginyo_img}
    {corner()}
    {footer(1, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 2: どっち買う？血統クイズ
# ══════════════════════════════════════════
def s02():
    return f'''<div class="slide" id="s2">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:#E8136E"></div>
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>

    <!-- ヘッダー -->
    <div style="position:absolute;top:0;left:4px;right:0;height:14%;background:white;border-bottom:1px solid rgba(232,19,110,0.12);display:flex;align-items:center;padding:0 4% 0 5%;justify-content:space-between">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="background:#E8136E;color:white;font-size:0.68em;font-weight:700;padding:4px 16px;border-radius:20px;letter-spacing:0.06em">🤔 血統クイズ</div>
        <div style="font-size:0.72em;font-weight:700;color:#111">ところで、みなさん…　どっち買いますか？</div>
      </div>
      <div style="text-align:right"><div style="color:#E8136E;font-size:0.82em;font-weight:800;line-height:1.15">桜花賞</div><div style="color:#E8136E;font-size:0.82em;font-weight:800;line-height:1.15">2026</div></div>
    </div>

    <!-- メインコンテンツ -->
    <div style="position:absolute;top:14%;left:4px;right:0;bottom:5%;display:grid;grid-template-columns:1fr 80px 1fr;align-items:center;padding:2% 4%">

      <!-- 左：リアルインパクト陣営 -->
      <div style="background:#F0FDF4;border-radius:12px;padding:12px 14px;border:2px solid #16A34A;height:90%;display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="font-size:0.62em;font-weight:700;color:#16A34A;letter-spacing:0.1em;margin-bottom:3px">父系 A</div>
          <div style="font-size:1.3em;font-weight:800;color:#111;margin-bottom:6px">リアルインパクト</div>
          <!-- 成績表 -->
          <div style="background:white;border-radius:6px;padding:7px 10px;font-size:0.65em;margin-bottom:8px">
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;text-align:center;margin-bottom:4px">
              <div style="color:#9CA3AF;font-size:0.85em">1着</div><div style="color:#9CA3AF;font-size:0.85em">2着</div><div style="color:#9CA3AF;font-size:0.85em">3着</div><div style="color:#9CA3AF;font-size:0.85em">着外</div>
              <div style="font-weight:800;color:#111">1</div><div style="font-weight:800;color:#111">0</div><div style="font-weight:800;color:#111">1</div><div style="font-weight:800;color:#111">2</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;text-align:center;border-top:1px solid #E5E7EB;padding-top:4px">
              <div><div style="color:#9CA3AF;font-size:0.8em">勝率</div><div style="font-weight:800;color:#16A34A;font-size:1.1em">25.0%</div></div>
              <div><div style="color:#9CA3AF;font-size:0.8em">複勝率</div><div style="font-weight:800;color:#16A34A;font-size:1.1em">50.0%</div></div>
              <div><div style="color:#9CA3AF;font-size:0.8em">単回収</div><div style="font-weight:800;color:#16A34A;font-size:1.1em">405</div></div>
            </div>
          </div>
          {bar(0.5, '#16A34A', 8)}
        </div>
        <div style="background:#DCFCE7;border-left:3px solid #16A34A;border-radius:0 6px 6px 0;padding:6px 10px;margin-top:8px">
          <div style="font-size:0.65em;font-weight:700;color:#15803D">👑 この父系の出走馬</div>
          <div style="font-size:0.82em;font-weight:800;color:#111;margin-top:2px">スウィートハピネス</div>
          <div style="font-size:0.6em;color:#6B7280;margin-top:1px">想定 中穴　キャリア浅め</div>
        </div>
      </div>

      <!-- 中央 VS -->
      <div style="text-align:center">
        <div style="font-size:1.8em;font-weight:900;color:#E8136E;line-height:1">VS</div>
        <div style="font-size:0.58em;color:#9CA3AF;margin-top:4px">桜花賞<br>2026</div>
      </div>

      <!-- 右：ドレフォン陣営 -->
      <div style="background:#FFF0F7;border-radius:12px;padding:12px 14px;border:2px solid #E8136E;height:90%;display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="font-size:0.62em;font-weight:700;color:#E8136E;letter-spacing:0.1em;margin-bottom:3px">父系 B</div>
          <div style="font-size:1.3em;font-weight:800;color:#111;margin-bottom:6px">ドレフォン</div>
          <!-- 成績表 -->
          <div style="background:white;border-radius:6px;padding:7px 10px;font-size:0.65em;margin-bottom:8px">
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;text-align:center;margin-bottom:4px">
              <div style="color:#9CA3AF;font-size:0.85em">1着</div><div style="color:#9CA3AF;font-size:0.85em">2着</div><div style="color:#9CA3AF;font-size:0.85em">3着</div><div style="color:#9CA3AF;font-size:0.85em">着外</div>
              <div style="font-weight:800;color:#111">1</div><div style="font-weight:800;color:#111">0</div><div style="font-weight:800;color:#111">0</div><div style="font-weight:800;color:#111">9</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;text-align:center;border-top:1px solid #E5E7EB;padding-top:4px">
              <div><div style="color:#9CA3AF;font-size:0.8em">勝率</div><div style="font-weight:800;color:#DC2626;font-size:1.1em">10.0%</div></div>
              <div><div style="color:#9CA3AF;font-size:0.8em">複勝率</div><div style="font-weight:800;color:#DC2626;font-size:1.1em">10.0%</div></div>
              <div><div style="color:#9CA3AF;font-size:0.8em">単回収</div><div style="font-weight:800;color:#DC2626;font-size:1.1em">50</div></div>
            </div>
          </div>
          {bar(0.1, '#DC2626', 8)}
        </div>
        <div style="background:#FFF0F7;border-left:3px solid #E8136E;border-radius:0 6px 6px 0;padding:6px 10px;margin-top:8px">
          <div style="font-size:0.65em;font-weight:700;color:#E8136E">⭐ この父系の出走馬</div>
          <div style="font-size:0.82em;font-weight:800;color:#111;margin-top:2px">スターアニス</div>
          <div style="font-size:0.6em;color:#6B7280;margin-top:1px">想定 1〜3番人気　単勝スコア1位</div>
        </div>
      </div>
    </div>

    <!-- 下部 答えへ誘導 -->
    <div style="position:absolute;bottom:5.5%;left:50%;transform:translateX(-50%);white-space:nowrap">
      <span style="font-size:0.65em;color:#E8136E;font-weight:700">答えは次のスライドへ…　でも実は、答えはもう出ている　▶</span>
    </div>

    {footer(2, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 3: G1前走1着 100%
# ══════════════════════════════════════════
def s03():
    bar_data = [
        ('G1前走1着 ★', '100%', 1.0, '#E8136E', '700'),
        ('2番人気',      '70%',  0.70, '#9CA3AF', '400'),
        ('1番人気',      '60%',  0.60, '#9CA3AF', '400'),
        ('G2前走1着',    '5%',   0.05, '#DC2626', '400'),
    ]
    bars_html = ''.join(
        f'<div><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">'
        f'<span style="font-size:0.6em;color:{tc};font-weight:{tw}">{lab}</span>'
        f'<span style="font-size:0.72em;font-weight:700;color:{tc}">{pct}</span></div>'
        f'{bar(pv, tc, 7)}</div>'
        for lab,pct,pv,tc,tw in bar_data
    )
    return f'''<div class="slide" id="s3">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:#E8136E"></div>
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    {corner()}

    <!-- 大数字 左65% -->
    <div style="position:absolute;left:4px;top:3%;width:65%;height:87%;display:flex;flex-direction:column;justify-content:center;padding:0 5% 0 7%">
      <div style="font-size:0.7em;font-weight:600;color:#E8136E;letter-spacing:0.12em;margin-bottom:3%">ここがポイント！ G1前走1着のデータ</div>
      <div style="line-height:1;display:flex;align-items:baseline;gap:4px">
        <span style="font-size:9em;font-weight:800;color:#E8136E;letter-spacing:-0.03em">100</span>
        <span style="font-size:3.2em;font-weight:700;color:#E8136E">%</span>
      </div>
      <div style="font-size:1.25em;font-weight:700;color:#111;margin-top:3%;letter-spacing:0.04em">G1前走1着の複勝率</div>
      <div style="font-size:0.72em;color:#6B7280;margin-top:2%;line-height:1.7">
        ソダシ・リバティアイランド・アスコリピチェーノ・アルマヴェローチェ<br>
        <strong style="color:#E8136E">過去10年　全馬が馬券に絡んでいる。</strong><br>
        これは「運」じゃない。データが証明した「法則」だ。
      </div>
    </div>

    <!-- 右サイド -->
    <div style="position:absolute;right:0;top:3%;width:35%;height:87%;border-left:1px solid #FFD6EA;padding:5% 4%;display:flex;flex-direction:column;gap:10px;justify-content:center">
      <div style="font-size:0.62em;font-weight:700;color:#E8136E;letter-spacing:0.1em;border-bottom:1px solid #FFD6EA;padding-bottom:4%;margin-bottom:2%">前走別　複勝率比較</div>
      {bars_html}
      <div style="background:#FFF0F7;border-radius:6px;padding:6px 8px;margin-top:4px">
        <div style="font-size:0.6em;color:#E8136E;font-weight:700">今年の該当馬</div>
        <div style="font-size:0.78em;font-weight:800;color:#111;margin-top:2px">スターアニス</div>
        <div style="font-size:0.6em;color:#6B7280">阪神JF（G1）1着 → 直行</div>
      </div>
    </div>

    <!-- 底部メモ -->
    <div style="position:absolute;left:5%;bottom:6.5%;background:#E8136E;color:white;font-size:0.6em;font-weight:700;padding:4px 18px;border-radius:20px">
      G1前走1着 = 過去10年で最も信頼できる　「買い」のシグナル
    </div>

    {footer(3, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 4: 2番人気 70% & G2前走1着 5%
# ══════════════════════════════════════════
def s04():
    bars2_html = ''.join(
        f'<div><div style="display:flex;justify-content:space-between;font-size:0.62em;margin-bottom:2px">'
        f'<span style="color:{tc};font-weight:{tw}">{lab}</span>'
        f'<span style="color:{tc};font-weight:700">{pct}</span></div>'
        f'{bar(pv, tc, 6)}</div>'
        for lab,pct,pv,tc,tw in [
            ('2番人気 ★ 最強！', '70%', 0.70, '#E8136E', '700'),
            ('1番人気',          '60%', 0.60, '#9CA3AF', '400'),
            ('3番人気',          '52%', 0.52, '#9CA3AF', '400'),
        ]
    )
    keshi_names_html = ''.join(
        f'<div style="background:#FEF2F2;border-left:2px solid #DC2626;padding:3px 8px;border-radius:0 4px 4px 0;font-size:0.65em;color:#111;margin:2px 0">{n}</div>'
        for n in ['アランカール（G2前走3着 → 回避）','エレガンスアスク（G2前走1着 → 要注意）']
    )
    return f'''<div class="slide" id="s4">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:#E8136E"></div>
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    {corner()}

    <div style="position:absolute;top:3%;left:4px;right:0;bottom:5%;display:grid;grid-template-columns:1fr 1fr;gap:0">

      <!-- 左：2番人気70% -->
      <div style="padding:5% 5% 3% 6%;border-right:1px solid #F3F4F6;display:flex;flex-direction:column;justify-content:center">
        <div style="font-size:0.62em;font-weight:700;color:#6B7280;letter-spacing:0.1em;margin-bottom:3%">みんな知ってる…でも、これだけ差があった</div>
        <div style="display:flex;align-items:baseline;gap:4px;line-height:1">
          <span style="font-size:6em;font-weight:800;color:#E8136E;letter-spacing:-0.03em">70</span>
          <span style="font-size:2.2em;font-weight:700;color:#E8136E">%</span>
        </div>
        <div style="font-size:1.0em;font-weight:700;color:#111;margin-top:4%;margin-bottom:3%">2番人気の複勝率</div>
        <div style="display:flex;flex-direction:column;gap:7px">
          {bars2_html}
        </div>
        <div style="background:#FFF0F7;border-radius:6px;padding:6px 10px;margin-top:5%;font-size:0.62em;color:#E8136E;font-weight:700">
          ここがポイント！　勝率も50%。1番人気より強い。
        </div>
      </div>

      <!-- 右：G2前走1着5% -->
      <div style="padding:5% 5% 3% 6%;display:flex;flex-direction:column;justify-content:center">
        <div style="font-size:0.62em;font-weight:700;color:#DC2626;letter-spacing:0.1em;margin-bottom:3%">え、これ知らずに買ってた？　衝撃の消しデータ</div>
        <div style="display:flex;align-items:baseline;gap:4px;line-height:1">
          <span style="font-size:6em;font-weight:800;color:#DC2626;letter-spacing:-0.03em">5</span>
          <span style="font-size:2.2em;font-weight:700;color:#DC2626">%</span>
        </div>
        <div style="font-size:1.0em;font-weight:700;color:#111;margin-top:4%;margin-bottom:3%">G2前走1着の複勝率</div>
        <div style="background:#FEF2F2;border-radius:8px;padding:8px 10px;font-size:0.65em;color:#991B1B;line-height:1.6">
          チューリップ賞・フィリーズレビューを<strong>勝ってきた馬</strong>が<br>
          なぜか桜花賞で壊滅する「罠データ」。<br>
          「前走勝ちだから安心」——その安心感が敗因。
        </div>
        <div style="margin-top:4%">
          <div style="font-size:0.6em;font-weight:700;color:#DC2626;margin-bottom:4px">🚫 今年の該当馬（消し候補）</div>
          {keshi_names_html}
        </div>
      </div>
    </div>

    {footer(4, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 5: 買いの5ヶ条
# ══════════════════════════════════════════
def s05():
    items = [
        ('#15803D','✅','G1前走1着は迷わず買い',
         '複勝率100%（過去10年・全頭連対）。阪神JFからの直行ローテは最高条件。迷った瞬間に負ける。'),
        ('#E8136E','✅','2番人気を軸にしろ',
         '複勝率70%・勝率50%。1番人気（60%）を上回る「最強人気ゾーン」。2番人気は弱い人気じゃない。'),
        ('#0891B2','✅','上がり3F最速馬を狙え',
         '勝率40%・複勝率80%。桜花賞の直線で一番切れる馬が主役になる。これは毎年のお約束。'),
        ('#6D28D9','✅','中9週以上の直行ローテは正解',
         '複勝率34.3%。間隔を開けてG1直行は正しいリフレッシュ策。しがらき・天栄帰りとの相性抜群。'),
        ('#B45309','✅','キャリア3戦以内×前走2着は逆説の穴',
         '複勝率38.5%。少ない経験でG1に挑む馬は「伸びしろ」の塊。未知の強さが潜んでいる。'),
    ]
    rows = ''.join(f'''<div style="display:flex;align-items:flex-start;gap:10px;background:white;border-radius:8px;padding:8px 12px;margin:4px 0;border-left:4px solid {col};box-shadow:0 1px 4px rgba(0,0,0,0.05)">
      <span style="font-size:1.1em;flex-shrink:0">{icon}</span>
      <div>
        <div style="font-weight:700;font-size:0.85em;color:{col}">{e(title)}</div>
        <div style="font-size:0.68em;color:#4B5563;margin-top:2px;line-height:1.45">{e(desc)}</div>
      </div>
    </div>''' for col,icon,title,desc in items)
    return f'''<div class="slide" id="s5">
  <div style="width:100%;height:100%;background:#F0FDF4;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#15803D"></div>
    <!-- ヘッダー -->
    <div style="background:#15803D;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <span style="color:white;font-weight:800;font-size:1.35em;letter-spacing:0.12em">🏆 桜花賞　買いの5ヶ条</span>
        <span style="color:rgba(220,252,231,0.8);font-size:0.7em;margin-left:12px">これを知らずに馬券を買うな</span>
      </div>
      {corner_in_header()}
    </div>
    <div style="flex:1;padding:6px 14px;overflow:hidden">{rows}</div>
    {footer(5, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 6: 消しの5ヶ条
# ══════════════════════════════════════════
def s06():
    items = [
        ('G2前走1着は全消し',
         '複勝率わずか5%。チューリップ賞・フィリーズレビューを勝ってきた馬は「罠」。自信満々に消せ。',
         'アランカール・エレガンスアスク等'),
        ('10番人気以下は完全消し',
         '複勝率0%。10番人気以下に1円も使う理由はない。その分を本命・対抗に集中。',
         '全ての二桁人気馬'),
        ('アネモネS・フラワーS・紅梅S前走は問答無用消し',
         '過去10年 複勝率0%。ディアダイヤモンド・リリージョワは三重苦。',
         'データに例外なし'),
        ('馬体重440〜459kgは危険ゾーン',
         '複勝率4.1%（460〜479kgの29.4%と雲泥の差）。小柄な馬は桜花賞に向かない。',
         '体重は大事な消しファクター'),
        ('前走6番人気以下は消し準拠',
         '複勝率2.1%。前走で人気薄だった馬が一気に巻き返すほど甘いG1ではない。',
         ''),
    ]
    rows = ''.join(f'''<div style="display:flex;align-items:flex-start;gap:10px;background:white;border-radius:8px;padding:8px 12px;margin:4px 0;border-left:4px solid #DC2626;box-shadow:0 1px 4px rgba(0,0,0,0.05)">
      <span style="font-size:1.2em;flex-shrink:0">❌</span>
      <div style="flex:1">
        <div style="font-weight:700;font-size:0.85em;color:#DC2626">{e(title)}</div>
        <div style="font-size:0.68em;color:#4B5563;margin-top:2px;line-height:1.45">{e(desc)}</div>
        {f'<div style="font-size:0.62em;color:#9CA3AF;margin-top:1px">→ {e(eg)}</div>' if eg else ''}
      </div>
    </div>''' for title,desc,eg in items)
    return f'''<div class="slide" id="s6">
  <div style="width:100%;height:100%;background:#FFF1F2;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#DC2626"></div>
    <!-- ヘッダー -->
    <div style="background:#DC2626;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <span style="color:white;font-weight:800;font-size:1.35em;letter-spacing:0.12em">🚫 桜花賞　消しの5ヶ条</span>
        <span style="color:rgba(254,202,202,0.85);font-size:0.7em;margin-left:12px">この馬を買ったら負ける</span>
      </div>
      {corner_in_header()}
    </div>
    <div style="flex:1;padding:6px 14px;overflow:hidden">{rows}</div>
    {footer(6, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 7: 血統解析（血統深掘り！）
# ══════════════════════════════════════════
def s07():
    sires=[('キタサンブラック','66.7',0.667,'3頭','ブラックチャリス','#B45309'),
           ('エピファネイア','28.6',0.286,'7頭','アランカール','#E8136E'),
           ('ロードカナロア','22.2',0.222,'多数','複○ 単×','#6B7280')]
    dams=[('ハーツクライ','50.0',0.50,'2頭','フェスティバルヒル','#B45309'),
          ('クロフネ','42.9',0.429,'7頭','穴で面白い','#0891B2'),
          ('ディープインパクト','0.0',0.0,'多数','ルールザウェイヴ → 消し','#DC2626')]
    medals=['🥇','🥈','🥉']
    def sire_row(data):
        rows=[]
        for i,(nm,pct,pv,cnt,note,col) in enumerate(data):
            rows.append(f'''<div style="background:{'#FFFBEF' if i%2==0 else 'white'};border-radius:6px;margin:3px 0;padding:6px 8px;border-left:3px solid {col}">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
    <span style="font-weight:{'700' if i==0 else '500'};font-size:0.8em">{medals[i]}　{e(nm)}</span>
    <span style="font-weight:700;font-size:0.8em;color:{col}">複勝 {pct}%</span>
  </div>
  <div style="margin-bottom:2px">{bar(pv,col,6)}</div>
  <div style="font-size:0.62em;color:{col}">{e(cnt)}出走　{e(note)}</div>
</div>''')
        return ''.join(rows)
    return f'''<div class="slide" id="s7">
  <div style="width:100%;height:100%;background:#FFFBF5;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <!-- ヘッダー -->
    <div style="background:#E8136E;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <span style="color:white;font-weight:800;font-size:1.35em;letter-spacing:0.15em">🧬 血統深掘り！</span>
        <span style="color:rgba(255,210,230,0.85);font-size:0.68em;margin-left:10px">父系・母父系 複勝率ランキング（過去10年）</span>
      </div>
      {corner_in_header()}
    </div>
    <div style="text-align:center;font-size:0.65em;color:#9CA3AF;padding:3px 0;font-style:italic;flex-shrink:0">
      「血統なんて関係ない」——そう思ってた人に見てほしいデータ
    </div>

    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:4px 12px 6px;overflow:hidden">
      <!-- 父系 -->
      <div>
        <div style="background:#B45309;color:white;font-weight:700;font-size:0.78em;padding:4px 8px;border-radius:4px 4px 0 0;text-align:center">父　系　ランキング</div>
        {sire_row(sires)}
      </div>
      <!-- 母父系 -->
      <div>
        <div style="background:#0891B2;color:white;font-weight:700;font-size:0.78em;padding:4px 8px;border-radius:4px 4px 0 0;text-align:center">母父系　ランキング</div>
        {sire_row(dams)}
      </div>
    </div>

    <!-- 血統総括 -->
    <div style="margin:0 12px 4px;background:white;border-left:3px solid #F59E0B;padding:5px 10px;border-radius:0 4px 4px 0;font-size:0.65em;color:#2D1A22;flex-shrink:0;line-height:1.55">
      <strong style="color:#B45309">血統総括：</strong>
      ブラックチャリス（父キタサン66.7%）＆フェスティバルヒル（母父ハーツ50%）が血統最上位。
      スターアニス（父ドレフォン10%）は<strong style="color:#DC2626">血統的には逆風</strong>だが、
      <strong style="color:#E8136E">G1前走1着データ×ZI132</strong>で他のファクターが全て補完している。
    </div>
    {footer(7, is_free=True)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 8: ティザー「単勝キングは...」
# ══════════════════════════════════════════
def s08():
    sc = score_map['スターアニス']
    hints8 = ''.join(
        f'<div style="background:white;border:2px solid #E8136E;border-radius:10px;padding:10px 14px;text-align:center;flex:1">'
        f'<div style="color:#9CA3AF;font-size:0.6em;margin-bottom:4px">{lbl}</div>'
        f'<div style="color:#E8136E;font-size:{fs}em;font-weight:800">{val}</div></div>'
        for lbl,val,fs in [
            ('ZI 全馬最上位','132','1.5'),('前走','G1・1着','1.1'),
            ('調教評価','3S','1.5'),('外厩','しがらき','0.9'),
        ]
    )
    return f'''<div class="slide" id="s8">
  <div style="width:100%;height:100%;background:#FFF0F7;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <span style="color:white;font-weight:800;font-size:1.2em;letter-spacing:0.1em">🔒 有料限定　本命発表</span>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 20px">
      <div style="color:#9CA3AF;font-size:0.65em;letter-spacing:0.4em;margin-bottom:10px">さあ、いよいよ本命発表</div>
      <div style="color:#111;font-weight:900;font-size:2.4em;text-align:center;line-height:1.25;margin-bottom:6px">
        桜花賞<br><span style="color:#E8136E">単勝キング</span>は...
      </div>
      <div style="display:flex;gap:10px;margin:18px 0;width:100%">
        {hints8}
      </div>
      <div style="color:#9CA3AF;font-size:0.72em;animation:pulse 2s infinite">次のスライドで正体を明かします　▶</div>
    </div>
    {footer(8, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 9: スターアニス 単勝解説
# ══════════════════════════════════════════
def s09():
    sc = score_map['スターアニス']
    h  = sc['h']
    sp = h.get('specialNote','')
    blood = h.get('bloodNote','')
    cond  = h.get('conditionNote','')
    joc_c = h.get('prevJockeyComment','')
    race_n= h.get('prevRaceNote','')
    return f'''<div class="slide" id="s9">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#E8136E,#B40050);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.62em;letter-spacing:0.2em;font-weight:700">🏆 TANSHO KING　単勝スコア 1位</div>
        <div style="color:white;font-weight:800;font-size:1.7em;letter-spacing:0.02em">スターアニス</div>
      </div>
      <div style="display:flex;align-items:flex-start;gap:10px">
        <div style="text-align:right">
          <div style="color:#FFD6EA;font-weight:700;font-size:1.1em">{e(str(sc["odds"]))}倍</div>
          <div style="color:rgba(255,210,230,0.7);font-size:0.62em">単#{sc["tanRank"]}位　複#{sc["fukuRank"]}位　穴#{sc["anaRank"]}位</div>
          <div style="display:flex;gap:5px;margin-top:3px;justify-content:flex-end">
            <span style="background:rgba(255,255,255,0.2);color:white;font-size:0.58em;padding:1px 7px;border-radius:10px;font-weight:700">単 #1</span>
            <span style="background:rgba(255,255,255,0.15);color:white;font-size:0.58em;padding:1px 7px;border-radius:10px">複 #2</span>
          </div>
        </div>
        {corner_in_header()}
      </div>
    </div>
    <!-- プロフィール行 -->
    {profile_strip(h)}
    <!-- ボディ 2カラム -->
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.5fr;gap:8px;padding:6px 10px;overflow:hidden">
      <!-- 左：スコア -->
      <div style="display:flex;flex-direction:column;gap:6px">
        <div style="background:#F3F4F6;border-radius:8px;padding:10px 12px">
          <div style="font-size:0.62em;color:#6B7280;margin-bottom:3px">単勝スコア</div>
          <div style="font-size:2.2em;font-weight:800;color:#E8136E;line-height:1">{sc["tanPct"]*100:.1f}<span style="font-size:0.4em">%</span></div>
          <div style="margin-top:4px">{bar(sc["tanPct"],"#E8136E",8)}</div>
          <div style="display:flex;justify-content:space-between;margin-top:5px">
            <span style="font-size:0.6em;color:#6B7280">複勝</span>
            <span style="font-size:0.6em;font-weight:700;color:#15803D">{sc["fukuPct"]*100:.1f}%　#{sc["fukuRank"]}</span>
          </div>
          {bar(sc["fukuPct"],"#15803D",5)}
        </div>
        <!-- KEY FACTOR -->
        <div style="background:#FFF0F7;border-radius:8px;padding:8px 10px">
          <div style="font-size:0.62em;font-weight:700;color:#E8136E;margin-bottom:4px;letter-spacing:0.08em">KEY FACTOR</div>
          {''.join(f'<div style="background:white;border-radius:4px;padding:3px 7px;margin:2px 0;font-size:0.65em;color:#B40050;font-weight:600">✦ {e(kf)}</div>' for kf in [
              f'前走 阪神JF（G1）1着',f'ZI {h.get("sabcZI","")}　全馬最上位',
              f'調教 {h.get("conditionGradeTan","")}　三冠仕上げ',
              f'コース {h.get("courseGrade","")}　阪神外回り最適',
              f'外厩 {h.get("extFacility","").replace("ノーザンF","")}',
          ])}
        </div>
        {f'<div style="background:#FFF9E6;border-left:3px solid #F59E0B;padding:5px 8px;border-radius:0 5px 5px 0;font-size:0.62em;color:#92400E;line-height:1.45">⭐ {e(sp[:110])}</div>' if sp else ''}
      </div>
      <!-- 右：分析 -->
      <div style="display:flex;flex-direction:column;gap:4px;overflow:hidden">
        {section_block('📍','前走・ローテ',f'<strong>阪神JF（G1）1着</strong>　→　桜花賞直行（中9週）<br>{e(race_n[:80])}…')}
        {section_block('🏇','騎手ジャッジ',e(joc_c[:110])+'…')}
        {section_block('🏋️','調教・気配',e(cond[:110])+'…','#6D28D9')}
        {section_block('🧬','血統深掘り！',e(blood),'#B45309')}
      </div>
    </div>
    {footer(9, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 10: ティザー「複勝キングは...」
# ══════════════════════════════════════════
def s10():
    sc = score_map['アランカール']
    h = sc['h']
    hints10 = ''.join(
        f'<div style="background:white;border:2px solid #15803D;border-radius:10px;padding:10px 14px;text-align:center;flex:1">'
        f'<div style="color:#9CA3AF;font-size:0.6em;margin-bottom:4px">{lbl}</div>'
        f'<div style="color:#15803D;font-size:{fs}em;font-weight:800">{val}</div></div>'
        for lbl,val,fs in [
            ('複勝スコア', f'#{sc["fukuRank"]}位', '1.5'),
            ('穴スコア',   f'#{sc["anaRank"]}位',  '1.5'),
            ('想定オッズ', f'{sc["odds"]}倍',       '1.2'),
            ('外厩',       h.get('extFacility','').replace('ノーザンF','').replace('ファーム','F'), '0.85'),
        ]
    )
    return f'''<div class="slide" id="s10">
  <div style="width:100%;height:100%;background:#F0FDF4;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#15803D"></div>
    <div style="background:#15803D;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <span style="color:white;font-weight:800;font-size:1.2em;letter-spacing:0.1em">🔒 有料限定　複勝キング発表</span>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 20px">
      <div style="color:#9CA3AF;font-size:0.65em;letter-spacing:0.4em;margin-bottom:10px">複勝で一番頼れる馬は？</div>
      <div style="color:#111;font-weight:900;font-size:2.4em;text-align:center;line-height:1.25;margin-bottom:6px">
        桜花賞<br><span style="color:#15803D">複勝キング</span>は...
      </div>
      <div style="display:flex;gap:10px;margin:18px 0;width:100%">
        {hints10}
      </div>
      <div style="color:#9CA3AF;font-size:0.72em">次のスライドで全データ公開　▶</div>
    </div>
    {footer(10, is_free=False)}
  </div>
</div>'''


# ══════════════════════════════════════════
# SLIDE 11: アランカール 複勝解説
# ══════════════════════════════════════════
def s11():
    sc = score_map['アランカール']
    h  = sc['h']
    sp    = h.get('specialNote','')
    blood = h.get('bloodNote','')
    cond  = h.get('conditionNote','')
    joc_c = h.get('prevJockeyComment','')
    race_n= h.get('prevRaceNote','')
    ana_n = h.get('raceAnaNote','')
    return f'''<div class="slide" id="s11">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#15803D"></div>
    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#15803D,#166534);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(187,247,208,0.8);font-size:0.62em;letter-spacing:0.2em;font-weight:700">🎯 FUKU KING　複勝スコア 1位</div>
        <div style="color:white;font-weight:800;font-size:1.7em">アランカール</div>
      </div>
      <div style="display:flex;align-items:flex-start;gap:10px">
        <div style="text-align:right">
          <div style="color:#86EFAC;font-weight:700;font-size:1.1em">{e(str(sc["odds"]))}倍</div>
          <div style="color:rgba(187,247,208,0.7);font-size:0.62em">単#{sc["tanRank"]}位　複#{sc["fukuRank"]}位　穴#{sc["anaRank"]}位</div>
          <div style="display:flex;gap:5px;margin-top:3px;justify-content:flex-end">
            <span style="background:rgba(255,255,255,0.2);color:white;font-size:0.58em;padding:1px 7px;border-radius:10px;font-weight:700">複 #1</span>
            <span style="background:rgba(255,255,255,0.15);color:white;font-size:0.58em;padding:1px 7px;border-radius:10px">穴 #2</span>
          </div>
        </div>
        {corner_in_header()}
      </div>
    </div>
    {profile_strip(h)}
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.5fr;gap:8px;padding:6px 10px;overflow:hidden">
      <div style="display:flex;flex-direction:column;gap:6px">
        <div style="background:#F3F4F6;border-radius:8px;padding:10px 12px">
          <div style="font-size:0.62em;color:#6B7280;margin-bottom:3px">複勝スコア</div>
          <div style="font-size:2.2em;font-weight:800;color:#15803D;line-height:1">{sc["fukuPct"]*100:.1f}<span style="font-size:0.4em">%</span></div>
          {bar(sc["fukuPct"],"#15803D",8)}
          <div style="display:flex;justify-content:space-between;margin-top:5px">
            <span style="font-size:0.6em;color:#6B7280">単勝</span>
            <span style="font-size:0.6em;font-weight:700;color:#E8136E">{sc["tanPct"]*100:.1f}%　#{sc["tanRank"]}</span>
          </div>
          {bar(sc["tanPct"],"#E8136E",5)}
        </div>
        <div style="background:#F0FDF4;border-radius:8px;padding:8px 10px">
          <div style="font-size:0.62em;font-weight:700;color:#15803D;margin-bottom:4px">複勝根拠</div>
          {''.join(f'<div style="background:white;border-radius:4px;padding:3px 7px;margin:2px 0;font-size:0.65em;color:#166534;font-weight:600">✦ {e(kf)}</div>' for kf in [
              f'G2前走3着 → データ罠を回避', 'しがらきリフレッシュ後の状態◎',
              f'穴スコア #{sc["anaRank"]}位　末脚爆発力',
              f'{ana_n[:45]}' if ana_n else '',
          ] if kf)}
        </div>
        {f'<div style="background:#FFF9E6;border-left:3px solid #F59E0B;padding:5px 8px;border-radius:0 5px 5px 0;font-size:0.62em;color:#92400E;line-height:1.45">⭐ {e(sp[:110])}</div>' if sp else ''}
      </div>
      <div style="display:flex;flex-direction:column;gap:4px;overflow:hidden">
        {section_block('📍','前走・ローテ',f'<strong>チューリップ賞（G2）3着</strong>　→　桜花賞直行<br><span style="color:#15803D;font-weight:700">ここがポイント！</span> G2前走3着 = データ罠を回避済み！<br>{e(race_n[:75])}…','#15803D')}
        {section_block('🏇','騎手ジャッジ',e(joc_c[:110])+'…','#15803D')}
        {section_block('🏋️','調教・気配',e(cond[:110])+'…','#6D28D9')}
        {section_block('🧬','血統深掘り！',e(blood),'#B45309')}
      </div>
    </div>
    {footer(11, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 12: ティザー「穴馬キングは...」
# ══════════════════════════════════════════
def s12():
    sc = score_map['ブラックチャリス']
    hints12 = ''.join(
        f'<div style="background:white;border:2px solid #6D28D9;border-radius:10px;padding:10px 14px;text-align:center;flex:1">'
        f'<div style="color:#9CA3AF;font-size:0.6em;margin-bottom:4px">{lbl}</div>'
        f'<div style="color:#6D28D9;font-size:{fs}em;font-weight:800">{val}</div></div>'
        for lbl,val,fs in [
            ('想定オッズ','27.7倍','1.4'),('父系複勝率','66.7%','1.4'),
            ('外厩','しがらき','0.9'),('前走','フェアリG3 1着','0.85'),
        ]
    )
    return f'''<div class="slide" id="s12">
  <div style="width:100%;height:100%;background:#FAF5FF;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#6D28D9"></div>
    <div style="background:#6D28D9;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <span style="color:white;font-weight:800;font-size:1.2em;letter-spacing:0.1em">🔒 有料限定　穴馬キング発表</span>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 20px">
      <div style="color:#9CA3AF;font-size:0.65em;letter-spacing:0.4em;margin-bottom:10px">血統データが激推しする穴馬…</div>
      <div style="color:#111;font-weight:900;font-size:2.4em;text-align:center;line-height:1.25;margin-bottom:6px">
        桜花賞<br><span style="color:#6D28D9">穴馬キング</span>は...
      </div>
      <div style="display:flex;gap:10px;margin:18px 0;width:100%">
        {hints12}
      </div>
      <div style="color:#9CA3AF;font-size:0.68em">キタサンブラック産駒　データの相克に挑む一頭</div>
      <div style="color:#9CA3AF;font-size:0.72em;margin-top:8px">▶　正体は次のスライドへ</div>
    </div>
    {footer(12, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 13: ブラックチャリス 穴馬解説
# ══════════════════════════════════════════
def s13():
    sc = score_map['ブラックチャリス']
    h  = sc['h']
    sp    = h.get('specialNote','')
    blood = h.get('bloodNote','')
    cond  = h.get('conditionNote','')
    joc_c = h.get('prevJockeyComment','')
    race_n= h.get('prevRaceNote','')
    ana_n = h.get('raceAnaNote','')
    return f'''<div class="slide" id="s13">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#6D28D9"></div>
    <!-- ヘッダー -->
    <div style="background:linear-gradient(135deg,#6D28D9,#5B21B6);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(221,214,254,0.8);font-size:0.62em;letter-spacing:0.2em;font-weight:700">⚡ ANA KING　穴スコア 1位　データの相克</div>
        <div style="color:white;font-weight:800;font-size:1.7em">ブラックチャリス</div>
      </div>
      <div style="display:flex;align-items:flex-start;gap:10px">
        <div style="text-align:right">
          <div style="color:#D8B4FE;font-weight:700;font-size:1.1em">{e(str(sc["odds"]))}倍</div>
          <div style="color:rgba(221,214,254,0.7);font-size:0.62em">単#{sc["tanRank"]}位　複#{sc["fukuRank"]}位　穴#{sc["anaRank"]}位</div>
          <div style="display:flex;gap:5px;margin-top:3px;justify-content:flex-end">
            <span style="background:rgba(255,255,255,0.2);color:white;font-size:0.58em;padding:1px 7px;border-radius:10px;font-weight:700">穴 #1</span>
          </div>
        </div>
        {corner_in_header()}
      </div>
    </div>
    {profile_strip(h)}
    <div style="flex:1;display:grid;grid-template-columns:1fr 1.5fr;gap:8px;padding:6px 10px;overflow:hidden">
      <div style="display:flex;flex-direction:column;gap:5px">
        <div style="background:#F3F4F6;border-radius:8px;padding:10px 12px">
          <div style="font-size:0.62em;color:#6B7280;margin-bottom:3px">穴スコア</div>
          <div style="font-size:2.2em;font-weight:800;color:#6D28D9;line-height:1">{sc["anaScore"]:.2f}<span style="font-size:0.35em">pt</span></div>
          {bar(min(sc["anaScore"]/3.0,1.0),"#6D28D9",8)}
          <div style="display:flex;justify-content:space-between;margin-top:5px">
            <span style="font-size:0.6em;color:#6B7280">単勝</span>
            <span style="font-size:0.6em;color:#E8136E">{sc["tanPct"]*100:.1f}%　#{sc["tanRank"]}</span>
          </div>
          {bar(sc["tanPct"],"#E8136E",5)}
          <div style="display:flex;justify-content:space-between;margin-top:3px">
            <span style="font-size:0.6em;color:#6B7280">複勝</span>
            <span style="font-size:0.6em;color:#15803D">{sc["fukuPct"]*100:.1f}%　#{sc["fukuRank"]}</span>
          </div>
          {bar(sc["fukuPct"],"#15803D",5)}
        </div>
        <!-- データの相克カード -->
        <div style="background:#F5F3FF;border-radius:8px;padding:8px 10px">
          <div style="font-size:0.62em;font-weight:700;color:#6D28D9;margin-bottom:5px">データの相克（葛藤ポイント！）</div>
          <div style="background:#F0FDF4;border-left:3px solid #15803D;padding:4px 8px;border-radius:0 4px 4px 0;margin-bottom:4px">
            <div style="font-size:0.65em;font-weight:700;color:#15803D">🧬 血統　最高評価</div>
            <div style="font-size:0.62em;color:#166534">父キタサン 複勝率66.7%</div>
          </div>
          <div style="background:#FEF2F2;border-left:3px solid #DC2626;padding:4px 8px;border-radius:0 4px 4px 0">
            <div style="font-size:0.65em;font-weight:700;color:#DC2626">📊 ローテ　消し根拠あり</div>
            <div style="font-size:0.62em;color:#991B1B">{e(ana_n[:55]) if ana_n else 'G3前走ローテ減点'}</div>
          </div>
        </div>
        <div style="background:#EDE9FE;border-left:3px solid #6D28D9;padding:5px 8px;border-radius:0 5px 5px 0;font-size:0.63em;color:#5B21B6;line-height:1.45">
          💡 <strong>結論：</strong>単勝は不要。複勝で少額バック推奨。
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:4px;overflow:hidden">
        {section_block('📍','前走・ローテ',f'<strong>フェアリーS（G3）1着</strong>（中山マイル）→ 桜花賞（阪神外）<br>{e(race_n[:80])}…','#6D28D9')}
        {section_block('🏇','騎手ジャッジ',e(joc_c[:110])+'…','#6D28D9')}
        {section_block('🏋️','調教・気配',e(cond[:110])+'…','#0891B2')}
        {section_block('🧬','血統深掘り！　キタサンブラック産駒の実力',e(blood),'#B45309')}
      </div>
    </div>
    {footer(13, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 14: 続きは有料
# ══════════════════════════════════════════
def s14():
    return f'''<div class="slide" id="s14">
  <div style="width:100%;height:100%;background:#E8136E;position:relative;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center">
    <div style="position:absolute;top:0;left:0;right:0;height:4px;background:#F5B731"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:4px;background:#F5B731"></div>
    <div style="position:absolute;inset:0;background:repeating-linear-gradient(45deg,transparent,transparent 40px,rgba(255,255,255,0.02) 40px,rgba(255,255,255,0.02) 80px)"></div>
    <div style="position:absolute;top:10px;right:14px;text-align:right">
      <div style="color:rgba(255,210,230,0.7);font-size:0.95em;font-weight:800;line-height:1.1">桜花賞</div>
      <div style="color:rgba(255,210,230,0.7);font-size:0.95em;font-weight:800;line-height:1.1">2026</div>
    </div>
    <div style="background:rgba(255,255,255,0.15);color:white;font-weight:700;font-size:0.8em;padding:5px 24px;border-radius:20px;margin-bottom:12px;backdrop-filter:blur(4px)">◆ 前半ブロック　ここまで ◆</div>
    <div style="font-weight:900;font-size:4.5em;color:white;letter-spacing:0.08em;line-height:1;margin-bottom:8px">続 き は...</div>
    <div style="font-weight:800;font-size:1.6em;color:#F5B731;margin-bottom:16px">有料メンバーシップ　限定公開</div>
    <div style="display:flex;flex-direction:column;gap:6px;width:62%">
      {''.join(f'<div style="background:rgba(180,8,75,0.55);border-radius:24px;padding:7px 20px;color:white;font-size:0.78em;text-align:center;backdrop-filter:blur(4px)">{e(p)}</div>' for p in [
          '▶ 全馬スコアランキング完全版（19頭）',
          '▶ 対抗馬・注意馬 詳細ファクター解説',
          '▶ 完全買い目提案（単勝〜3連単まで）',
          '▶ 最終予想宣言　これが答えだ',
      ])}
    </div>
    <div style="background:#F5B731;color:#0F0A0C;font-weight:900;font-size:0.85em;padding:10px 30px;border-radius:25px;margin-top:16px">▶ チャンネル登録・メンバーシップはこちら</div>
    <div style="position:absolute;bottom:8%;left:0;right:0;text-align:center;color:rgba(255,210,230,0.55);font-size:0.63em">[チャンネルURL / QRコードをここに挿入]</div>
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 15: 後半開幕「3強の正体」
# ══════════════════════════════════════════
def s15():
    tan1=by_tan[0]; fuku1=by_fuku[0]; ana1=by_ana[0]
    def king_card(title, icon, d, accent, sub):
        return f'''<div style="background:white;border:2px solid {accent};border-radius:12px;padding:12px 14px;text-align:center">
  <div style="font-size:1.6em;margin-bottom:4px">{icon}</div>
  <div style="color:{accent};font-weight:700;font-size:0.68em;letter-spacing:0.12em;margin-bottom:4px">{e(title)}</div>
  <div style="color:#111;font-weight:900;font-size:1.25em;margin-bottom:3px">{e(d["name"])}</div>
  <div style="color:#6B7280;font-size:0.62em">{e(str(d["odds"]))}倍　{e(sub)}</div>
</div>'''
    return f'''<div class="slide" id="s15">
  <div style="width:100%;height:100%;background:#FFF0F7;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:9px 16px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <span style="color:white;font-weight:800;font-size:1.35em;letter-spacing:0.12em">🔒 後半開幕　3強の正体</span>
        <span style="color:rgba(255,210,230,0.85);font-size:0.7em;margin-left:12px">すべて見せます</span>
      </div>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px 16px;gap:14px">
      <div style="color:#9CA3AF;font-size:0.6em;letter-spacing:0.4em">PREMIUM MEMBERS ONLY</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;width:90%">
        {king_card('単勝キング','🥇',tan1,'#E8136E',f'単勝スコア {tan1["tanPct"]*100:.1f}%')}
        {king_card('複勝キング','🎯',fuku1,'#15803D',f'複勝スコア {fuku1["fukuPct"]*100:.1f}%')}
        {king_card('穴馬キング','⚡',ana1,'#6D28D9',f'穴スコア {ana1["anaScore"]:.2f}pt')}
      </div>
      <div style="color:#9CA3AF;font-size:0.63em">次のスライドから全19頭の完全データを公開　▶</div>
    </div>
    {footer(15, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 16: 全19頭スコアランキング
# ══════════════════════════════════════════
def _score_row(d):
    """共通テーブル行生成（sougouRankベース印）"""
    h=d['h']; num=h.get('num',''); odds=d['odds']
    sr=d['sougouRank']; ar=d['anaRank']
    tr=d['tanRank']; fr=d['fukuRank']
    prn=h.get('prevRaceName','')
    is_keshi=any(x in prn for x in ['アネモネ','フラワー','紅梅']) or float(str(odds))>=80 or ('G2' in prn and str(h.get('prevFinish',''))=='1着')
    if is_keshi:    mark='✕'; mc='#DC2626'; bg='rgba(220,38,38,0.04)'; bold='400'
    elif sr==1:     mark='◎'; mc='#E8136E'; bg='rgba(232,19,110,0.07)'; bold='900'
    elif sr<=3:     mark='○'; mc='#15803D'; bg='rgba(21,128,61,0.06)';  bold='700'
    elif sr<=7:     mark='▲'; mc='#0891B2'; bg='rgba(8,145,178,0.04)';  bold='500'
    elif ar==1:     mark='☆'; mc='#6D28D9'; bg='rgba(109,40,217,0.05)'; bold='600'
    else:           mark='△'; mc='#9CA3AF'; bg='transparent';            bold='400'
    tw=min(d['tanPct']*100,100); fw=min(d['fukuPct']*100,100)
    tbar=f'<div style="background:rgba(232,19,110,0.15);height:5px;border-radius:2px;width:46px;display:inline-block;vertical-align:middle;overflow:hidden"><div style="width:{tw:.0f}%;height:100%;background:#E8136E"></div></div>'
    fbar=f'<div style="background:rgba(21,128,61,0.15);height:5px;border-radius:2px;width:46px;display:inline-block;vertical-align:middle;overflow:hidden"><div style="width:{fw:.0f}%;height:100%;background:#15803D"></div></div>'
    nm=d['name'][:6]+('…' if len(d['name'])>6 else '')
    return f'''<tr style="background:{bg};border-bottom:1px solid #F3F4F6">
  <td style="text-align:center;color:#9CA3AF;font-size:0.62em;padding:3px 4px;width:20px">{e(str(num))}</td>
  <td style="padding:3px 4px">
    <span style="font-size:0.95em;font-weight:900;color:{mc}">{mark}</span>
    <span style="font-size:0.7em;font-weight:{bold};color:{'#111' if sr<=3 else '#374151'};margin-left:3px">{e(nm)}</span>
  </td>
  <td style="text-align:right;font-size:0.62em;color:#6B7280;padding:3px 4px">{e(str(odds))}倍</td>
  <td style="padding:3px 5px">{tbar}<br><span style="font-size:0.5em;color:#E8136E">#{tr} {d["tanPct"]*100:.0f}%</span></td>
  <td style="padding:3px 5px">{fbar}<br><span style="font-size:0.5em;color:#15803D">#{fr} {d["fukuPct"]*100:.0f}%</span></td>
  <td style="text-align:center;font-size:0.58em;color:{'#6D28D9' if ar<=3 else '#D1D5DB'};font-weight:{'700' if ar<=3 else '400'};padding:3px 3px">{'★' if ar==1 else '◇' if ar<=3 else '·'}</td>
</tr>'''

def _score_table_header():
    return '''<thead><tr style="border-bottom:2px solid #E8136E">
  <th style="font-size:0.55em;color:#9CA3AF;padding:2px 4px;text-align:center">番</th>
  <th style="font-size:0.55em;color:#9CA3AF;padding:2px 4px;text-align:left">馬名</th>
  <th style="font-size:0.55em;color:#9CA3AF;padding:2px 4px;text-align:right">オッズ</th>
  <th style="font-size:0.55em;color:#E8136E;padding:2px 5px;text-align:center">単勝スコア</th>
  <th style="font-size:0.55em;color:#15803D;padding:2px 5px;text-align:center">複勝スコア</th>
  <th style="font-size:0.55em;color:#6D28D9;padding:2px 3px;text-align:center">穴</th>
</tr></thead>'''

def _score_legend():
    return '''<div style="font-size:0.6em;text-align:right;line-height:1.8">
  <span style="color:white">◎</span><span style="color:rgba(255,255,255,0.7)"> 本命　</span>
  <span style="color:rgba(255,255,255,0.9)">○</span><span style="color:rgba(255,255,255,0.7)"> 対抗　</span>
  <span style="color:rgba(255,255,255,0.9)">▲</span><span style="color:rgba(255,255,255,0.7)"> 注意　</span>
  <span style="color:rgba(255,255,255,0.9)">☆</span><span style="color:rgba(255,255,255,0.7)"> 穴　</span>
  <span style="color:rgba(255,255,255,0.9)">✕</span><span style="color:rgba(255,255,255,0.7)"> 消し</span>
</div>'''

def s16():
    rows1=''.join(_score_row(d) for d in by_num[:10])
    return f'''<div class="slide" id="s16">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:7px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.25em">COMPLETE SCORE BOARD　① / ②</div>
        <div style="color:white;font-weight:800;font-size:1.2em">全19頭　スコアランキング　馬番1〜10</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        {_score_legend()}
        {corner_in_header()}
      </div>
    </div>
    <div style="flex:1;overflow:hidden;padding:2px 8px">
      <table style="width:100%;border-collapse:collapse">
        {_score_table_header()}
        <tbody>{rows1}</tbody>
      </table>
    </div>
    {footer(16, is_free=False)}
  </div>
</div>'''


def s16b():
    rows2=''.join(_score_row(d) for d in by_num[10:])
    return f'''<div class="slide" id="s16b">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:7px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.25em">COMPLETE SCORE BOARD　② / ②</div>
        <div style="color:white;font-weight:800;font-size:1.2em">全19頭　スコアランキング　馬番11〜19</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        {_score_legend()}
        {corner_in_header()}
      </div>
    </div>
    <div style="flex:1;overflow:hidden;padding:2px 8px">
      <table style="width:100%;border-collapse:collapse">
        {_score_table_header()}
        <tbody>{rows2}</tbody>
      </table>
    </div>
    {footer(17, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 17: 対抗馬2頭（アランカール & ドリームコア）
# ══════════════════════════════════════════
def s17():
    def card(name, accent, role_label, verdict_label, verdict_body):
        sc=score_map[name]; h=sc['h']
        cond=h.get('conditionNote',''); blood=h.get('bloodNote','')
        joc=h.get('prevJockeyComment',''); sp=h.get('specialNote','')
        ran=h.get('raceAnaNote','')
        prof_items = [
            ('騎手',h.get('jockey','')),('外厩',h.get('extFacility','').replace('ノーザンF','')),
            ('父',h.get('sabcSire','')),('前走',f'{h.get("prevRaceName","")} {h.get("prevFinish","")}'),
        ]
        chips=''.join(f'<span style="background:#F3F4F6;border-radius:3px;padding:1px 5px;font-size:0.55em;color:#374151"><span style="color:{accent};font-weight:700">{k}</span> {e(str(v))}</span>' for k,v in prof_items if v)
        sp_html = f'<div style="background:#FFFBEB;border-radius:4px;padding:3px 8px;font-size:0.6em;color:#92400E;line-height:1.4">⭐ {e(sp[:90])}</div>' if sp else ''
        ran_html = f'<div style="background:{accent}0D;border-left:2px solid {accent};padding:3px 7px;border-radius:0 4px 4px 0;font-size:0.6em;color:#111;line-height:1.4">ここがポイント！ {e(ran)}</div>' if ran else ''
        return f'''<div style="background:white;border:2px solid {accent}55;border-radius:10px;display:flex;flex-direction:column;overflow:hidden">
  <div style="background:{accent}11;padding:8px 12px;border-bottom:2px solid {accent}33">
    <div style="color:{accent};font-size:0.6em;font-weight:700;letter-spacing:0.12em">{e(role_label)}</div>
    <div style="display:flex;align-items:baseline;justify-content:space-between">
      <div style="color:#111;font-weight:900;font-size:1.25em">{e(name)}</div>
      <div style="color:#6B7280;font-size:0.65em">{e(str(sc["odds"]))}倍</div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:4px">{chips}</div>
    <div style="display:flex;gap:7px;margin-top:5px">
      <div style="flex:1"><div style="font-size:0.55em;color:{accent};margin-bottom:1px">単勝 {sc["tanPct"]*100:.1f}%</div>{bar(sc["tanPct"],accent,5)}</div>
      <div style="flex:1"><div style="font-size:0.55em;color:#15803D;margin-bottom:1px">複勝 {sc["fukuPct"]*100:.1f}%</div>{bar(sc["fukuPct"],"#15803D",5)}</div>
      <div style="flex:1"><div style="font-size:0.55em;color:#6D28D9;margin-bottom:1px">穴 {sc["anaScore"]:.2f}pt</div>{bar(min(sc["anaScore"]/3,1),"#6D28D9",5)}</div>
    </div>
  </div>
  <div style="flex:1;padding:7px 10px;overflow:hidden;display:flex;flex-direction:column;gap:4px">
    {sp_html}
    {ran_html}
    <div style="font-size:0.6em;color:#374151;line-height:1.45">🏇 {e(joc[:95])}{"…" if len(joc)>95 else ""}</div>
    <div style="font-size:0.6em;color:#374151;line-height:1.45">🧬 血統深掘り！ {e(blood[:80])}{"…" if len(blood)>80 else ""}</div>
    <div style="background:{accent}0A;border:1px solid {accent}33;border-radius:6px;padding:5px 8px;margin-top:2px">
      <div style="font-size:0.62em;font-weight:700;color:{accent};margin-bottom:2px">{e(verdict_label)}</div>
      <div style="font-size:0.6em;color:#374151;line-height:1.4">{verdict_body}</div>
    </div>
  </div>
</div>'''

    c1=card('アランカール','#E8136E','対抗　複#1 穴#2',
        '🌸 総合最上位の対抗',
        '複勝スコア1位・穴スコア2位の二冠。G2前走3着でデータ罠を回避済み。しがらきリフレッシュ後の末脚は爆発的。本命を脅かす最右翼。')
    c2=card('ドリームコア','#0891B2','注目　クイーンCパターン特注',
        '🔵 スターズオンアース再現なるか',
        'クイーンC1着→2022スターズオンアース（7番人気1着）と完全同パターン。穴ボーナス+1.2。ただし調教は案外で割り引き必要。複勝で押さえたい。')
    return f'''<div class="slide" id="s17">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:7px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.2em">CONTENDER DEEP DIVE</div>
        <div style="color:white;font-weight:800;font-size:1.2em">対抗馬　徹底解剖　—　本命に続く2頭</div>
      </div>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:8px;overflow:hidden">
      {c1}{c2}
    </div>
    {footer(18, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 18: 注意馬 & 消し馬
# ══════════════════════════════════════════
def s18():
    chui=[d for d in by_fuku[2:6] if d['name'] not in ['スターアニス','アランカール']][:2]
    keshi=[]
    for d in horse_data:
        h=d['h']; prn=h.get('prevRaceName',''); odds=float(str(d['odds']))
        reasons=[]
        if any(x in prn for x in ['アネモネ','フラワー','紅梅']): reasons.append(f'前走{prn}複勝率0%')
        if odds>=80: reasons.append(f'{odds}倍超')
        elif odds>=30: reasons.append(f'低人気({odds}倍)')
        if 'G2' in prn and str(h.get('prevFinish',''))=='1着': reasons.append('G2前走1着5%罠')
        if reasons: keshi.append((d['name'],d['odds'],' / '.join(reasons[:2])))
    keshi.sort(key=lambda x:float(str(x[1])))

    def chui_row(d):
        h=d['h']; ran=h.get('raceAnaNote',''); sp=h.get('specialNote','')
        sp_html = '<div style="font-size:0.58em;color:#92400E">⭐ ' + e(sp[:75]) + '</div>' if sp else ''
        ran_html = '<div style="font-size:0.58em;color:#0891B2">ここがポイント！ ' + e(ran) + '</div>' if ran else ''
        return (
            '<div style="background:white;border:1px solid rgba(8,145,178,0.3);border-radius:8px;padding:7px 10px;margin-bottom:5px">'
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px">'
            '<div><span style="background:#0891B2;color:white;font-size:0.56em;padding:1px 5px;border-radius:8px;margin-right:4px">要注目</span>'
            f'<strong style="color:#111;font-size:0.88em">{e(d["name"])}</strong></div>'
            f'<span style="color:#6B7280;font-size:0.62em">{d["odds"]}倍　単#{d["tanRank"]} 複#{d["fukuRank"]}</span>'
            '</div>'
            '<div style="display:flex;gap:5px;margin-bottom:4px">'
            f'<div style="flex:1"><div style="font-size:0.55em;color:#E8136E">単{d["tanPct"]*100:.1f}%</div>{bar(d["tanPct"],"#E8136E",5)}</div>'
            f'<div style="flex:1"><div style="font-size:0.55em;color:#15803D">複{d["fukuPct"]*100:.1f}%</div>{bar(d["fukuPct"],"#15803D",5)}</div>'
            '</div>'
            + sp_html + ran_html +
            '</div>'
        )

    keshi_items=''.join(
        '<div style="display:flex;align-items:center;gap:5px;padding:3px 7px;border-radius:4px;background:#FEF2F2;margin:2px 0;border-left:2px solid #DC2626">'
        '<span style="color:#DC2626;font-weight:900;font-size:0.75em;flex-shrink:0">✕</span>'
        f'<span style="color:#111;font-size:0.63em;font-weight:600">{e(name)}</span>'
        f'<span style="color:#9CA3AF;font-size:0.56em;flex:1;text-align:right">{e(str(odds))}倍 {e(reason)}</span>'
        '</div>'
        for name,odds,reason in keshi
    )
    chui_rows = ''.join(chui_row(d) for d in chui)

    return f'''<div class="slide" id="s18">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:7px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.2em">WATCH &amp; ELIMINATE</div>
        <div style="color:white;font-weight:800;font-size:1.2em">注意馬　&amp;　「これは買わなくていい」消し馬リスト</div>
      </div>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1.1fr 0.9fr;gap:10px;padding:8px;overflow:hidden">
      <div>
        <div style="color:#0891B2;font-size:0.62em;font-weight:700;margin-bottom:4px">⚠️ 押さえ候補</div>
        {chui_rows}
        <div style="background:#EFF6FF;border:1px solid rgba(8,145,178,0.25);border-radius:6px;padding:6px 10px;margin-top:4px">
          <div style="font-size:0.6em;font-weight:700;color:#0891B2;margin-bottom:2px">💡 注意馬の扱い方</div>
          <div style="font-size:0.58em;color:#374151;line-height:1.5">軸にしない。余力がある場合のみ少額で押さえる。</div>
        </div>
      </div>
      <div>
        <div style="color:#DC2626;font-size:0.62em;font-weight:700;margin-bottom:4px">🚫 データ根拠あり消し馬</div>
        {keshi_items}
        <div style="background:#FEF2F2;border:1px solid rgba(220,38,38,0.25);border-radius:6px;padding:6px 10px;margin-top:5px">
          <div style="font-size:0.6em;font-weight:700;color:#DC2626;margin-bottom:2px">消しの黄金則</div>
          <div style="font-size:0.58em;color:#374151;line-height:1.5">消し馬に1円も使わないことが最大の収益最適化。浮いた資金を本命・対抗に集中。</div>
        </div>
      </div>
    </div>
    {footer(19, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 19: 単勝 + 複勝
# ══════════════════════════════════════════
def s19():
    tan1=by_tan[0]; fuku1=by_fuku[0]; ana1=by_ana[0]
    return f'''<div class="slide" id="s19">
  <div style="width:100%;height:100%;background:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.2em">STEP 1 / 3　まずはここから</div>
        <div style="color:white;font-weight:800;font-size:1.35em">🎯 単勝 · 複勝　合計 3点</div>
      </div>
      {corner_in_header()}
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:12px 16px;overflow:hidden">
      <!-- 単勝 -->
      <div style="background:#FFF0F7;border:2px solid #E8136E;border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:14px;position:relative;overflow:hidden">
        <div style="position:absolute;top:-16px;right:-16px;font-size:5em;opacity:0.04">🥇</div>
        <div style="background:#E8136E;color:white;font-size:0.6em;font-weight:700;padding:3px 14px;border-radius:20px;letter-spacing:0.1em;margin-bottom:10px">単勝　1点</div>
        <div style="font-size:0.75em;color:#9CA3AF;margin-bottom:4px">◎ 本命</div>
        <div style="font-weight:900;font-size:2.2em;color:#E8136E;line-height:1;margin-bottom:4px">{e(tan1["name"])}</div>
        <div style="font-size:0.75em;color:#6B7280;margin-bottom:10px">想定 {e(str(tan1["odds"]))}倍</div>
        <div style="background:white;border-radius:8px;padding:6px 10px;width:100%;text-align:center">
          <div style="font-size:0.6em;color:#E8136E;font-weight:700">なぜ単勝で買えるのか</div>
          <div style="font-size:0.58em;color:#374151;margin-top:2px;line-height:1.5">ZI132 × G1前走1着 × 調教3S<br>三冠データ揃い。軸確定。</div>
        </div>
      </div>
      <!-- 複勝 -->
      <div style="background:#F0FDF4;border:2px solid #15803D;border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:14px;position:relative;overflow:hidden">
        <div style="position:absolute;top:-16px;right:-16px;font-size:5em;opacity:0.04">🎯</div>
        <div style="background:#15803D;color:white;font-size:0.6em;font-weight:700;padding:3px 14px;border-radius:20px;letter-spacing:0.1em;margin-bottom:10px">複勝　2点</div>
        <div style="font-size:0.75em;color:#9CA3AF;margin-bottom:6px">複勝1位 ＋ 穴馬1位</div>
        <div style="display:flex;flex-direction:column;gap:6px;width:100%">
          <div style="background:white;border:1px solid #15803D44;border-radius:8px;padding:6px 10px;text-align:center">
            <div style="font-size:0.58em;color:#15803D;font-weight:600">複勝スコア #1</div>
            <div style="font-weight:800;font-size:1.2em;color:#111">{e(fuku1["name"])}</div>
            <div style="font-size:0.58em;color:#6B7280">{e(str(fuku1["odds"]))}倍　複勝{fuku1["fukuPct"]*100:.1f}%</div>
          </div>
          <div style="background:white;border:1px solid #6D28D944;border-radius:8px;padding:6px 10px;text-align:center">
            <div style="font-size:0.58em;color:#6D28D9;font-weight:600">穴スコア #1</div>
            <div style="font-weight:800;font-size:1.2em;color:#111">{e(ana1["name"])}</div>
            <div style="font-size:0.58em;color:#6B7280">{e(str(ana1["odds"]))}倍　穴{ana1["anaScore"]:.2f}pt</div>
          </div>
        </div>
      </div>
    </div>
    {footer(19, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 20: 馬単マルチ 12点
# ══════════════════════════════════════════
def s20():
    tan1=by_tan[0]
    aite_names = ['ブラックチャリス','アランカール','ディアダイヤモンド','ナムラコスモス','ドリームコア','フェスティバルヒル']
    aite_chips_html = ''.join(
        '<div style="background:white;border:2px solid #E8136E66;border-radius:10px;padding:5px 8px;text-align:center;flex:1;min-width:0">'
        '<div style="font-weight:800;font-size:0.72em;color:#111;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + n + '</div>'
        '<div style="font-size:0.52em;color:#E8136E;font-weight:600;margin-top:1px">' + str(score_map[n]["odds"]) + '倍</div>'
        '</div>'
        for n in aite_names
    )
    return f'''<div class="slide" id="s20">
  <div style="width:100%;height:100%;background:#FFF0F7;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.2em">STEP 2 / 3　馬単マルチ</div>
        <div style="color:white;font-weight:800;font-size:1.35em">🔗 馬単マルチ　12点</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <div style="background:rgba(255,255,255,0.2);border-radius:8px;padding:3px 12px;text-align:center">
          <div style="color:rgba(255,210,230,0.8);font-size:0.52em">合計点</div>
          <div style="color:white;font-weight:900;font-size:1.2em">12点</div>
        </div>
        {corner_in_header()}
      </div>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;padding:10px 14px;gap:10px;overflow:hidden">
      <!-- 軸馬 -->
      <div style="background:white;border:2px solid #E8136E;border-radius:12px;padding:10px 16px;display:flex;align-items:center;gap:14px">
        <div style="background:#E8136E;color:white;font-weight:900;font-size:1.1em;padding:6px 12px;border-radius:8px;flex-shrink:0">◎ 軸馬</div>
        <div>
          <div style="font-weight:900;font-size:1.7em;color:#E8136E;line-height:1">{e(tan1["name"])}</div>
          <div style="font-size:0.62em;color:#6B7280;margin-top:2px">想定 {e(str(tan1["odds"]))}倍　単勝スコア {tan1["tanPct"]*100:.1f}%</div>
        </div>
        <div style="flex:1;text-align:center;font-size:1.8em;color:#E8136E">⇄</div>
        <div style="text-align:right">
          <div style="font-size:0.65em;color:#6B7280">表流し 6点</div>
          <div style="font-size:0.65em;color:#6B7280">裏流し 6点</div>
          <div style="font-weight:900;font-size:1.1em;color:#E8136E">= 12点</div>
        </div>
      </div>
      <!-- 相手6頭 -->
      <div>
        <div style="font-size:0.62em;color:#E8136E;font-weight:700;margin-bottom:6px;letter-spacing:0.08em">相手 6頭</div>
        <div style="display:flex;gap:6px">
          {aite_chips_html}
        </div>
      </div>
      <!-- 説明 -->
      <div style="background:white;border-radius:10px;padding:8px 14px;border-left:3px solid #E8136E">
        <div style="font-size:0.65em;color:#374151;line-height:1.7">
          <strong style="color:#E8136E">◎スターアニス → 相手6頭</strong>　6点（スターアニスが1着）<br>
          <strong style="color:#E8136E">相手6頭 → ◎スターアニス</strong>　6点（スターアニスが2着でも的中）<br>
          <span style="color:#9CA3AF">マルチ買いで「どちらが1着でも」カバー。単勝より高倍率を狙う。</span>
        </div>
      </div>
    </div>
    {footer(20, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 21: 3連単 30点
# ══════════════════════════════════════════
def s21():
    tan1=by_tan[0]
    aite_names = ['ブラックチャリス','アランカール','ディアダイヤモンド','ナムラコスモス','ドリームコア','フェスティバルヒル']
    aite_chips_html = ''.join(
        '<div style="background:white;border:2px solid #6D28D966;border-radius:10px;padding:5px 8px;text-align:center;flex:1;min-width:0">'
        '<div style="font-weight:800;font-size:0.72em;color:#111;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + n + '</div>'
        '<div style="font-size:0.52em;color:#6D28D9;font-weight:600;margin-top:1px">' + str(score_map[n]["odds"]) + '倍</div>'
        '</div>'
        for n in aite_names
    )
    return f'''<div class="slide" id="s21">
  <div style="width:100%;height:100%;background:#FAF5FF;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#6D28D9"></div>
    <div style="background:linear-gradient(135deg,#E8136E,#6D28D9);padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.56em;letter-spacing:0.2em">STEP 3 / 3　本命固め打ち</div>
        <div style="color:white;font-weight:800;font-size:1.35em">💎 3連単　30点</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <div style="background:rgba(255,255,255,0.2);border-radius:8px;padding:3px 12px;text-align:center">
          <div style="color:rgba(255,210,230,0.8);font-size:0.52em">合計点</div>
          <div style="color:white;font-weight:900;font-size:1.2em">30点</div>
        </div>
        {corner_in_header()}
      </div>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;padding:10px 14px;gap:10px;overflow:hidden">
      <!-- 1着固定 -->
      <div style="background:white;border:2px solid #E8136E;border-radius:12px;padding:10px 16px;display:flex;align-items:center;gap:14px">
        <div style="background:linear-gradient(135deg,#E8136E,#6D28D9);color:white;font-weight:900;font-size:0.9em;padding:6px 10px;border-radius:8px;flex-shrink:0;text-align:center;line-height:1.3">🥇<br>1着<br>固定</div>
        <div>
          <div style="font-weight:900;font-size:1.8em;color:#E8136E;line-height:1">{e(tan1["name"])}</div>
          <div style="font-size:0.62em;color:#6B7280;margin-top:2px">想定 {e(str(tan1["odds"]))}倍　単勝スコア {tan1["tanPct"]*100:.1f}%　ZI132</div>
        </div>
        <div style="flex:1;text-align:right">
          <div style="font-size:0.6em;color:#9CA3AF">6頭 × 5頭</div>
          <div style="font-weight:900;font-size:1.3em;color:#6D28D9">= 30点</div>
        </div>
      </div>
      <!-- 相手6頭 -->
      <div>
        <div style="font-size:0.62em;color:#6D28D9;font-weight:700;margin-bottom:6px;letter-spacing:0.08em">2・3着　相手 6頭ボックス</div>
        <div style="display:flex;gap:6px">
          {aite_chips_html}
        </div>
      </div>
      <!-- 説明 -->
      <div style="background:white;border-radius:10px;padding:8px 14px;border-left:3px solid #6D28D9">
        <div style="font-size:0.65em;color:#374151;line-height:1.7">
          <strong style="color:#E8136E">◎スターアニス</strong>　が1着　×　<strong style="color:#6D28D9">相手6頭</strong>　から2着・3着<br>
          <span style="font-size:0.9em;color:#9CA3AF">1着固定 × P(6,2) = 6 × 5 = 30点。全マルチ(60点)の半分の資金で同等カバー。</span>
        </div>
      </div>
    </div>
    {footer(21, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# SLIDE 22: 最終予想宣言
# ══════════════════════════════════════════
def s22():
    tan1=by_tan[0]; fuku1=by_fuku[0]; ana1=by_ana[0]
    def decl_card(icon, role, name, odds_str, score_str, reason, accent):
        return f'''<div style="background:white;border:2px solid {accent}55;border-radius:12px;padding:11px 14px;position:relative;overflow:hidden">
  <div style="position:absolute;top:-10px;right:-10px;font-size:3em;opacity:0.06">{icon}</div>
  <div style="color:{accent};font-size:0.6em;font-weight:700;letter-spacing:0.12em;margin-bottom:3px">{e(role)}</div>
  <div style="font-weight:900;font-size:1.3em;color:#111;margin-bottom:2px">{e(name)}</div>
  <div style="color:#6B7280;font-size:0.63em;margin-bottom:7px">{e(odds_str)}　{e(score_str)}</div>
  <div style="font-size:0.62em;color:#374151;line-height:1.55;border-top:1px solid {accent}22;padding-top:5px">{e(reason)}</div>
</div>'''
    tan_name = e(tan1["name"])
    fuku_name = e(fuku1["name"])
    ana_name = e(ana1["name"])
    card1 = decl_card('🥇','◎ 本命　単勝1点 複勝1点',tan1["name"],f'{tan1["odds"]}倍',f'単勝{tan1["tanPct"]*100:.1f}% 単#1','ZI全馬最上位132 × G1前走1着 × 調教3S × 複勝率100%。三冠データが揃った唯一の馬。これ以上の根拠が何が必要？迷わず本命。','#E8136E')
    card2 = decl_card('🥈','○ 対抗　複勝 馬連・ワイド相手',fuku1["name"],f'{fuku1["odds"]}倍',f'複勝{fuku1["fukuPct"]*100:.1f}% 複#1','複勝スコア最上位・穴スコア2位の二冠。G2前走3着でデータ罠を回避済み。しがらきリフレッシュ後の末脚は爆発的。本命を脅かす最右翼。','#15803D')
    card3 = decl_card('⚡','☆ 穴馬　複勝少額',ana1["name"],f'{ana1["odds"]}倍',f'穴スコア{ana1["anaScore"]:.2f}pt 穴#1','父キタサンブラック複勝率66.7%という驚異データ。レースデータは消し根拠ありの「データの相克」。単勝は不要だが複勝で少額バックが合理的。','#6D28D9')
    return f'''<div class="slide" id="s22">
  <div style="width:100%;height:100%;background:#FFF0F7;position:relative;overflow:hidden;display:flex;flex-direction:column">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:#E8136E"></div>
    <div style="position:absolute;left:0;top:0;width:4px;height:100%;background:#E8136E"></div>
    <div style="background:#E8136E;padding:8px 14px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:rgba(255,210,230,0.8);font-size:0.6em;letter-spacing:0.5em">FINAL DECLARATION</div>
        <div style="font-weight:900;font-size:1.6em;color:white;letter-spacing:0.1em;line-height:1.1">最終　予想宣言</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <div style="font-size:0.65em;color:rgba(255,255,255,0.9)">ギーニョ重賞データ解析　2026桜花賞　—　これが答えだ</div>
        {corner_in_header()}
      </div>
    </div>
    <div style="flex:1;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;padding:8px 14px;overflow:hidden">
      {card1}
      {card2}
      {card3}
    </div>
    <div style="margin:0 14px 5px;background:white;border:1px solid rgba(232,19,110,0.3);border-radius:8px;padding:8px 14px;flex-shrink:0">
      <div style="display:flex;align-items:center;gap:10px">
        <span style="font-size:1.3em">📌</span>
        <div style="font-size:0.63em;color:#374151;line-height:1.65;flex:1">
          <strong style="color:#E8136E">買い目まとめ（45点）：</strong>
          単勝 <strong style="color:#111">{tan_name}</strong>1点　／
          複勝 <strong style="color:#111">{fuku_name}・{ana_name}</strong>2点　／
          馬単 <strong style="color:#111">{tan_name}軸×6頭流し</strong>12点　／　3連単30点
        </div>
      </div>
    </div>
    {footer(23, is_free=False)}
  </div>
</div>'''

# ══════════════════════════════════════════
# HTML出力
# ══════════════════════════════════════════
CSS = '''
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
body {
  background:#DFDFDF;
  font-family:"Hiragino Kaku Gothic ProN","ヒラギノ角ゴ ProN W3","Hiragino Sans","Yu Gothic","游ゴシック",sans-serif;
  overflow:hidden;
}
#viewer { width:100vw; height:100vh; display:flex; align-items:center; justify-content:center; }
#sc { position:relative; background:#fff; }
.slide { display:none; width:100%; height:100%; position:relative; overflow:hidden; }
.slide.active { display:block; }

/* ナビ */
#nav {
  position:fixed; bottom:16px; left:50%; transform:translateX(-50%);
  display:flex; gap:10px; align-items:center; z-index:200;
}
#nav button {
  background:rgba(232,19,110,0.9); color:white; border:none;
  padding:7px 20px; border-radius:20px; cursor:pointer; font-size:0.85em;
  font-family:inherit; font-weight:700; transition:background .2s;
}
#nav button:hover { background:#B40050; }
#counter { color:#555; font-size:0.82em; min-width:55px; text-align:center; }
#progress { position:fixed; top:0; left:0; height:3px; background:#E8136E; transition:width .35s; z-index:300; }

@keyframes pulse {
  0%,100%{opacity:1} 50%{opacity:0.4}
}

@media print {
  body { background:white; overflow:visible; }
  #nav, #progress { display:none !important; }
  #viewer { width:auto; height:auto; display:block; }
  #sc { width:277mm !important; height:155.8mm !important; font-size:16.5px !important; page-break-after:always; }
  .slide { display:block !important; }
}
'''

JS = '''
const slides = document.querySelectorAll('.slide');
const total  = slides.length;
let cur = 0;
const prog = document.getElementById('progress');
const cnt  = document.getElementById('counter');

function show(n) {
  slides[cur].classList.remove('active');
  cur = (n + total) % total;
  slides[cur].classList.add('active');
  prog.style.width = ((cur+1)/total*100)+'%';
  cnt.textContent  = (cur+1)+' / '+total;
}
document.getElementById('prev').onclick = () => show(cur-1);
document.getElementById('next').onclick = () => show(cur+1);
document.addEventListener('keydown', e => {
  if(e.key==='ArrowRight'||e.key===' ') show(cur+1);
  if(e.key==='ArrowLeft') show(cur-1);
});

// スライドスケーリング
function resize() {
  const sc = document.getElementById('sc');
  const W=window.innerWidth, H=window.innerHeight;
  const sw=960, sh=540;
  const scale = Math.min(W/sw, H/sh);
  sc.style.width  = sw+'px';
  sc.style.height = sh+'px';
  sc.style.transform = `scale(${scale})`;
  sc.style.transformOrigin = 'center center';
  sc.style.fontSize = (scale*16)+'px';
}
window.addEventListener('resize', resize);
resize();
cnt.textContent = '1 / '+total;
prog.style.width = (1/total*100)+'%';
'''

def build():
    slides_html = '\n'.join([
        s01(), s02(), s03(), s04(), s05(), s06(), s07(),
        s08(), s09(), s10(), s11(), s12(), s13(), s14(),
        s15(), s16(), s16b(), s17(), s18(), s19(), s20(), s21(), s22(),
    ])
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>桜花賞徹底解析 2026</title>
<style>{CSS}</style>
</head>
<body>
<div id="progress"></div>
<div id="viewer">
  <div id="sc">
{slides_html}
  </div>
</div>
<div id="nav">
  <button id="prev">◀ 前へ</button>
  <span id="counter"></span>
  <button id="next">次へ ▶</button>
</div>
<script>{JS}</script>
</body>
</html>'''
    out = os.path.join(BASE, '桜花賞徹底解析2026_v5.html')
    with open(out,'w',encoding='utf-8') as f:
        f.write(html)
    print(f'✅  {out}')
    print(f'    サイズ: {len(html)//1024} KB　スライド: 23枚')

if __name__ == '__main__':
    build()

