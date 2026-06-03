import json

DATE = "2026-06-01"
crawl = json.load(open('/tmp/suzaku_crawl.json'))
ccd_master = json.load(open('docs/data/jockey/jockey_ccd_master.json'))
order = {('j'+j['ccd'].lstrip('j')): i+1 for i,j in enumerate(ccd_master['jockeys'])}

jockeys = {}
for ccd, j in crawl.items():
    jockeys[ccd] = {
        "ccd": ccd, "name": j['name'], "rank": order.get(ccd, 999),
        "wins": j.get('wins',0), "winRate": j.get('winRate',0), "shRate": j.get('shRate',0),
        "g1": j.get('g1',0), "g2": j.get('g2',0), "g3": j.get('g3',0),
        "recent": j.get('recent',{"w1":0,"w2":0,"w3":0,"avg":0,"active":False}),
        "venues": j.get('venues',{}), "popularity": j.get('popularity',{}),
        "classes": j.get('classes',{}), "turfWR": j.get('turfWR',0), "dirtWR": j.get('dirtWR',0),
    }

active = [j for j in jockeys.values() if j['recent'].get('active') and j['shRate']>0]
def delta(j): return round(j['recent']['avg'] - j['shRate'], 1)
rising = sorted([j for j in active if delta(j)>0], key=lambda x:-delta(x))[:10]
falling = sorted([j for j in active if delta(j)<0], key=lambda x:delta(x))[:10]
def rf(j): return {"name":j['name'],"rank":j['rank'],"shRate":j['shRate'],"recentAvg":j['recent']['avg'],"delta":delta(j),"wins":j['wins']}

master = {"_meta":{"fetched":DATE,"source":"JRDB","count":len(jockeys)},
          "jockeys":jockeys,"rising":[rf(j) for j in rising],"falling":[rf(j) for j in falling]}
json.dump(master, open(f'docs/data/jockey/{DATE}_master149.json','w'), ensure_ascii=False, indent=1)

VENUES=['東京芝','東京ダ','京都芝','京都ダ','新潟芝','新潟ダ','中山芝','中山ダ','阪神芝','阪神ダ','中京芝','中京ダ','福島芝','福島ダ','小倉芝','小倉ダ']
def ti(a):
    return "🔥" if a>=50 else "↗︎" if a>=35 else "→" if a>=20 else "↘︎"
venues_out={}
for v in VENUES:
    rows=[]
    for j in jockeys.values():
        ven=j['venues'].get(v)
        if not ven or ven['n']<10 or not j['recent'].get('active'): continue
        rows.append({"name":j['name'],"shRate":ven['shRate'],"n":ven['n'],"recentAvg":j['recent']['avg'],
                     "trend":ti(j['recent']['avg']),"w1":j['recent']['w1'],"w2":j['recent']['w2'],"w3":j['recent']['w3']})
    rows.sort(key=lambda x:-x['shRate'])
    venues_out[v]=rows[:5]
venue_enriched={"_meta":{"fetched":DATE,"source":"JRDB","note":"149人完全DB・active filter適用済",
                "criteria":"場別複勝率(n>=10) ∧ 直近3週騎乗あり",
                "trendIcons":{"🔥":">=50%","↗︎":">=35%","→":">=20%","↘︎":"<20%"}},"venues":venues_out}
json.dump(venue_enriched, open(f'docs/data/jockey/{DATE}_venue_top5_enriched.json','w'), ensure_ascii=False, indent=1)

print("✅ 生成完了 master149:", len(jockeys), "人")
print("🌟急上昇:", " / ".join("{}({:+.1f})".format(j['name'],delta(j)) for j in rising[:3]))
print("🌧急落:", " / ".join("{}({:+.1f})".format(j['name'],delta(j)) for j in falling[:3]))
print("東京芝TOP3:", " / ".join("{}{}%".format(r['name'],r['shRate']) for r in venues_out['東京芝'][:3]))
