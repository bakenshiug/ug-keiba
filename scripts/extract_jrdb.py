#!/usr/bin/env python3
"""
JRDB txt → structured JSON extractor
=====================================
Parses JRDB individual horse PDF text (post-pypdf extraction) into:
  - basicInfo: 父/母父/生産/兄弟/厩舎/最終外厩情報
  - surfaceTotal: 芝/ダ通算成績
  - gaikyuRecord: 外厩別成績 [{name, record:[勝,2,3,着外]}]
  - jockeyRecord: 騎手別成績
  - turfVenue / dirtVenue: 場別成績 (芝/ダ別)
  - turfCondition / dirtCondition: 馬場状態別成績
  - lastGaikyu: 最終「外厩」情報
  - specialTraits: 近走特記
Usage:
  python3 extract_jrdb.py <txt_file> [<txt_file> ...]
Output: writes <horse>.json next to the txt file, in ../extracted/
"""
import re
import json
import sys
import os
from pathlib import Path

VENUES = ['札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉']
TRACK_CONDS = ['良', '稍重', '重', '不良']

# ── Regex patterns ─────────────────────────────────────────
# 外厩別成績 / 騎手別成績: "{name}{d} {d} {d} {d}"  e.g. "チャンピオンヒルズ1 0 0 0"
#   ※ name が非数字で始まる and ends where digit appears (+space+3more digits)
PAT_RECORD = re.compile(r'^(.+?)(\d)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')

# 場別 / 馬場状態別: "{name}{d}-{d}-{d}-{d} ..."  e.g. "東京1-0-0-0 100100100" or "良 1-0-0-0 100100100"
PAT_VENUE = re.compile(r'^(.+?)\s*(\d+)-(\d+)-(\d+)-(\d+)')

# 芝/ダ 通算成績: "芝 1 - 0 - 0 - 0100%100%100%48"
PAT_SURFACE_TOTAL = re.compile(
    r'^(芝|ダ)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)(\d{2,3}%|\s)',
    re.MULTILINE
)

# 最終「外厩」情報: "最終「外厩」情報 1走前:2026-2/3　チャンピオンヒルズ地方交流 0 - 0 - 0 - 0単勝回収値 1590"
PAT_LAST_GAIKYU = re.compile(
    r'最終「外厩」情報\s*(\d+)走前[:：]?\s*([\d/\-]+)[　\s]*([^\d\s]+?)(?:地方交流)?'
    r'\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+).*?単勝回収値\s*(\d+)'
)

# 父/母父: "父 キズナ2010父父 ディープインパクト..." (父 is line start, not after 父父)
PAT_SIRE = re.compile(r'^父\s+([^\d]+?)\s*(\d{4})', re.MULTILINE)
PAT_BMS = re.compile(r'母父\s*([^\d]+?)\s*(\d{4})')

# 厩舎: "...厩舎 吉岡辰..."
PAT_TRAINER = re.compile(r'厩舎\s*(\S+?)\s+データ更新日')

# 近走特記
# PDF extraction can break "近走特記" across multiple lines (e.g. "近走\n特記\n").
# Allow whitespace between each character.
PAT_TRAITS = re.compile(r'近\s*走\s*特\s*記\s*(.+?)(?=最終「外厩」|テン３F順位)', re.DOTALL)


def clean_name(s):
    """Remove PDF extraction artifacts from name strings."""
    return re.sub(r'[\s　]+', '', s).strip()


def parse_record(s):
    """Parse '1 0 0 0' or '1-0-0-0' → [1,0,0,0]"""
    m = re.findall(r'\d+', s)
    return [int(x) for x in m[:4]] if len(m) >= 4 else None


def extract_section(lines, start_marker, end_markers):
    """Return lines between start_marker and any of end_markers (exclusive)."""
    out = []
    in_section = False
    for line in lines:
        if not in_section:
            if start_marker in line:
                in_section = True
            continue
        if any(em in line for em in end_markers):
            break
        if line.strip():
            out.append(line.rstrip())
    return out


def parse_gaikyu_records(lines):
    """「外厩」別成績"""
    section = extract_section(lines, '「外厩」別成績', ['騎手別成績', '芝成績', '過 去 走', '過去走'])
    results = []
    for line in section:
        m = PAT_RECORD.match(line.strip())
        if m:
            name = clean_name(m.group(1))
            record = [int(m.group(i)) for i in range(2, 6)]
            if name and sum(record) > 0:
                results.append({'name': name, 'record': record})
    return results


def parse_jockey_records(lines):
    """騎手別成績"""
    section = extract_section(lines, '騎手別成績', ['芝成績', 'ダート成績', '過 去 走', '過去走'])
    results = []
    for line in section:
        m = PAT_RECORD.match(line.strip())
        if m:
            name = clean_name(m.group(1))
            record = [int(m.group(i)) for i in range(2, 6)]
            if name and sum(record) > 0:
                results.append({'name': name, 'record': record})
    return results


def parse_venue_block(lines, start_marker, end_markers):
    """芝成績 or ダート成績 — split into venues & track conditions."""
    section = extract_section(lines, start_marker, end_markers)
    venues = {}
    conditions = {}
    for line in section:
        s = line.strip()
        m = PAT_VENUE.match(s)
        if not m:
            continue
        name = clean_name(m.group(1))
        record = [int(m.group(i)) for i in range(2, 6)]
        if name in VENUES:
            venues[name] = record
        elif name in TRACK_CONDS:
            conditions[name] = record
    return venues, conditions


def parse_surface_totals(text):
    """芝 通算成績 / ダ 通算成績 from header lines.
    e.g. '芝 1 - 0 - 1 - 225%25%50%47' → record=[1,0,1,2], idm=47
    """
    # Simpler two-step: find surface line, then extract record + trailing IDM
    out = {}
    for line in text.splitlines():
        s = line.strip()
        # 4th record = single digit (fused with pct in PDF extraction)
        m = re.match(r'^(芝|ダ)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d)(.*)$', s)
        if not m:
            continue
        surface = m.group(1)
        record = [int(m.group(i)) for i in range(2, 6)]
        # Last record digit may be fused with pct (e.g. "225%") — the fourth record is
        # really just the first \d+ before the '%'. Let's extract IDM from tail.
        tail = m.group(6)
        # Look for trailing 2-3 digit IDM at end (or '--')
        t = re.search(r'(\d{2,3})\s*$', tail)
        idm = int(t.group(1)) if t else None
        out[surface] = {'record': record, 'idm': idm}
    return out


def parse_last_gaikyu(text):
    m = PAT_LAST_GAIKYU.search(text)
    if not m:
        return None
    return {
        'sogoBack': int(m.group(1)),   # 何走前
        'date': m.group(2),
        'facility': clean_name(m.group(3)),
        'record': [int(m.group(i)) for i in range(4, 8)],
        'tanshoReturnAll': int(m.group(8)),
    }


def parse_basic(text):
    info = {}
    m = PAT_SIRE.search(text)
    if m: info['sire'] = m.group(1).strip()
    m = PAT_BMS.search(text)
    if m: info['broodmareSire'] = m.group(1).strip()
    m = PAT_TRAINER.search(text)
    if m: info['trainer'] = m.group(1).strip()
    return info


def parse_traits(text):
    m = PAT_TRAITS.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    # Line-break artifacts: traits like "後ろから行く○" can get split as
    # "後ろから行く\n○". Remove newlines so orphan ○/× re-attach to prior token.
    raw = raw.replace('\n', '')
    # Split by all Unicode whitespace incl. U+00A0 NBSP (JRDB PDF uses NBSP as separator)
    items = [t.strip() for t in re.split(r'[　\s]+', raw) if t.strip()]
    return items


def extract_horse(txt_path):
    txt = Path(txt_path).read_text(encoding='utf-8')
    lines = txt.splitlines()
    name = Path(txt_path).stem

    return {
        'horseName': name,
        'basicInfo': parse_basic(txt),
        'specialTraits': parse_traits(txt),
        'lastGaikyu': parse_last_gaikyu(txt),
        'surfaceTotal': parse_surface_totals(txt),
        'gaikyuRecord': parse_gaikyu_records(lines),
        'jockeyRecord': parse_jockey_records(lines),
        'turfVenue': parse_venue_block(lines, '芝成績', ['ダート成績', '過 去 走', '過去走'])[0],
        'turfCondition': parse_venue_block(lines, '芝成績', ['ダート成績', '過 去 走', '過去走'])[1],
        'dirtVenue': parse_venue_block(lines, 'ダート成績', ['過 去 走', '過去走'])[0],
        'dirtCondition': parse_venue_block(lines, 'ダート成績', ['過 去 走', '過去走'])[1],
    }


def main():
    if len(sys.argv) < 2:
        print('usage: extract_jrdb.py <txt_file> [...]', file=sys.stderr)
        sys.exit(1)

    for txt_path in sys.argv[1:]:
        data = extract_horse(txt_path)

        # Write to ../extracted/{horse}.json
        src_dir = Path(txt_path).parent
        out_dir = src_dir.parent / 'extracted'
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f'{Path(txt_path).stem}.json'

        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'→ {out_path}')


if __name__ == '__main__':
    main()
