#!/usr/bin/env python3
"""
JRDB joc.php の 重賞版CSV生成スクリプト

入力: joc.php を Chrome MCP get_page_text で取得した text を /tmp/joc_raw.txt に保存
出力: docs/data/jockey/YYYY-MM-DD_juushou.csv

CSVカラム:
  順, 騎手名, 属, 1着, 勝率, 連対率, 複勝率,
  G1, G2, G3, 重賞合計,
  3週前複勝率, 2週前複勝率, 1週前複勝率,
  判定アイコン, 判定理由
"""
import re
import csv
import sys
from pathlib import Path
from datetime import date

RAW_PATH = Path('/tmp/joc_raw.txt')
OUT_DIR = Path('/Users/buntawakase/Desktop/ug-keiba/docs/data/jockey')

# joc.php 行フォーマット例:
# "1 Ｃ．ルメール 関西 67 42 34 14 19 52 29.4 47.8 62.7 2 1 4 38 24 23 29 18 11 0 0 0 1 - 4 - 2 - 8 /46.7% 1 - 2 - 0 - 3 /50.0% 6 - 1 - 2 - 2 /81.8%"

LINE_RE = re.compile(
    r'^(?P<rank>\d+)\s+'                            # 順位
    r'(?P<name>\S+)\s+'                              # 騎手名
    r'(?P<zoku>関東|関西|英国|豪州|独国|亜国|大井|佐賀|兵庫|愛知|川崎|船橋|岩手)\s+'
    r'(?P<w>\d+)\s+(?P<p>\d+)\s+(?P<s>\d+)\s+(?P<f>\d+)\s+(?P<fi>\d+)\s+(?P<o>\d+)\s+'
    r'(?P<wr>[\d.]+)\s+(?P<rr>[\d.]+)\s+(?P<fr>[\d.]+)\s+'
    r'(?P<g1>\d+)\s+(?P<g2>\d+)\s+(?P<g3>\d+)\s+'
    r'\d+\s+\d+\s+\d+\s+'                           # 芝1-3
    r'\d+\s+\d+\s+\d+\s+'                           # ダ1-3
    r'\d+\s+\d+\s+\d+\s+'                           # 障1-3
    r'.*?/(?P<w3>[\d.]+)%\s+'                       # 3週前複勝率
    r'.*?/(?P<w2>[\d.]+)%\s+'                       # 2週前複勝率
    r'.*?/(?P<w1>[\d.]+)%'                          # 1週前複勝率
)

def judge(d):
    """ニックドクトリン v0.3 自動判定"""
    g1, g2, g3 = d['g1'], d['g2'], d['g3']
    juushou = g1 + g2 + g3
    win_rate = d['wr']
    w1 = d['w1']
    w3 = d['w3']
    wins = d['w']

    # ⚠️ G1ゼロ異常（イップス疑い・川田パターン）
    if win_rate >= 20 and g1 == 0:
        return ('⚠️', 'G1ゼロ異常（高勝率なのに勝てない）')

    # 🔥🔥 本物・爆発中（ルメールパターン）
    if g1 >= 2 and w1 >= 60:
        return ('🔥🔥', '本物・爆発中')

    # 🔥 重賞勝てる新興（津村パターン）
    if g2 + g3 >= 3 and g1 == 0 and w1 >= 25:
        return ('🔥', '重賞勝てる新興')

    # ✅ 安定本物
    if g1 >= 1 and (g2 + g3 >= 1 or win_rate >= 15):
        return ('✅', '安定本物')

    # ↘ 急降下
    if w3 >= 60 and w1 <= 30:
        return ('↘', '急降下トレンド')

    # 🎓 重賞経験不足（軸不適格）
    if juushou == 0 and wins >= 5:
        return ('🎓', '重賞未経験（軸不可）')

    # 🎓 G1経験不足（G1で軸不可）
    if g1 == 0 and g2 <= 1 and g3 <= 1:
        return ('📖', 'G1経験浅い（G1で軸要注意）')

    return ('→', 'ニュートラル')


def parse(text):
    rows = []
    for line in text.splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        d = {
            'rank': int(m.group('rank')),
            'name': m.group('name'),
            'zoku': m.group('zoku'),
            'w': int(m.group('w')),
            'wr': float(m.group('wr')),
            'rr': float(m.group('rr')),
            'fr': float(m.group('fr')),
            'g1': int(m.group('g1')),
            'g2': int(m.group('g2')),
            'g3': int(m.group('g3')),
            'w3': float(m.group('w3')),
            'w2': float(m.group('w2')),
            'w1': float(m.group('w1')),
        }
        d['juushou'] = d['g1'] + d['g2'] + d['g3']
        icon, reason = judge(d)
        d['icon'] = icon
        d['reason'] = reason
        rows.append(d)
    return rows


def main():
    if not RAW_PATH.exists():
        print(f'❌ {RAW_PATH} が見つかりません', file=sys.stderr)
        print('   Chrome MCP で http://www.jrdb.com/member/jrdv/joc/joc.php を', file=sys.stderr)
        print('   get_page_text して /tmp/joc_raw.txt に保存してください', file=sys.stderr)
        sys.exit(1)

    text = RAW_PATH.read_text(encoding='utf-8')
    rows = parse(text)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f'{date.today().isoformat()}_juushou.csv'

    with out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            '順', '騎手名', '属',
            '1着', '勝率', '連対率', '複勝率',
            'G1', 'G2', 'G3', '重賞合計',
            '3週前複勝率', '2週前複勝率', '1週前複勝率',
            '判定', '判定理由'
        ])
        for d in rows:
            writer.writerow([
                d['rank'], d['name'], d['zoku'],
                d['w'], d['wr'], d['rr'], d['fr'],
                d['g1'], d['g2'], d['g3'], d['juushou'],
                d['w3'], d['w2'], d['w1'],
                d['icon'], d['reason']
            ])

    print(f'✅ {out} に {len(rows)} 行書き出し')

    # サマリ表示
    print('\n=== 判定別集計 ===')
    from collections import Counter
    c = Counter(d['icon'] for d in rows)
    for icon, n in c.most_common():
        print(f'  {icon}  {n}人')

    print('\n=== 注目騎手 (リーディング20位以内) ===')
    for d in rows[:20]:
        print(f"  {d['rank']:3d}位 {d['name']:12s} {d['icon']} {d['reason']}  "
              f"(勝率{d['wr']:5.1f}% / G1{d['g1']}・G2{d['g2']}・G3{d['g3']} / "
              f"3w{d['w3']:5.1f}→1w{d['w1']:5.1f})")


if __name__ == '__main__':
    main()
