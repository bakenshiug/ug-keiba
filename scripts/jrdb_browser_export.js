/**
 * 🐢 JRDB ブラウザ書き出しスクリプト
 *
 * JRDBのページを開いた状態でブラウザコンソールに貼り付けると
 * racekey_json51.php API から全レースデータを取得して
 * window.__rosterResult に格納する。
 *
 * 【API 仕様 (2026-05-15 解析)】
 *   /member/racekey_json51.php?racedate=YYYYMMDD&racekey=XXXXXXXX&mode=&cs=047&ts=...&username=...
 *   レスポンス: { ra_al: {...レース情報}, ky_al: [{...馬データ}, ...] }
 *
 * 使い方 (全36R一括):
 *   1. JRDBの任意ページを開く（ログイン済み）
 *   2. F12 → Console タブ
 *   3. USERNAME と DATE を書き換えて貼り付け → Enter
 *   4. 完了後 copy(JSON.stringify(window.__rosterResult)) でクリップボードへ
 */

// ==========================================
// 設定 — ここだけ書き換える
// ==========================================
const USERNAME = '20036286';     // JRDBメンバーID（URLのusername=の数値）
const DATE     = '20260516';     // 対象日 YYYYMMDD

// 週次で更新するレースコード一覧
// n_index.html の n_live_{DATE}_{CODE}.html から自動取得
const RACE_CODES_BY_DATE = {
  '20260516': [
    // 東京
    '05262701','05262702','05262703','05262704','05262705','05262706',
    '05262707','05262708','05262709','05262710','05262711','05262712',
    // 京都
    '08263701','08263702','08263703','08263704','08263705','08263706',
    '08263707','08263708','08263709','08263710','08263711','08263712',
    // 新潟
    '04261501','04261502','04261503','04261504','04261505','04261506',
    '04261507','04261508','04261509','04261510','04261511','04261512',
  ],
  '20260517': [
    // TODO: 翌日分は n_index.html から確認して追記
  ],
};

const VENUE_MAP = {
  '01':'札幌','02':'函館','03':'福島','04':'新潟',
  '05':'東京','06':'中山','07':'中京','08':'京都',
  '09':'阪神','10':'小倉'
};

// ==========================================
// 馬データパース (ky_al エントリ → 必要フィールド)
// ==========================================
function parseHorse(h) {
  const gaikyu     = (!h.houbokusaki || h.houbokusaki === 'null') ? '' : h.houbokusaki;
  const baguname1  = (h.baguname1  || '').trim();
  const zenBagu1   = (h.zenbaguname1 || '').trim();
  const briNow     = (h.blinkercd && h.blinkercd !== 'null') || baguname1.includes('ブ');
  const briPrev    = zenBagu1.includes('ブ');
  const kisyuhenko = h.kisyuhenko;
  return {
    num:        String(h.umaban || '').replace(/^0+/, '') || h.umaban,
    name:       (h.bamei9m || '').trim(),
    jockey:     h.kisyu3m   || '',
    daijo:      !!(kisyuhenko && kisyuhenko !== 'null' && kisyuhenko !== '0'),
    trainer:    h.chokyosi3m || '',
    belong:     h.shozoku    || '',
    gaikyu:     gaikyu,
    gaikyuRank: h.houbokusaki_rank,
    nyukyu:     h.nyukyudate,
    banushi:    h.banusiname || '',
    bri:        briNow,
    hatsuBri:   briNow && !briPrev,
  };
}

// ==========================================
// 1レース取得
// ==========================================
async function fetchOneRace(code8, date, username) {
  const ts  = Date.now();
  const url = `/member/racekey_json51.php?racedate=${date}&racekey=${code8}&mode=&cs=047&ts=${ts}&username=${username}`;
  const resp = await fetch(url, { credentials: 'include' });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  return data;
}

// ==========================================
// 全レース一括取得
// ==========================================
async function fetchAllRaces() {
  const codes = RACE_CODES_BY_DATE[DATE];
  if (!codes || codes.length === 0) {
    console.error(`❌ ${DATE} のレースコードが未定義。RACE_CODES_BY_DATE を更新してください。`);
    return;
  }

  window.__rosterResult = [];
  console.log(`📋 ${DATE} — ${codes.length}レース取得開始...`);

  for (let i = 0; i < codes.length; i++) {
    const code8 = codes[i];
    const venue = VENUE_MAP[code8.slice(0, 2)] || '?';
    const raceNum = parseInt(code8.slice(6, 8), 10);

    try {
      const data   = await fetchOneRace(code8, DATE, USERNAME);
      const ra_al  = data.ra_al  || {};
      const ky_al  = data.ky_al  || [];
      const horses = ky_al.filter(h => h.torikesi !== '1').map(parseHorse);

      window.__rosterResult.push({
        jrdbCode:  code8,
        venue:     venue,
        raceNum:   `${raceNum}R`,
        raceName:  ra_al.txt_racename || '',
        numHorses: horses.length,
        horses:    horses,
      });

      const hatsuri = horses.filter(h => h.hatsuBri).map(h => `${h.num}番${h.name}`);
      const tag = hatsuri.length ? ` 🐅初ブリ:${hatsuri.join(',')}` : '';
      console.log(`  [${String(i+1).padStart(2,'0')}/${codes.length}] ${venue}${raceNum}R ${ra_al.txt_racename||''} — ${horses.length}頭${tag}`);

    } catch(e) {
      console.error(`  [${i+1}] ${venue}${raceNum}R ERROR:`, e.message);
      window.__rosterResult.push({ jrdbCode: code8, venue, raceNum: `${raceNum}R`, horses: [], error: e.message });
    }

    await new Promise(r => setTimeout(r, 300));
  }

  const briList = window.__rosterResult.flatMap(r =>
    r.horses.filter(h => h.hatsuBri).map(h => `${r.venue}${r.raceNum} ${h.num}番${h.name}(${h.jockey}/${h.gaikyu||'在厩'})`)
  );
  if (briList.length) {
    console.log(`\n${'='.repeat(55)}`);
    console.log(`🐅 初ブリンカー馬 — ${briList.length}頭`);
    briList.forEach(s => console.log(' ', s));
  }

  console.log(`\n✅ 完了! ${window.__rosterResult.length}レース → window.__rosterResult`);
  console.log('📋 コピー: copy(JSON.stringify(window.__rosterResult, null, 2))');
  return window.__rosterResult;
}

// 実行
fetchAllRaces();
