#!/usr/bin/env python3
"""
YouTube字幕取得スクリプト（神眼ソース）
========================================
弥永さんの重賞解説動画から自動字幕を取得し、
apply_shingan.py で使える形式でキャッシュする。

Usage:
  python3 scripts/fetch_youtube_transcript.py <url_or_videoid> [--lang ja|en-US]
  python3 scripts/fetch_youtube_transcript.py https://www.youtube.com/watch?v=Yy38_knOHK0

出力:
  scripts/yt_cache/{video_id}.json
  形式: {
    "videoId": "Yy38_knOHK0",
    "lang":    "ja",
    "isGenerated": true,
    "fetchedAt": "2026-04-22T20:00:00",
    "snippets": [{"start": 0.0, "duration": 2.5, "text": "..."}, ...]
  }

依存: pip3 install youtube-transcript-api
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')
CACHE = BASE / 'scripts/yt_cache'


def extract_video_id(s):
    """URLまたはIDから動画IDを抽出"""
    if re.match(r'^[A-Za-z0-9_-]{11}$', s):
        return s
    m = re.search(r'(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})', s)
    if m:
        return m.group(1)
    raise ValueError(f'動画IDを抽出できません: {s}')


def fetch_transcript(video_id, lang='ja'):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print('pip3 install youtube-transcript-api が必要', file=sys.stderr)
        sys.exit(1)

    api = YouTubeTranscriptApi()
    # 利用可能言語リスト
    tl = api.list(video_id)
    available = [(t.language_code, t.is_generated) for t in tl]
    print(f'利用可能な字幕:')
    for lc, gen in available:
        tag = '(自動)' if gen else '(手動)'
        print(f'  - {lc} {tag}')

    # langが指定なければ ja優先、無ければen-US
    try_order = [lang] if lang else ['ja', 'en-US', 'en']
    for try_lang in try_order:
        try:
            snippets = api.fetch(video_id, languages=[try_lang])
            is_gen = any(t.is_generated for t in tl if t.language_code == try_lang)
            return {
                'lang': try_lang,
                'isGenerated': is_gen,
                'snippets': [
                    {'start': s.start, 'duration': s.duration, 'text': s.text}
                    for s in snippets.snippets
                ],
            }
        except Exception as e:
            print(f'  {try_lang}失敗: {e}', file=sys.stderr)
    raise RuntimeError('どの言語でも字幕取得できませんでした')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url_or_id', help='YouTube URL または動画ID')
    ap.add_argument('--lang', default='ja', help='言語コード (ja / en-US)')
    ap.add_argument('--force', action='store_true', help='キャッシュ済みでも再取得')
    args = ap.parse_args()

    video_id = extract_video_id(args.url_or_id)
    CACHE.mkdir(parents=True, exist_ok=True)
    out_path = CACHE / f'{video_id}.json'

    if out_path.exists() and not args.force:
        existing = json.loads(out_path.read_text(encoding='utf-8'))
        total = len(existing.get('snippets', []))
        duration = existing['snippets'][-1]['start'] if total else 0
        print(f'✓ キャッシュ済: {out_path.name} ({total}snippets, {duration/60:.1f}min)')
        print(f'  再取得するには --force')
        return

    print(f'動画ID: {video_id}')
    data = fetch_transcript(video_id, args.lang)
    total = len(data['snippets'])
    duration = data['snippets'][-1]['start'] if total else 0

    out = {
        'videoId':     video_id,
        'lang':        data['lang'],
        'isGenerated': data['isGenerated'],
        'fetchedAt':   datetime.now().isoformat(timespec='seconds'),
        'snippets':    data['snippets'],
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'✓ 保存: {out_path} ({total}snippets, {duration/60:.1f}min, lang={data["lang"]})')


if __name__ == '__main__':
    main()
