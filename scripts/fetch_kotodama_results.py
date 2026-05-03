#!/usr/bin/env python3
"""
fetch_kotodama_results.py — 言霊神宮 全レース結果取得＆回収率計算

docs/data/kotodama-test/{date}.json の各レース picks に対して:
  - netkeiba から着順・払戻取得
  - 各馬の人気・着順を picks に反映
  - 7券種BOX購入をシミュレート → 回収率算出

7券種:
  単勝 4点 (4頭) = 400円
  複勝 4点 (4頭) = 400円
  ワイドBOX 6点 (4C2) = 600円
  馬連BOX 6点 (4C2) = 600円
  馬単BOX 12点 (4P2) = 1200円
  3連複BOX 4点 (4C3) = 400円
  3連単BOX 24点 (4P3) = 2400円
  → 1Rあたり 60点 / 6,000円
"""
import urllib.request, re, json, sys, argparse, os
from pathlib import Path
from datetime import datetime
from itertools import combinations, permutations

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
ROOT = Path(__file__).resolve().parent.parent
KT_DIR = ROOT / 'docs/data/kotodama-test'

# 競馬ブックraceId → netkeiba raceId 変換マップ
# 2026-05-03 開催:
#   東京: 2回東京4日 → 05 02 04
#   京都: 3回京都4日 → 08 03 04
#   新潟: 1回新潟2日 → 04 01 02
KEIBABOOK_TO_NETKEIBA = {
    # keibabook prefix : netkeiba prefix (年除く10桁)
    '0204040': '0502040',  # 東京 5/3
    '0300040': '0803040',  # 京都 5/3
    '0107020': '0401020',  # 新潟 5/3
}

PAYOUT_KEY_MAP = {
    'Tansho':     'tan',
    'Fukusho':    'fuku',
    'Wakuren':    'wakuren',
    'Umaren':     'umaren',
    'Wide':       'wide',
    'Umatan':     'umatan',
    'Fuku3':      'sanrenpuku',
    'Tan3':       'sanrentan',
}


def kb_to_nk(kb_id):
    """競馬ブックraceId → netkeiba raceId"""
    if len(kb_id) != 12:
        return None
    year = kb_id[:4]
    body = kb_id[4:11]   # 7桁
    rr   = kb_id[11:]    # 1桁? いや12桁なので分割が違う
    # 12桁: YYYY(4) + body(6) + RR(2)
    body = kb_id[4:10]
    rr   = kb_id[10:12]
    nk_body = KEIBABOOK_TO_NETKEIBA.get(body[:7]) or KEIBABOOK_TO_NETKEIBA.get(body)
    # body は 6桁(例:020404)、マップキーは 7桁(0204040) なので合わない
    # 再設計: kb形式は {年4}{場2}{回2}{日2}{R2} だが場2の扱いが特殊
    # kb 例: 202602040401 → 2026 02 04 04 01
    #         year=2026, kb_venue=02, kai=04, day=04, R=01
    return None  # 下の new 実装を使う


# 場別マッピング（kb_venue → netkeiba (jra_venue, kai, day) 2026-05-03 当日固定）
KB_VENUE_TO_NK = {
    '02': ('05', '02', '04'),  # 東京 → JRA場05 / 2回4日
    '03': ('08', '03', '04'),  # 京都 → JRA場08 / 3回4日
    '01': ('04', '01', '02'),  # 新潟 → JRA場04 / 1回2日
}


def kb_to_netkeiba(kb_id):
    """例: 202602040401 → 202605020401。既にnetkeiba形式なら(JRA場コード04-10)そのまま返す"""
    if len(kb_id) != 12:
        return None
    year = kb_id[:4]
    kb_v = kb_id[4:6]
    rr   = kb_id[10:12]
    # 既にnetkeiba形式（JRA場コード04新潟/05東京/08京都）かつ既知マップ外
    if kb_v in ('04','05','08') and kb_v not in KB_VENUE_TO_NK:
        return kb_id
    # 場コード重複ケース: kb=02東京 / nk=05東京 のとき、kb_idの3-4桁目で見分けつかない
    # → 2026-05-03は11Rだけ既にnetkeiba形式と判明 → rr=11 かつ場コードがJRA形式なら通す
    if rr == '11' and kb_v in ('05','08','04'):
        return kb_id
    m = KB_VENUE_TO_NK.get(kb_v)
    if not m:
        return None
    nk_v, kai, day = m
    return f'{year}{nk_v}{kai}{day}{rr}'


def fetch_html(race_id):
    url = f'https://race.netkeiba.com/race/result.html?race_id={race_id}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('euc-jp', errors='replace')


def _txt(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


def parse_horses(html):
    horses = []
    rows = re.findall(r'<tr\s+class="[^"]*HorseList[^"]*"[^>]*>(.*?)</tr>', html, re.S)
    for row in rows:
        rank   = re.search(r'class="Rank">([^<]+)</div>', row)
        num    = re.search(r'class="Num Txt_C">\s*<div>(\d+)</div>', row)
        name   = re.search(r'<span class="HorseNameSpan">\s*([^<\n]+?)\s*</span>', row)
        ninki  = re.search(r'class="OddsPeople">\s*([^<]+?)\s*</span>', row)
        odds_td = re.search(r'<td class="Odds Txt_R"[^>]*>(.*?)</td>', row, re.S)
        odds = re.search(r'<span[^>]*>\s*([\d\.]+)\s*</span>', odds_td.group(1)) if odds_td else None
        horses.append({
            'rank':   (rank.group(1).strip()   if rank   else ''),
            'num':    (num.group(1)             if num    else ''),
            'name':   (name.group(1).strip()    if name   else ''),
            'finalNinki': (ninki.group(1).strip() if ninki else ''),
            'finalOdds':  (odds.group(1).strip()  if odds  else ''),
        })
    return horses


def parse_payouts(html):
    out = {}
    for tbl in re.findall(r'<table[^>]*class="Payout_Detail_Table"[^>]*>(.*?)</table>', html, re.S):
        for cls, body in re.findall(r'<tr class="(\w+)"[^>]*>(.*?)</tr>', tbl, re.S):
            key = PAYOUT_KEY_MAP.get(cls)
            if not key:
                continue
            result_m = re.search(r'<td class="Result"[^>]*>(.*?)</td>', body, re.S)
            payout_m = re.search(r'<td class="Payout"[^>]*>(.*?)</td>', body, re.S)
            if not (result_m and payout_m):
                continue
            r_html = result_m.group(1)
            ul_blocks = re.findall(r'<ul[^>]*>(.*?)</ul>', r_html, re.S)
            r_items = ul_blocks if ul_blocks else [r_html]
            amts = [int(a.replace(',','')) for a in re.findall(r'([\d,]+)\s*円', _txt(payout_m.group(1)))]
            picks = []
            # 複勝/ワイドは「1ulに1組合せ」形式が正しい。ulがない場合は<br>で区切られた複数組
            if key in ('fuku',) and not ul_blocks:
                # 複勝は br で1着/2着/3着が並ぶ → spanごとに1組
                nums_all = re.findall(r'<span[^>]*>(\d+)</span>', r_html)
                for idx, n in enumerate(nums_all):
                    picks.append({'combo': [n], 'amount': amts[idx] if idx < len(amts) else None})
            else:
                for idx, r in enumerate(r_items):
                    nums = re.findall(r'<span[^>]*>(\d+)</span>', r)
                    if not nums:
                        continue
                    picks.append({
                        'combo':  nums,
                        'amount': amts[idx] if idx < len(amts) else None,
                    })
            out[key] = picks
    return out


def calc_betting(picks, payouts):
    """4頭picksから7券種BOX購入結果計算"""
    nums = [str(int(p['num'])) for p in picks]  # 馬番文字列
    n = len(nums)
    invest = {'tan': n*100, 'fuku': n*100,
              'wide': len(list(combinations(nums,2)))*100,
              'umaren': len(list(combinations(nums,2)))*100,
              'umatan': len(list(permutations(nums,2)))*100,
              'sanrenpuku': len(list(combinations(nums,3)))*100 if n>=3 else 0,
              'sanrentan':  len(list(permutations(nums,3)))*100 if n>=3 else 0}

    # 払戻ヒット計算
    payout = {k: 0 for k in invest}

    def hit_combo(p_combo, my_set, ordered=False):
        if ordered:
            return list(p_combo) == list(my_set)
        return sorted(p_combo) == sorted(my_set)

    # 単勝（comboは1頭）
    for p in payouts.get('tan', []):
        for h in p['combo']:
            if h in nums:
                payout['tan'] += p['amount'] or 0
    # 複勝（comboに複数頭=1〜3着が入る形式 / amountは各頭分の払戻）
    for p in payouts.get('fuku', []):
        for h in p['combo']:
            if h in nums:
                payout['fuku'] += p['amount'] or 0
    # ワイド (BOX)
    for p in payouts.get('wide', []):
        for c2 in combinations(nums, 2):
            if hit_combo(p['combo'], list(c2), ordered=False):
                payout['wide'] += p['amount'] or 0
                break
    # 馬連
    for p in payouts.get('umaren', []):
        for c2 in combinations(nums, 2):
            if hit_combo(p['combo'], list(c2), ordered=False):
                payout['umaren'] += p['amount'] or 0
                break
    # 馬単
    for p in payouts.get('umatan', []):
        for c2 in permutations(nums, 2):
            if hit_combo(p['combo'], list(c2), ordered=True):
                payout['umatan'] += p['amount'] or 0
                break
    # 3連複
    if n >= 3:
        for p in payouts.get('sanrenpuku', []):
            for c3 in combinations(nums, 3):
                if hit_combo(p['combo'], list(c3), ordered=False):
                    payout['sanrenpuku'] += p['amount'] or 0
                    break
        # 3連単
        for p in payouts.get('sanrentan', []):
            for c3 in permutations(nums, 3):
                if hit_combo(p['combo'], list(c3), ordered=True):
                    payout['sanrentan'] += p['amount'] or 0
                    break

    invest_total = sum(invest.values())
    payout_total = sum(payout.values())
    return {
        'invest': invest, 'payout': payout,
        'investTotal': invest_total, 'payoutTotal': payout_total,
        'recovery': round(payout_total / invest_total * 100, 1) if invest_total else 0,
    }


def update_race(race, force=False):
    kb_id = race.get('raceId')
    nk_id = kb_to_netkeiba(kb_id)
    if not nk_id:
        print(f'  ⚠ raceId変換失敗: {kb_id}')
        return False
    if race.get('result') and not force:
        # 既取得済みでもbetting再計算したい → 払戻あれば再計算のみ
        pass
    try:
        html = fetch_html(nk_id)
    except Exception as e:
        print(f'  ✗ fetch失敗 {kb_id}→{nk_id}: {e}')
        return False
    horses = parse_horses(html)
    payouts = parse_payouts(html)
    if not horses:
        print(f'  ⚠ 着順データなし {kb_id}（未確定の可能性）')
        return False

    # picksに人気・着順を付与
    name_to_h = {h['name']: h for h in horses}
    num_to_h  = {h['num']: h for h in horses}
    for p in race.get('picks', []):
        h = name_to_h.get(p['name']) or num_to_h.get(str(int(p['num']))) if p.get('num') else None
        if h:
            p['finalRank']  = h['rank']
            p['finalNinki'] = h['finalNinki']
            p['finalOdds']  = h['finalOdds']

    bet = calc_betting(race['picks'], payouts)
    race['result'] = {
        'fetched': datetime.now().isoformat(timespec='seconds'),
        'netkeibaRaceId': nk_id,
        'horses': horses[:5],   # 上位5着のみ保存
        'payouts': payouts,
        'betting': bet,
        'summary': f"1着 {horses[0]['num']}番 {horses[0]['name']} ({horses[0]['finalNinki']}人気) | 回収率 {bet['recovery']}%",
    }
    win = horses[0]
    print(f"  ✓ {race['venue']}{race['raceNum']}  1着={win['num']:>2}番 {win['name']:<10} ({win['finalNinki']}人気)  投資¥{bet['investTotal']:,} 払戻¥{bet['payoutTotal']:,}  回収率{bet['recovery']}%")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('date', help='例: 2026-05-03')
    ap.add_argument('--venue', help='場で絞る (例: 東京)')
    ap.add_argument('--race', type=int, help='Rで絞る (例: 11)')
    args = ap.parse_args()

    path = KT_DIR / f'{args.date}.json'
    d = json.load(open(path))
    races = d['races']
    if args.venue:
        races = [r for r in races if r['venue'] == args.venue]
    if args.race:
        races = [r for r in races if str(r['raceNum']).rstrip('R') == str(args.race)]

    ok = 0
    for r in races:
        if update_race(r):
            ok += 1

    # 全体集計
    target = [r for r in d['races'] if r.get('result')]
    if target:
        tot_inv = sum(r['result']['betting']['investTotal'] for r in target)
        tot_pay = sum(r['result']['betting']['payoutTotal'] for r in target)
        # 券種別集計
        kinds = ['tan','fuku','wide','umaren','umatan','sanrenpuku','sanrentan']
        per = {k: {'inv':0,'pay':0} for k in kinds}
        for r in target:
            b = r['result']['betting']
            for k in kinds:
                per[k]['inv'] += b['invest'].get(k,0)
                per[k]['pay'] += b['payout'].get(k,0)
        d['summary'] = {
            'updated': datetime.now().isoformat(timespec='seconds'),
            'racesWithResult': len(target),
            'totalInvest': tot_inv,
            'totalPayout': tot_pay,
            'totalRecovery': round(tot_pay/tot_inv*100,1) if tot_inv else 0,
            'byKind': {k: {'invest': per[k]['inv'], 'payout': per[k]['pay'],
                            'recovery': round(per[k]['pay']/per[k]['inv']*100,1) if per[k]['inv'] else 0}
                        for k in kinds},
        }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'\n完了: {ok}/{len(races)} 取得')
    if target:
        s = d['summary']
        print(f"集計: {s['racesWithResult']}R / 投資¥{s['totalInvest']:,} 払戻¥{s['totalPayout']:,} 回収率{s['totalRecovery']}%")
        print('券種別:')
        for k, v in s['byKind'].items():
            print(f"  {k:<12} 投資¥{v['invest']:>7,} 払戻¥{v['payout']:>7,} 回収率{v['recovery']:>6.1f}%")


if __name__ == '__main__':
    main()
