#!/usr/bin/env python3
"""
神眼ファクター流し込みスクリプト
=====================================
弥永さんのYouTube解説(自動字幕)から各馬narrativeを抽出し、
Claude APIで S/A/B/C/D grade を付与して race-notes に書き込む。

Usage:
  # 1本の動画で単一レースを処理 (通常の使い方)
  python3 scripts/apply_shingan.py \\
      --video Yy38_knOHK0 \\
      --race 2026-04-25-tokyo-11r

  # 時間範囲を指定 (複数レース収録動画から特定区間だけ)
  python3 scripts/apply_shingan.py \\
      --video Yy38_knOHK0 \\
      --race 2026-04-19-fukushima-11r \\
      --start 1980 --end 2300

  # Claude呼ばずに narrative 抽出だけ (検証用)
  python3 scripts/apply_shingan.py \\
      --video Yy38_knOHK0 \\
      --race 2026-04-19-nakayama-11r \\
      --end 1980 \\
      --extract-only

入力:
  scripts/yt_cache/{video_id}.json       (fetch_youtube_transcript.py出力)
  docs/data/race-notes/{race_slug}.json  (既存の race-notes, horses[]を参照)

出力:
  docs/data/race-notes/{race_slug}.json に各馬の h['shingan'] を追加
  {
    "grade":   "S/A/B/C/D",
    "keyword": "一言サマリ (12字以内)",
    "note":    "判定根拠 (Claude生成)",
    "source":  "shingan-v1",
    "videoId": "Yy38_knOHK0"
  }

環境:
  ANTHROPIC_API_KEY が必要
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')
CACHE = BASE / 'scripts/yt_cache'
NOTES = BASE / 'docs/data/race-notes'

# 自動字幕のカタカナ揺らぎへの対応
MATCH_WINDOW = 60  # 馬名ヒット前後 N 秒を narrative 窓として抽出
NGRAM_N      = 3   # 正規化後のカタカナ3-gramでマッチング

# カタカナ正規化: 濁音/半濁音→清音、小文字カナ→通常カナ、ッ/ー→除去
# 自動字幕での頻出揺らぎ (例: カヴァ→カバ、ファ→ハ、ォ/ッ 欠落、ー 欠落) を吸収
KANA_NORMALIZE = str.maketrans({
    'ガ':'カ','ギ':'キ','グ':'ク','ゲ':'ケ','ゴ':'コ',
    'ザ':'サ','ジ':'シ','ズ':'ス','ゼ':'セ','ゾ':'ソ',
    'ダ':'タ','ヂ':'チ','ヅ':'ツ','デ':'テ','ド':'ト',
    'バ':'ハ','ビ':'ヒ','ブ':'フ','ベ':'ヘ','ボ':'ホ',
    'パ':'ハ','ピ':'ヒ','プ':'フ','ペ':'ヘ','ポ':'ホ',
    'ヴ':'ウ',
    'ァ':'ア','ィ':'イ','ゥ':'ウ','ェ':'エ','ォ':'オ',
    'ャ':'ヤ','ュ':'ユ','ョ':'ヨ',
    'ッ':'','ー':'',
})


def normalize_kana(s):
    """カタカナを揺らぎ吸収形式に正規化"""
    if not s:
        return ''
    return s.translate(KANA_NORMALIZE)


def horse_ngrams(name, n=NGRAM_N):
    """馬名をカタカナ正規化し、n文字連続のn-gramを返す"""
    norm = normalize_kana(name)
    if len(norm) < n:
        return [norm] if norm else []
    return [norm[i:i+n] for i in range(len(norm) - n + 1)]


def extract_narrative_for_horse(snippets, horse_name, window=MATCH_WINDOW, n=NGRAM_N):
    """字幕全体から、horse_nameに言及された部分の前後windowを抽出。
    カタカナ正規化+N-gramマッチで字幕揺らぎを吸収。
    """
    ngrams = horse_ngrams(horse_name, n)
    if not ngrams:
        return '', 0

    hit_times = []
    for s in snippets:
        norm_text = normalize_kana(s['text'])
        for ng in ngrams:
            if ng in norm_text:
                hit_times.append(s['start'])
                break

    if not hit_times:
        return '', 0

    # ヒットした時刻の前後 window 秒を集める
    narrative_parts = []
    covered = set()  # start時刻で重複排除
    for ht in hit_times:
        lo, hi = ht - window, ht + window
        for s in snippets:
            if lo <= s['start'] <= hi and s['start'] not in covered:
                narrative_parts.append(s['text'])
                covered.add(s['start'])
    narrative = ''.join(narrative_parts)
    return narrative, len(hit_times)


def slice_transcript(snippets, start_s, end_s):
    if start_s is None and end_s is None:
        return snippets
    lo = start_s or 0
    hi = end_s or 10**9
    return [s for s in snippets if lo <= s['start'] <= hi]


# ── Claude API呼び出し ────────────────────────────────────
SHINGAN_SYSTEM_PROMPT = """あなたは競馬予想の分析アシスタント「ギーニョ」です。
YouTube解説者「弥永さん（相馬眼お化け）」の自動字幕から抽出した、ある特定の馬へのnarrativeを受け取ります。

自動字幕なのでカタカナ馬名は崩れます (例: 「カヴァレリッツォ」→「カバレリッツ」、「コガネノソラ」→「小金の空」)。
弥永さんは以下のような特徴的な語彙で評価を表現します:

【肯定signal】
  - 「本命」「本命だ」「本命でいい」「1番強い」→ S級 (確信)
  - 「黒三角」「本命候補」「素晴らしい」「ギア上がった」「とてつもなく強い」→ A級
  - 「オッケー」「いいな」「能力はある」「問題ない」→ B級

【否定signal】
  - 「ピンとこない」「引っかかる」「不安」「稽古がピンとこない」→ C級 (減点)
  - 「飛びつきたくない」「ケツから」「当たんねえ」「～の上」(自馬が下)
  - 「印は落とす」「要らない」「勝負にならない」「厳しい」→ D級 (消し)

【文脈解釈】
  - 相対比較: 「6:4で上」「~の上だと思う」→ 比較対象との相対評価
  - 騎手依存: 「クリスチャンがうまく乗った」「○○で助かった」→ 前走の割引signal
  - コース問題: 「コーナー4つ初めて」「距離不安」「枠悪」→ 減点
  - 言及薄 (1-2文): 判断材料不足で B-C 付近
  - 言及なし / まったく触れていない → null grade (データなし)

判定出力:
  - grade: S / A / B / C / D / null
  - keyword: 12字以内の一言サマリ (例: 「黒三角確定穴」「ピンと来ない減点」「本命対抗S」)
  - note: 30字以内の判定根拠 (例: 「コーナー4つ初体験+騎手頼み」)

重要:
  - narrativeが比較文脈("Xの上")に出るだけの場合、その馬自身への直接評価ではないので注意
  - 弥永が全体で自信なさげでも (「当たんない」等)、個別馬narrativeの質的評価で判定すること
  - 消し判定も本命判定と等しく重要。神眼の真価は"人気馬を正しく消す"ことにあり

必ず JSON (単一オブジェクト) で返答すること。コードブロックや説明文は不要。
"""


def build_user_prompt(horse_name, narrative, mention_count):
    return f"""馬名: {horse_name}
言及回数: {mention_count}
narrative (自動字幕, カタカナ揺らぎあり):
```
{narrative if narrative else '(言及なし)'}
```

この馬に対する弥永さんの評価を判定し、以下のJSON形式で返答:
{{"grade": "S|A|B|C|D|null", "keyword": "12字以内", "note": "30字以内"}}"""


def grade_horse_via_claude(client, horse_name, narrative, mention_count):
    if not narrative:
        return {'grade': None, 'keyword': '言及なし', 'note': 'narrative抽出できず'}

    user_prompt = build_user_prompt(horse_name, narrative, mention_count)
    try:
        resp = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=300,
            system=SHINGAN_SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_prompt}],
        )
        text = resp.content[0].text.strip()
        # コードブロックを削ぐ (念のため)
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.MULTILINE).strip()
        data = json.loads(text)
        # normalize grade
        g = data.get('grade')
        if g == 'null' or g == '':
            g = None
        elif g in ('S', 'A', 'B', 'C', 'D'):
            pass
        else:
            g = None
        return {
            'grade':   g,
            'keyword': (data.get('keyword') or '')[:20],
            'note':    (data.get('note') or '')[:80],
        }
    except Exception as e:
        print(f'  ⚠ Claude API呼び出し失敗 ({horse_name}): {e}', file=sys.stderr)
        return {'grade': None, 'keyword': 'API失敗', 'note': str(e)[:60]}


def apply_to_race(video_id, race_slug, start_s, end_s, extract_only, dry_run):
    yt_path = CACHE / f'{video_id}.json'
    rn_path = NOTES / f'{race_slug}.json'

    if not yt_path.exists():
        print(f'⚠ 字幕キャッシュなし: {yt_path.name} (fetch_youtube_transcript.py を先に実行)')
        return None
    if not rn_path.exists():
        print(f'⚠ race-notes なし: {rn_path.name}')
        return None

    yt = json.loads(yt_path.read_text(encoding='utf-8'))
    notes = json.loads(rn_path.read_text(encoding='utf-8'))
    horses = notes.get('horses', [])

    if not isinstance(horses, list):
        print(f'  ⏭ スキップ (旧SABCスキーマ): {rn_path.name}')
        return None

    # transcript スライス
    snippets = slice_transcript(yt['snippets'], start_s, end_s)
    total_duration = snippets[-1]['start'] - snippets[0]['start'] if snippets else 0
    print(f'  transcript区間: {snippets[0]["start"]:.0f}s - {snippets[-1]["start"]:.0f}s ({total_duration/60:.1f}min, {len(snippets)}snippets)')

    # 各馬のnarrative抽出
    narratives = []
    for h in horses:
        name = h.get('name') or ''
        narrative, count = extract_narrative_for_horse(snippets, name)
        narratives.append({
            'horse':    h,
            'name':     name,
            'narrative': narrative,
            'mentions': count,
        })

    # 抽出のみモード
    if extract_only:
        print(f'\n=== narrative抽出結果 (extract-only モード) ===\n')
        for nr in narratives:
            print(f'--- {nr["name"]} ({nr["mentions"]}言及 / {len(nr["narrative"])}文字) ---')
            print(nr['narrative'][:400] if nr['narrative'] else '(言及なし)')
            print()
        return narratives

    # Claude APIで grade 付与
    try:
        import anthropic
    except ImportError:
        print('pip3 install anthropic が必要', file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('ANTHROPIC_API_KEY が環境変数に設定されていません', file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    print(f'\n  Claude API で各馬を判定中 ({len(narratives)}頭)...')

    grade_hist = {'S': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0, None: 0}
    for nr in narratives:
        verdict = grade_horse_via_claude(client, nr['name'], nr['narrative'], nr['mentions'])
        nr['horse']['shingan'] = {
            'grade':    verdict['grade'],
            'keyword':  verdict['keyword'],
            'note':     verdict['note'],
            'mentions': nr['mentions'],
            'source':   'shingan-v1',
            'videoId':  video_id,
        }
        g = verdict['grade']
        grade_hist[g] = grade_hist.get(g, 0) + 1
        mark = {'S':'◎', 'A':'○', 'B':'△', 'C':'▲', 'D':'✕', None:'-'}.get(g, '?')
        print(f'    {mark} {nr["name"]:<12} {str(g):<4} 「{verdict["keyword"]}」  {verdict["note"][:40]}')

    # 神眼 apply メタ
    notes['shinganApplied'] = {
        'appliedAt': datetime.now().isoformat(timespec='seconds'),
        'videoId':   video_id,
        'timeWindow': [start_s, end_s],
        'gradeHistogram': {k if k else 'null': v for k, v in grade_hist.items()},
    }

    # dataStatus 更新 (既存のgateを壊さないよう軽量に)
    status = notes.get('dataStatus')
    graded = sum(v for k, v in grade_hist.items() if k)
    if graded >= len(horses) * 0.7 and status in ('preparation', 'bracket-fixed', 'lap-partial'):
        # shingan が7割埋まれば shingan-partial / shingan-fixed に進める
        if status == 'bracket-fixed':
            notes['dataStatus'] = 'shingan-fixed'
        elif status == 'lap-partial':
            notes['dataStatus'] = 'lap-shingan-partial'
        else:
            notes['dataStatus'] = 'shingan-partial'

    if not dry_run:
        rn_path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'\n  summary: S={grade_hist["S"]} A={grade_hist["A"]} B={grade_hist["B"]} C={grade_hist["C"]} D={grade_hist["D"]} null={grade_hist[None]}')
    return narratives


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video',         required=True, help='動画ID (yt_cache に保存済)')
    ap.add_argument('--race',          required=True, help='race-notes slug (例: 2026-04-25-tokyo-11r)')
    ap.add_argument('--start',         type=float, default=None, help='transcript切り出し開始秒')
    ap.add_argument('--end',           type=float, default=None, help='transcript切り出し終了秒')
    ap.add_argument('--extract-only',  action='store_true', help='Claude呼ばずに narrative 抽出だけ表示')
    ap.add_argument('--dry-run',       action='store_true', help='書き込みスキップ')
    args = ap.parse_args()

    print(f'=== apply_shingan.py ===')
    print(f'video: {args.video}')
    print(f'race:  {args.race}')
    if args.start or args.end:
        print(f'window: [{args.start}s - {args.end}s]')
    if args.extract_only: print('[EXTRACT-ONLY mode]')
    if args.dry_run:      print('[DRY-RUN mode]')
    print()

    apply_to_race(args.video, args.race, args.start, args.end,
                  args.extract_only, args.dry_run)


if __name__ == '__main__':
    main()
