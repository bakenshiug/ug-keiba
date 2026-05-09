# 🏇 騎手フルデータ・スクレイパー仕様書

**2026-05-09 MVP（3騎手テスト）成功 → 150騎手本番設計**

## 概要
JRDB joca.php?ccd= から騎手データを構造化JSON取得するスクレイパー。
Chrome MCP経由で Basic 認証越え。

## 必要環境
- Chrome MCP 接続
- JRDB会員ログイン済（ブラウザ側で）

## データソース
- 騎手マスター: `docs/data/jockey/jockey_ccd_master.json`（149人）
- 個別データURL: `http://www.jrdb.com/member/jrdv/joc/joca.php?ccd={ccd}`

## SPA タブ構造
```
#hbt_ky        今週出走予定
#hbt_tnsei     厩舎別
#hbt_seininki  人気別
#hbt_seclass   クラス別
#hbt_seijo     競馬場別
#hbt_su        開催別
#hbt_winf      WIN5
#hbt_se        レース成績
```
**重要**: クリックでデータが**APPEND**される（タブ切替えではない）。
→ 全タブクリック後に1回 DOM 取得すれば全データ取れる。

## 1騎手取得フロー（実証済み）

### Step 1: navigate
```
url: http://www.jrdb.com/member/jrdv/joc/joca.php?ccd={ccd}
```

### Step 2: クリック＋待機
```javascript
(async()=>{
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  ['#hbt_seijo','#hbt_seininki','#hbt_seclass'].forEach(s=>document.querySelector(s)?.click());
  await sleep(1500);  // データ展開待ち
  return 'ok';
})()
```

### Step 3: 構造化抽出
```javascript
(()=>{
  const t = document.body.innerText;
  const lines = t.split('\n').map(l=>l.trim());
  const findIdx = k => lines.findIndex(l=>l.includes(k));
  const parseRow = str => str.split(/[\s\t]+/).filter(Boolean);
  
  // 本年度成績（1着〜複率、G1G2G3、芝/ダ別勝率）
  const honnenIdx = findIdx('本年度成績');
  const honnen = parseRow(lines[honnenIdx+2]);
  
  // 昨年度成績
  const sakunenIdx = findIdx('昨年度成績');
  const sakunen = parseRow(lines[sakunenIdx+2]);
  
  // 人気別（1〜5人気＋10人気以降）
  const ninkiIdx = findIdx('人気別成績');
  const ninki = {};
  for (let i = ninkiIdx+2; i < ninkiIdx+10; i++) {
    const c = parseRow(lines[i]);
    if (c[0]?.includes('人気')) {
      ninki[c[0]] = {
        win: +c[1], pl: +c[2], sh: +c[3],
        winRate: +c[7], plRate: +c[8], shRate: +c[9]
      };
    }
  }
  
  // クラス別（複勝率のみ）
  const clsIdx = findIdx('クラス別成績');
  const clsRow = parseRow(lines[clsIdx+2]);
  const cls = {};
  const clsKeys = ['新馬','未勝利','1勝','2勝','3勝','OP'];
  let ci = 0;
  for (const v of clsRow) {
    if (v.includes('%')) cls[clsKeys[ci++]] = parseFloat(v.split('/')[1]);
  }
  
  // 近3週
  const recIdx = findIdx('近３週成績');
  const rec = parseRow(lines[recIdx+2]);
  const recScores = [];
  rec.forEach(v => {
    const m = v.match(/([\d.]+)%/);
    if (m) recScores.push(parseFloat(m[1]));
  });
  
  return JSON.stringify({
    honnen: {
      wins: +honnen[0], winRate: +honnen[6], plRate: +honnen[7], shRate: +honnen[8],
      g1: +honnen[9], g2: +honnen[10], g3: +honnen[11],
      turfWinRate: +honnen[16], dirtWinRate: +honnen[23]
    },
    sakunen: {wins: +sakunen[0], winRate: +sakunen[6], g1: +sakunen[9], g2: +sakunen[10], g3: +sakunen[11]},
    recent: {w3: recScores[0], w2: recScores[1], w1: recScores[2]},
    popularity: ninki,
    classes: cls
  });
})()
```

## 150騎手本番運用フロー

### 実行
```
for each jockey in jockey_ccd_master.json (149人):
  1. navigate(joca.php?ccd={ccd})
  2. click 3 tabs + wait
  3. extract JSON
  4. accumulate to results object
  5. sleep 2 seconds (rate limit)

合計: 149 × 約8秒 = 約20分
```

### 出力
- `docs/data/jockey/{date}_full.json` - 全騎手構造化データ
- `docs/data/jockey/{date}_full.csv` - CSV版（人間レビュー用）

## 取得指標サマリ（CSVカラム）

| カラム | 意味 |
|---|---|
| ccd | 騎手ID |
| name | 騎手名 |
| rank | リーディング順位 |
| honnen_wins | 本年勝利数 |
| honnen_winRate | 本年勝率 |
| honnen_g1/g2/g3 | 本年G1/G2/G3勝ち |
| sakunen_wins | 昨年勝利数 |
| sakunen_g1/g2/g3 | 昨年G1/G2/G3勝ち |
| turf_winRate | 芝勝率 |
| dirt_winRate | ダ勝率 |
| recent_w1/w2/w3 | 1〜3週前複勝率 |
| pop1_winRate | 1人気勝率 ← **戸崎vsルメール識別** |
| pop1_shRate | 1人気複勝率 |
| pop10_wins | 10人気以降勝ち数 ← **津村穴勝ち識別** |
| pop10_winRate | 10人気以降勝率 |
| class_OP | OP複勝率 ← **重賞・特別の真の力** |

## 3騎手テスト結果サマリ（2026-05-09）

| 騎手 | 1人気勝率 | 10人気以降勝ち | OP複勝率 | 本年G1 |
|---|---|---|---|---|
| ルメール | **39.6%** | 0勝 | 47.8% | 2 |
| 川田 | 34.8% | 0勝 | 46.2% | **0** ← イップス |
| 津村 | 34.7% | **5勝** | 19.0% | 0 |

→ 津村1人気勝率34.7%は意外に高い（ルメールに5%差）  
→ 10人気以降勝ち5回は津村の真骨頂（穴乗り本物の決定的証拠）  
→ 川田の本年G1ゼロが川田型イップスの数字証明
