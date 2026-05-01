#!/usr/bin/env python3
"""
auto_pick.py — 4神grade 1位の4頭を自動選定し、race-notes.presentation.horses に格納

ロジック:
  1. 各神（青龍/朱雀/白虎/玄武）ごとに grade S>A>B>C>D 順位付け
  2. 1位馬を選定。同grade複数の場合は「他神grade合計の高い順」でタイブレーク
  3. 4神中で同馬が複数神1位の場合、重複神は次点を繰り上げて必ず別馬4頭を確保

Usage:
  # ドライラン（書き込みなし、結果を端末に表示）
  python3 scripts/auto_pick.py 2026-04-26-tokyo-11r --dry-run
  python3 scripts/auto_pick.py --day 2026-04-26 --dry-run

  # 本反映（race-notes.presentation.horses を上書き）
  python3 scripts/auto_pick.py 2026-04-26-tokyo-11r --apply
  python3 scripts/auto_pick.py --day 2026-04-26 --apply
"""
import json, argparse, sys, os
from pathlib import Path

RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'

GRADE_RANK = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}

GODS = ['seiryu', 'suzaku', 'byakko', 'genbu']

GOD_LABEL = {
    'seiryu': '青龍', 'suzaku': '朱雀', 'byakko': '白虎', 'genbu': '玄武',
}
GOD_SUB = {
    'seiryu': '言霊', 'suzaku': '速眼', 'byakko': 'ラップ', 'genbu': '地脈',
}
GOD_EMOJI = {
    'seiryu': '🐉', 'suzaku': '🔥', 'byakko': '🐅', 'genbu': '🐢',
}


def get_god_grade(horse, god):
    """各馬の各神 grade を取得（race-notes 構造から）"""
    if god == 'seiryu':
        return (horse.get('relComment') or {}).get('grade')
    if god == 'suzaku':
        # suzakuGrade.grade（速×眼合議）優先
        sg = horse.get('suzakuGrade') or {}
        if sg.get('grade'):
            return sg['grade']
        # fallback: gan のみ（v2 移行期）
        gan = (sg.get('gan') or {}).get('grade')
        return gan
    if god == 'byakko':
        return (horse.get('yugomiLapGrade') or {}).get('grade')
    if god == 'genbu':
        # courseDataGrade.grade（玄武v1）優先
        cd = (horse.get('courseDataGrade') or {}).get('grade')
        if cd:
            return cd
        # fallback: gaikyuFactor.grade
        return (horse.get('gaikyuFactor') or {}).get('grade')
    return None


def grade_score(g):
    return GRADE_RANK.get(g, 0)


def total_other_grade_score(horse, exclude_god):
    """他神gradeの合計（タイブレーク用）"""
    return sum(grade_score(get_god_grade(horse, g)) for g in GODS if g != exclude_god)


def rank_for_god(horses, god):
    """各神のgradeランキング。タイブレーク=他神grade合計（高い順）"""
    return sorted(
        horses,
        key=lambda h: (
            -grade_score(get_god_grade(h, god)),
            -total_other_grade_score(h, god),
        )
    )


def pick_4gods(horses):
    """4神1位の4頭を選定。重複の場合は次点繰り上げで別馬4頭を確保"""
    selected_names = set()
    picks = []
    god_rankings = {g: rank_for_god(horses, g) for g in GODS}

    for god in GODS:
        for horse in god_rankings[god]:
            if horse.get('name') not in selected_names:
                grade = get_god_grade(horse, god)
                # rank within this god (1-based)
                rank_in_god = god_rankings[god].index(horse) + 1
                picks.append({
                    'god': god,
                    'horse': horse,
                    'grade': grade,
                    'rankInGod': rank_in_god,
                })
                selected_names.add(horse.get('name'))
                break
    return picks


def build_badges(horse):
    """各馬の4神badges を構築（既存 final-display.html の badge スキーマに準拠）"""
    badges = []
    for g in GODS:
        grade = get_god_grade(horse, g) or '—'
        b = {
            't': g,
            'g': grade,
            'label': f'{GOD_LABEL[g]}（{GOD_SUB[g]}）',
        }
        if g == 'suzaku':
            sg = horse.get('suzakuGrade') or {}
            soku = (sg.get('soku') or {}).get('grade') or '—'
            gan  = (sg.get('gan')  or {}).get('grade') or '—'
            b['soku'] = soku
            b['gan']  = gan
        badges.append(b)
    return badges


def to_presentation_horse(pick):
    """auto_pick の pick を presentation.horses 形式に変換"""
    h = pick['horse']
    god = pick['god']
    return {
        'god':       god,
        'godLabel':  GOD_LABEL[god],
        'godEmoji':  GOD_EMOJI[god],
        'godGrade':  pick['grade'],
        'rankInGod': pick['rankInGod'],
        # 互換のため mark/markLabel も持たせる（旧UIへのフォールバック）
        'mark':      GOD_EMOJI[god],
        'markLabel': f'{GOD_LABEL[god]}1位',
        'num':       str(h.get('num') or h.get('umaban') or '—'),
        'gate':      str(h.get('gate') or '—'),
        'name':      h.get('name', '?'),
        'ninki':     '—',  # 確定オッズ取得前は空、result反映で上書きされる
        'odds':      str(h.get('expectedOdds') or '—'),
        'sire':      h.get('sire', '—'),
        'bms':       h.get('broodmareSire', h.get('bms', '—')),
        'jockey':    h.get('jockey', '—'),
        'trainer':   h.get('trainer', '—'),
        'gaikyu':    h.get('gaikyu', '—'),
        'prevName':  h.get('prevName', h.get('relComment', {}).get('prevRace', '—') if isinstance(h.get('relComment'), dict) else '—'),
        'prevFinish':h.get('prevFinish', '—'),
        'badges':    build_badges(h),
        'comment':   (h.get('relComment') or {}).get('keyword', '—') if isinstance(h.get('relComment'), dict) else '—',
    }


def process_race(race_key, apply=False):
    path = RN_DIR / f'{race_key}.json'
    if not path.exists():
        print(f"  ⚠ NOT FOUND: {path}")
        return None
    d = json.load(open(path))
    horses = d.get('horses') or []
    if not horses:
        print(f"  ⚠ horses 空: {race_key}")
        return None

    picks = pick_4gods(horses)
    pres_horses = [to_presentation_horse(p) for p in picks]

    # bets.wide / bets.umaren の horses を 4神picks の馬名に同期
    pres = d.setdefault('presentation', {})
    bets = pres.setdefault('bets', {})
    horse_names = [p['name'] for p in pres_horses]
    n = len(pres_horses)
    combos = n * (n - 1) // 2  # 4頭BOX = 6点

    bets['strategy'] = 'wide-umaren'
    bets['wide'] = {
        'horses':   horse_names,
        'perPoint': 100,
        'points':   combos,
        'spend':    combos * 100,
    }
    bets['umaren'] = {
        'horses':   horse_names,
        'perPoint': 100,
        'points':   combos,
        'spend':    combos * 100,
    }
    bets['totalSpend'] = combos * 100 * 2  # ワイド6点 + 馬連6点 = 1200円

    if apply:
        pres['horses'] = pres_horses
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

    return pres_horses


def print_picks(race_key, picks):
    if not picks:
        return
    print(f"\n=== {race_key} ===")
    print(f"  {'神':<6} {'rank':>4} {'grade':>5}  {'馬名':<14}  他神合計")
    print(f"  {'-'*60}")
    for p in picks:
        # 他神合計を再計算（表示用）
        other_total = sum(grade_score(b['g']) for b in p['badges'] if b['t'] != p['god'])
        gg = p.get('godGrade') or '—'  # None → '—' にしてformat落ちを防ぐ
        print(f"  {GOD_EMOJI[p['god']]} {GOD_LABEL[p['god']]:<3} {p['rankInGod']:>4}位  {gg:>3}    {p['name']:<14}  {other_total}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('race_key', nargs='?')
    ap.add_argument('--day',     help='例: 2026-04-26')
    ap.add_argument('--dry-run', action='store_true', help='書き込まずに結果のみ表示（デフォルト）')
    ap.add_argument('--apply',   action='store_true', help='race-notes に書き込み')
    args = ap.parse_args()

    if args.day:
        keys = [p.stem for p in sorted(RN_DIR.glob(f'{args.day}-*.json'))
                if not any(p.name.endswith(s) for s in ['.bak','.bak2','.bak3','.bak4'])]
    elif args.race_key:
        keys = [args.race_key]
    else:
        ap.print_help()
        sys.exit(0)

    apply_mode = args.apply  # --dry-run / no-flag は両方ドライラン
    for k in keys:
        path = RN_DIR / f'{k}.json'
        if not path.exists():
            print(f"  ⚠ NOT FOUND: {k}")
            continue
        d = json.load(open(path))
        horses = d.get('horses') or []
        if not horses:
            print(f"  ⚠ horses空: {k}")
            continue
        picks_raw = pick_4gods(horses)
        # 表示用に build_badges 含めた dict を渡す
        picks_for_display = [{
            'god': p['god'], 'name': p['horse'].get('name','?'),
            'rankInGod': p['rankInGod'], 'godGrade': p.get('grade'),
            'badges': build_badges(p['horse']),
        } for p in picks_raw]
        print_picks(k, picks_for_display)
        if apply_mode:
            process_race(k, apply=True)
            print(f"  ✓ 書込完了 → race-notes.presentation.horses")
    print()
    print("--apply で本反映、--dry-run（または無指定）で表示のみ。")
