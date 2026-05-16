#!/usr/bin/env python3
"""
gen_archive_v2.py — 言霊神宮 土曜アーカイブページ生成（新買い方ルール対応）

新買い方:
  ⛩️ 単勝◎1点 + 馬単マルチ◎軸6点
  🌕 単勝激1点 + 馬単マルチ激軸6点

Usage:
    python3 scripts/gen_archive_v2.py 2026-05-16 --label "新潟大賞典週・土曜"
"""
import argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
TEMPLATE = DOCS / 'kotodama.html'


NEW_RENDER_SUMMARY_AXIS = r"""
// ─── v2 サマリー（新買い方: 単勝◎+馬単◎軸 / 単勝激+馬単激軸）───
const V2_KIND_LABEL = {
  honmei_tan:    '⛩️ 単勝◎',
  honmei_umatan: '⛩️ 馬単◎軸マルチ',
  ana_tan:       '🌕 単勝激',
  ana_umatan:    '🌕 馬単激軸マルチ',
};

function venueBoardV2(name, s){
  return `
    <div class="vb">
      <div class="vb-h mincho">${name}</div>
      <div class="vb-total ${s.totalRecovery>=100?'win':''}"><span style="font-size:12px;font-weight:400;letter-spacing:.1em;margin-right:6px">回収率</span>${s.totalRecovery}%</div>
      <div class="vb-meta">${s.racesHit}/${s.racesWithResult}R的中 (${s.raceHitRate}%) ／ 投資¥${s.totalInvest.toLocaleString()} 払戻¥${s.totalPayout.toLocaleString()}</div>
      <table class="vb-table">
        <tr><th>券種</th><th style="text-align:right">的中率</th><th style="text-align:right">回収率</th></tr>
        ${Object.entries(s.byKind).map(([k,v])=>`
          <tr>
            <td>${V2_KIND_LABEL[k]||k}</td>
            <td class="v-hit ${v.hitRate>=50?'win':''}">${v.hit}/${v.races} (${v.hitRate}%)</td>
            <td class="v-rec ${v.recovery>=100?'win':''}">${v.recovery}%</td>
          </tr>`).join('')}
      </table>
    </div>`;
}

function renderSummaryAxis(){
  const el = document.getElementById('summary-board-axis');
  if (!el) return;
  if (!SUMMARY_V2) { el.innerHTML = ''; return; }
  const s = SUMMARY_V2;
  const venueOrder = ['東京','京都','新潟','中山','阪神','中京','福島','小倉','札幌','函館'];
  const venues = Object.entries(s.byVenue || {}).sort((a,b)=>{
    const ai=venueOrder.indexOf(a[0]), bi=venueOrder.indexOf(b[0]);
    return (ai<0?99:ai)-(bi<0?99:bi);
  });

  el.innerHTML = `
    <details class="summary-board neon sb-fold">
      <summary class="sb-fold-summary">
        <div class="sb-title mincho">⛩ 言霊神宮 土曜全36R 集計　単勝◎1点購入 & ◎馬単軸マルチ（6点）購入 / 激走穴同様</div>
        <div class="sb-total ${s.totalRecovery>=100?'win':''}">
          総合回収率 ${s.totalRecovery}%
        </div>
        <div class="sb-fold-hint mincho">▼ クリックで詳細を展開</div>
      </summary>
      <div class="sb-total-detail ${s.totalRecovery>=100?'win':''}">
        <small>${s.racesHit}/${s.racesWithResult}R的中 (${s.raceHitRate}%) ／ 投資¥${s.totalInvest.toLocaleString()} 払戻¥${s.totalPayout.toLocaleString()}</small>
      </div>
      <div class="sb-meta">⛩️ 単勝◎¥100 + 馬単マルチ◎軸¥600 ／ 🌕 単勝激¥100 + 馬単マルチ激軸¥600 （1Rあたり14点 ¥1,400）</div>
      <div class="sb-kinds">
        ${Object.entries(s.byKind).map(([k,v])=>`
          <div class="sb-kind">
            <div class="k-name">${V2_KIND_LABEL[k]||k}</div>
            <div class="k-rec ${v.recovery>=100?'win':''}">${v.recovery}%</div>
            <div class="k-hit ${v.hitRate>=50?'win':''}">的中${v.hit}/${v.races} (${v.hitRate}%)</div>
            <div class="k-amt">¥${v.payout.toLocaleString()} / ¥${v.invest.toLocaleString()}</div>
          </div>
        `).join('')}
      </div>
      <details class="summary-d" open>
        <summary>場別 集計（東京 / 京都 / 新潟）</summary>
        <div class="venue-boards">
          ${venues.map(([v,sv])=>venueBoardV2(v,sv)).join('')}
        </div>
      </details>
      <div class="sb-learn">🔬 神宮の本命軸 & 激走穴軸の回収率 ／ 1Rあたり¥1,400の投資効率型</div>
    </details>`;
}
"""


def generate(date_str: str, label: str = None):
    out_filename = f'archive-{date_str}.html'
    out_path = DOCS / out_filename
    label_text = f"（{label}）" if label else ""

    html = TEMPLATE.read_text(encoding='utf-8')

    # 1) FILES → 該当日のJSONのみ
    target_json = f"data/kotodama-test/{date_str}.json"
    html = re.sub(
        r"const FILES\s*=\s*\[[^\]]*\];",
        f"const FILES = ['{target_json}'];",
        html, count=1,
    )

    # 2) paidDay 全公開
    html = html.replace(
        "const paidDay = d.paidDay === true;",
        "const paidDay = false; /* アーカイブ：全公開 */",
    )

    # 3) summaryV2 変数追加（load関数内）
    html = html.replace(
        "let SUMMARY = null;\nlet CURRENT_TAB = '';",
        "let SUMMARY = null;\nlet SUMMARY_V2 = null;\nlet CURRENT_TAB = '';",
    )
    html = html.replace(
        "if (d.summary) SUMMARY = d.summary;",
        "if (d.summary) SUMMARY = d.summary;\n      if (d.summaryV2) SUMMARY_V2 = d.summaryV2;",
    )

    # 4) renderSummaryAxis を新版に置き換え
    # calcAxis / aggregateAxis / venueBoardAxis / renderSummaryAxis をまとめて置換
    start_marker = "// ◎軸流し戦略の計算"
    end_marker   = "}\n\nfunction venueBoard("
    start_idx = html.find(start_marker)
    end_idx   = html.find(end_marker, start_idx)
    if start_idx >= 0 and end_idx >= 0:
        html = html[:start_idx] + NEW_RENDER_SUMMARY_AXIS + "\n\nfunction venueBoard(" + html[end_idx + len(end_marker):]
    else:
        print("⚠ renderSummaryAxis の置換に失敗しました。手動確認が必要です。")

    # 5) renderSummary → 土曜のみ集計に変更（summaryV2から）
    # renderSummary は不要なので空関数に
    html = re.sub(
        r'function renderSummary\(\)\{.*?\n\}(\n\n)',
        'function renderSummary(){\n  const el = document.getElementById(\'summary-board\');\n  if (el) el.innerHTML = \'\';\n}\n\n',
        html, count=1, flags=re.DOTALL,
    )

    # 6) <title> 変更
    html = re.sub(
        r'<title>.*?</title>',
        f'<title>言霊神宮アーカイブ {date_str}{label_text} ｜ UG競馬神宮</title>',
        html, count=1,
    )

    # 7) アーカイブバナー追加（<body>直後）
    banner = f'''<div style="background:linear-gradient(135deg,#f5f2eb,#fbf7ee);border-bottom:2px solid #8a7a3a;
            padding:14px 20px;text-align:center;font-family:'Shippori Mincho',serif;letter-spacing:.05em">
  📜 <b style="color:#7A1E1E">言霊神宮アーカイブ</b>
  ｜ {date_str}{label_text}
  ｜ <a href="kotodama.html" style="color:#a44a3f;font-weight:700;text-decoration:underline">最新週へ戻る ▶</a>
  ｜ <a href="kotodama-archive.html" style="color:#a44a3f;font-weight:700;text-decoration:underline">アーカイブ一覧 📚</a>
</div>'''
    html = html.replace('<body>', f'<body>\n{banner}')

    # 8) header のサブタイトルを更新
    html = re.sub(
        r'(<div class="h-sub mincho">)[^<]*(</div>)',
        r'\1⛩ ギーニョ・青龍・クロード（神主）\2',
        html, count=1,
    )

    out_path.write_text(html, encoding='utf-8')
    print(f'✅ 生成完了: {out_path}')
    print(f'   → https://bakenshiug.github.io/ug-keiba/{out_filename}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('date',    help='例: 2026-05-16')
    ap.add_argument('--label', help='例: 新潟大賞典週・土曜')
    args = ap.parse_args()
    generate(args.date, args.label)
