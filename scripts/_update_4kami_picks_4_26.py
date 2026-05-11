#!/usr/bin/env python3
"""
2026-04-26 5レース 4神picks を race-notes.presentation.horses に書込
ニック確定マトリクス（玄武+25%反映後）に基づく
"""
import json
from pathlib import Path

RN_DIR = Path(__file__).resolve().parent.parent / 'docs/data/race-notes'

GOD_LABEL = {'seiryu': '青龍', 'suzaku': '朱雀', 'byakko': '白虎', 'genbu': '玄武'}
GOD_SUB   = {'seiryu': '言霊', 'suzaku': '速眼', 'byakko': 'ラップ', 'genbu': '地脈'}
GOD_EMOJI = {'seiryu': '🐉', 'suzaku': '🔥', 'byakko': '🐅', 'genbu': '🐢'}

# レース別ピック: {race_key: [(god, name, grade), ...]}
PICKS = {
    '2026-04-26-kyoto-10r': [   # センテニアル・PS
        ('seiryu', 'レイニング',          'S'),
        ('suzaku', 'ミスタージーティー',   'A'),
        ('byakko', 'ショウナンラピダス',   'S'),
        ('genbu',  'レディーミコノス',     'S'),
    ],
    '2026-04-26-tokyo-10r': [   # オアシスS
        ('seiryu', 'ドンインザムード',    'S'),
        ('suzaku', 'バトルクライ',        'S'),
        ('byakko', 'オウギノカナメ',      'S'),
        ('genbu',  'ウェイワードアクト',  'S'),
    ],
    '2026-04-26-fukushima-11r': [   # モルガナイトS
        ('seiryu', 'サウンド',            'S'),
        ('suzaku', 'シュタールヴィント',  'A'),
        ('byakko', 'イツモニコニコ',      'S'),
        ('genbu',  'ナムラローズマリー',  'S'),
    ],
    '2026-04-26-kyoto-11r': [   # マイラーズC
        ('seiryu', 'ベラジオボンド',      'S'),
        ('suzaku', 'アドマイヤズーム',    'S'),
        ('byakko', 'エルトンバローズ',    'S'),
        ('genbu',  'ショウナンアデイブ',  'S'),
    ],
    '2026-04-26-tokyo-11r': [   # フローラS
        ('seiryu', 'エンネ',              'S'),
        ('suzaku', 'ラフターラインズ',    'A'),
        ('byakko', 'ペイシャシス',        'S'),
        ('genbu',  'サムシングスイート',  'S'),
    ],
}


def get_horse_from_horses(horses, name):
    """horses[]から馬名で検索"""
    for h in horses:
        if h.get('name') == name:
            return h
    return None


def build_badges_from_horse(horse, picked_god, picked_grade):
    """horses[]データから4神badges構築。picked_godは matrix grade で上書き"""
    badges = []
    for g in ('seiryu', 'suzaku', 'byakko', 'genbu'):
        b = {'t': g, 'label': f'{GOD_LABEL[g]}（{GOD_SUB[g]}）'}
        if g == 'seiryu':
            b['g'] = (horse.get('relComment') or {}).get('grade') or '—'
        elif g == 'suzaku':
            sg = horse.get('suzakuGrade') or {}
            b['g'] = sg.get('grade') or '—'
            b['soku'] = (sg.get('soku') or {}).get('grade') or '—'
            b['gan']  = (sg.get('gan')  or {}).get('grade') or '—'
        elif g == 'byakko':
            b['g'] = (horse.get('yugomiLapGrade') or {}).get('grade') or '—'
        elif g == 'genbu':
            b['g'] = (horse.get('courseDataGrade') or {}).get('grade') or '—'
        # picked_god はmatrix gradeで上書き
        if g == picked_god:
            b['g'] = picked_grade
        badges.append(b)
    return badges


def build_badges_minimal(picked_god, picked_grade):
    """horses[]なしレース用：picked_god のみ grade、他は "—" """
    badges = []
    for g in ('seiryu', 'suzaku', 'byakko', 'genbu'):
        b = {'t': g, 'label': f'{GOD_LABEL[g]}（{GOD_SUB[g]}）'}
        b['g'] = picked_grade if g == picked_god else '—'
        if g == 'suzaku':
            b['soku'] = '—'
            b['gan']  = '—'
        badges.append(b)
    return badges


def make_pres_horse(picked_god, name, picked_grade, horse=None):
    """presentation.horses 形式に変換"""
    if horse:
        badges = build_badges_from_horse(horse, picked_god, picked_grade)
        comment = (horse.get('relComment') or {}).get('keyword', '—') if isinstance(horse.get('relComment'), dict) else '—'
        prev = '—'
        rc = horse.get('relComment')
        if isinstance(rc, dict):
            prev = rc.get('prevRace') or '—'
        return {
            'god':       picked_god,
            'godLabel':  GOD_LABEL[picked_god],
            'godEmoji':  GOD_EMOJI[picked_god],
            'godGrade':  picked_grade,
            'rankInGod': 1,
            'mark':      GOD_EMOJI[picked_god],
            'markLabel': f'{GOD_LABEL[picked_god]}1位',
            'num':       str(horse.get('num') or horse.get('umaban') or '—'),
            'gate':      str(horse.get('gate') or '—'),
            'name':      name,
            'ninki':     '—',
            'odds':      str(horse.get('expectedOdds') or '—'),
            'sire':      horse.get('sire', '—'),
            'bms':       horse.get('broodmareSire', horse.get('bms', '—')),
            'jockey':    horse.get('jockey', '—'),
            'trainer':   horse.get('trainer', '—'),
            'gaikyu':    horse.get('gaikyu', '—'),
            'prevName':  prev,
            'prevFinish':horse.get('prevFinish', '—'),
            'badges':    badges,
            'comment':   comment,
        }
    else:
        # horses[]データなし
        return {
            'god':       picked_god,
            'godLabel':  GOD_LABEL[picked_god],
            'godEmoji':  GOD_EMOJI[picked_god],
            'godGrade':  picked_grade,
            'rankInGod': 1,
            'mark':      GOD_EMOJI[picked_god],
            'markLabel': f'{GOD_LABEL[picked_god]}1位',
            'num':       '—',
            'gate':      '—',
            'name':      name,
            'ninki':     '—',
            'odds':      '—',
            'sire':      '—',
            'bms':       '—',
            'jockey':    '—',
            'trainer':   '—',
            'gaikyu':    '—',
            'prevName':  '—',
            'prevFinish':'—',
            'badges':    build_badges_minimal(picked_god, picked_grade),
            'comment':   '神託確認待ち',
        }


def update(race_key):
    path = RN_DIR / f'{race_key}.json'
    d = json.load(open(path))
    horses = d.get('horses') or []

    picks = PICKS[race_key]
    pres_horses = []
    for god, name, grade in picks:
        h = get_horse_from_horses(horses, name)
        pres_horses.append(make_pres_horse(god, name, grade, h))

    pres = d.setdefault('presentation', {})
    pres['horses'] = pres_horses

    # bets.wide も更新
    bets = pres.setdefault('bets', {})
    bets['strategy'] = 'wide-only'
    bets['wide'] = {
        'horses': [p['name'] for p in pres_horses],
        'perPoint': 100,
    }
    n = len(pres_horses)
    bets['totalSpend'] = (n * (n - 1) // 2) * 100  # 4頭BOX = 6点 = ¥600

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    name = d.get('race', {}).get('name', '?')
    print(f"  ✓ {race_key:<32} {name:<20}")
    for p in pres_horses:
        print(f"      {p['godEmoji']} {p['godLabel']}({p['godGrade']}) {p['name']}")


if __name__ == '__main__':
    for k in PICKS.keys():
        update(k)
    print('\n完了！5レース×4頭=20頭')
