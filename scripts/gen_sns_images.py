#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNS シェア画像生成スクリプト — 四神の御神託
=====================================
使用: python3 scripts/gen_sns_images.py [--only <race-label>]

入力:
  docs/data/race-notes/{race}.json の finalBets.presentation

出力:
  docs/img/sns/{race}-twitter.png  (1080x1080 正方形)
  docs/img/sns/{race}-tiktok.png   (1080x1920 縦長 9:16)

デザイン:
  - 神社風（朱・金・墨）× 四神カラー
  - Hiragino Mincho / Kakugo フォント
  - 絵文字はビットマップ込みで未対応 → 日本語ラベル（青龍/朱雀/白虎/玄武）で表現
"""
import json
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')
OUT_DIR = BASE / 'docs/img/sns'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ギーニョ大神 御本尊画像 (縦長 1616x2176, アスペクト比 0.743)
GIINYO_IMG_PATH = BASE / 'docs/img/giinyo-daijin.png'
GIINYO_IMG = Image.open(GIINYO_IMG_PATH).convert('RGBA') if GIINYO_IMG_PATH.exists() else None

# ニック Vtuber アバター (正方形クロップ版優先)
_NICK_PATHS = [BASE / 'docs/img/nick-vtuber-square.png',
               BASE / 'docs/img/nick-vtuber.png',
               BASE / 'docs/img/nick.png']
NICK_IMG = None
for _p in _NICK_PATHS:
    if _p.exists():
        NICK_IMG = Image.open(_p).convert('RGBA')
        break


def paste_circular(base_img, src_img, cx, cy, radius, halo=True):
    """base_img の (cx, cy) を中心に半径 radius の円形で src_img を貼る
    halo=True なら外側に金色の二重後光を描画"""
    draw = ImageDraw.Draw(base_img)
    # 後光
    if halo:
        r1 = radius + 18
        draw.ellipse([(cx - r1, cy - r1), (cx + r1, cy + r1)],
                     fill=(249, 233, 183), outline=C_KIN, width=2)
        r2 = radius + 10
        draw.ellipse([(cx - r2, cy - r2), (cx + r2, cy + r2)],
                     outline=C_KIN_D, width=1)
    # 画像を正方形にリサイズ
    size = radius * 2
    resized = src_img.resize((size, size), Image.LANCZOS).convert('RGBA')
    # 円形マスク
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (size, size)], fill=255)
    # 貼り付け
    base_img.paste(resized, (cx - radius, cy - radius), mask)
    # 金縁
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                 outline=C_KIN_D, width=3)

RACE_MAP = [
    ('2026-04-25-aobasho',  '2026-04-25-tokyo-11r', '青葉賞',    'G2 東京芝2400m',  '2026/04/25 土'),
    ('2026-04-26-floras',   '2026-04-26-tokyo-11r', 'フローラS', 'G2 東京芝2000m',  '2026/04/26 日'),
    ('2026-04-26-milers-c', '2026-04-26-kyoto-11r', 'マイラーズC','G2 京都芝1600m', '2026/04/26 日'),
]

FONT_MINCHO = '/System/Library/Fonts/ヒラギノ明朝 ProN.ttc'
FONT_KAKU_W3 = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
FONT_KAKU_W8 = '/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc'
FONT_KAKU_W9 = '/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc'

# 神社風カラーパレット
C_PAPER   = (244, 238, 221)  # 和紙
C_PAPER_D = (240, 234, 219)
C_SUMI    = (26, 26, 26)     # 墨
C_SHU     = (155, 45, 48)    # 朱
C_SHU_D   = (122, 30, 30)
C_KIN     = (201, 169, 97)   # 金
C_KIN_D   = (139, 117, 48)
C_MIDORI  = (31, 77, 46)     # 緑（青龍）
C_MUTED   = (127, 117, 100)

# 四神カラー
SHIJIN = {
    'seiryu':  {'jp': '青龍', 'factor': '言霊',  'color': C_MIDORI},
    'suzaku':  {'jp': '朱雀', 'factor': '神眼',  'color': C_SHU},
    'byakko':  {'jp': '白虎', 'factor': 'ラップ', 'color': C_KIN_D},
    'genbu':   {'jp': '玄武', 'factor': '外厩',  'color': (30, 30, 30)},
}

GRADE_COLOR = {
    'S': (196, 154, 61),
    'A': (47, 92, 59),
    'B': (45, 74, 110),
    'C': (160, 102, 84),
    'D': (62, 58, 54),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, text, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0]


def text_h(draw, text, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[3] - bbox[1]


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """簡易丸角四角形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def load_presentation(rn):
    p = BASE / 'docs/data/race-notes' / f'{rn}.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    fb = data.get('finalBets') or {}
    pres = fb.get('presentation')
    if not pres:
        raise RuntimeError(f'{rn}: presentation 未生成。 gen_presentation.py を先に実行してください。')
    return data, fb, pres


def role_meta(role_tag):
    return {
        'main':    {'accent': C_SHU,    'label': '本命'},
        'counter': {'accent': C_KIN_D,  'label': '対抗'},
        'support': {'accent': C_MIDORI, 'label': '押さえ'},
        'hole':    {'accent': (110, 74, 31), 'label': '穴'},
    }.get(role_tag, {'accent': C_MUTED, 'label': '候補'})


def wrap_text(draw, text, fnt, max_w):
    """テキストを幅で折り返す (日本語想定: 1文字ずつ)"""
    lines = []
    line = ''
    for ch in text:
        if ch == '\n':
            lines.append(line)
            line = ''
            continue
        test = line + ch
        if text_w(draw, test, fnt) > max_w:
            lines.append(line)
            line = ch
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def draw_shijin_chip(draw, xy, kind, grade):
    """四神グレードチップ 1個 (横幅140 × 高さ48想定)"""
    x1, y1, x2, y2 = xy
    meta = SHIJIN[kind]
    color = meta['color']
    draw_rounded_rect(draw, (x1, y1, x2, y2), radius=6, fill=(255, 255, 255), outline=color, width=2)

    # 漢字（青龍等）
    f_jp = font(FONT_MINCHO, 20)
    draw.text((x1 + 10, y1 + 4), meta['jp'], fill=color, font=f_jp)
    # ファクター小
    f_factor = font(FONT_KAKU_W3, 11)
    draw.text((x1 + 10, y1 + 28), meta['factor'], fill=C_MUTED, font=f_factor)

    # グレード 右詰め
    g_color = GRADE_COLOR.get(grade, (180, 170, 150))
    g_text = grade if grade else '—'
    f_g = font(FONT_KAKU_W9, 22)
    tw = text_w(draw, g_text, f_g)
    # 背景
    bg_w = 34
    bg_x1 = x2 - bg_w - 8
    bg_y1 = y1 + 8
    draw_rounded_rect(draw, (bg_x1, bg_y1, bg_x1 + bg_w, bg_y1 + 32), radius=4, fill=g_color)
    draw.text((bg_x1 + (bg_w - tw) // 2, bg_y1 + 2), g_text, fill=(255, 255, 255), font=f_g)


def draw_header(draw, W, H, race_label, race_meta, date_label, readiness, total_spend, y_start=30):
    """ヘッダー: 御神託降臨 + レース情報"""
    # 上部金線
    draw.line([(60, y_start + 6), (W - 60, y_start + 6)], fill=C_KIN, width=2)
    draw.line([(60, y_start + 10), (W - 60, y_start + 10)], fill=C_KIN, width=1)

    # FINAL ORACLE
    f_eng = font(FONT_KAKU_W3, 20)
    s = 'FINAL  ORACLE   ／   四神の御神託'
    draw.text((W // 2 - text_w(draw, s, f_eng) // 2, y_start + 26), s, fill=C_KIN_D, font=f_eng)

    # 御神託降臨
    f_title = font(FONT_MINCHO, 68)
    t = '御神託降臨'
    draw.text((W // 2 - text_w(draw, t, f_title) // 2, y_start + 58), t, fill=C_SUMI, font=f_title)

    # レース名（大）
    f_race = font(FONT_MINCHO, 48)
    tw_race = text_w(draw, race_label, f_race)
    y_race = y_start + 160
    # 朱背景帯
    draw.rectangle([(0, y_race - 8), (W, y_race + 62)], fill=C_SHU)
    draw.text((W // 2 - tw_race // 2, y_race - 4), race_label, fill=(255, 248, 232), font=f_race)

    # メタ情報
    f_meta = font(FONT_KAKU_W3, 22)
    meta_text = f'{race_meta}　／　{date_label}'
    draw.text((W // 2 - text_w(draw, meta_text, f_meta) // 2, y_race + 64), meta_text, fill=C_SUMI, font=f_meta)

    # 揃い率 + 投資
    f_stat = font(FONT_KAKU_W3, 16)
    f_amt = font(FONT_KAKU_W9, 26)
    sp_text = f'¥{total_spend:,}'
    re_text = f'揃い率 {readiness}'
    draw.text((80, y_race + 108), re_text, fill=C_MUTED, font=f_stat)
    draw.text((W - 80 - text_w(draw, sp_text, f_amt), y_race + 100), sp_text, fill=C_SHU, font=f_amt)

    return y_race + 148  # 次のy位置を返す


def draw_horse_card(draw, xy, ph, scale=1.0):
    """1頭分プレゼンカード (指定矩形内に収める)"""
    x1, y1, x2, y2 = xy
    w = x2 - x1
    h = y2 - y1

    role = role_meta(ph.get('roleTag'))
    accent = role['accent']

    # 枠
    draw_rounded_rect(draw, (x1, y1, x2, y2), radius=10, fill=(255, 255, 255), outline=accent, width=3)

    # 役割帯 (上部)
    band_h = int(42 * scale)
    draw.rectangle([(x1 + 3, y1 + 3), (x2 - 3, y1 + band_h)], fill=accent)

    # 役割ラベル
    f_role = font(FONT_MINCHO, int(22 * scale))
    role_text = f'【{role["label"]}】'
    draw.text((x1 + 12, y1 + 6), role_text, fill=(255, 248, 232), font=f_role)

    # 人気/穴バッジ
    is_hole = ph.get('popularity') == 'hole'
    pop_text = '[穴]' if is_hole else '[人気]'
    f_pop = font(FONT_KAKU_W8, int(16 * scale))
    pop_tw = text_w(draw, pop_text, f_pop)
    px = x1 + 12 + text_w(draw, role_text, f_role) + 10
    # バッジ背景
    bg_col = (255, 229, 161) if is_hole else (212, 240, 200)
    draw.rectangle([(px - 4, y1 + 10), (px + pop_tw + 4, y1 + 10 + int(22 * scale))], fill=bg_col)
    draw.text((px, y1 + 11), pop_text, fill=C_SUMI, font=f_pop)

    # スコア 右詰め
    score = ph.get('score')
    if score is not None:
        f_score = font(FONT_KAKU_W9, int(22 * scale))
        sc_text = f'{score:.1f}pt'
        sw = text_w(draw, sc_text, f_score)
        draw.text((x2 - 12 - sw, y1 + 9), sc_text, fill=(255, 248, 232), font=f_score)

    # コンテンツ領域
    cy = y1 + band_h + 12
    # 馬番 + 馬名
    num = ph.get('num')
    num_text = str(num) if num is not None else '?'
    f_num = font(FONT_KAKU_W9, int(30 * scale))
    num_box_w = int(52 * scale)
    num_box_h = int(42 * scale)
    draw_rounded_rect(draw, (x1 + 14, cy, x1 + 14 + num_box_w, cy + num_box_h), radius=4, fill=C_SUMI)
    nw = text_w(draw, num_text, f_num)
    draw.text((x1 + 14 + (num_box_w - nw) // 2, cy - 2), num_text, fill=C_KIN, font=f_num)

    # 馬名
    f_name = font(FONT_MINCHO, int(30 * scale))
    name = ph.get('name', '')
    draw.text((x1 + 14 + num_box_w + 10, cy - 2), name, fill=C_SUMI, font=f_name)

    # 想定OD
    od = ph.get('expectedOdds')
    if od is not None:
        f_od = font(FONT_KAKU_W3, int(14 * scale))
        od_text = f'想定OD {od:.1f}'
        draw.text((x1 + 14 + num_box_w + 10, cy + int(30 * scale)), od_text, fill=C_MUTED, font=f_od)

    # 四神チップ (2行 x 2列 or 1行 x 4列 scale依存)
    cy += int(62 * scale)
    sg = ph.get('shijinGrades') or {}
    kinds = ['seiryu', 'suzaku', 'byakko', 'genbu']
    chip_w = (w - 40) // 4
    chip_h = int(48 * scale)
    for i, k in enumerate(kinds):
        cx1 = x1 + 16 + i * chip_w
        cx2 = cx1 + chip_w - 6
        draw_shijin_chip(draw, (cx1, cy, cx2, cy + chip_h), k, sg.get(k))

    cy += chip_h + 10
    # 買い目役割
    f_buy = font(FONT_KAKU_W8, int(14 * scale))
    buy_text = f'買い目：{ph.get("buyRole", "-")}'
    tw_buy = text_w(draw, buy_text, f_buy)
    draw.rectangle([(x1 + 16, cy), (x2 - 16, cy + int(28 * scale))], fill=(248, 240, 216))
    draw.text((x1 + 16 + 10, cy + 4), buy_text, fill=C_KIN_D, font=f_buy)


def draw_buy_box(draw, xy, fb):
    """買い目ボックス"""
    x1, y1, x2, y2 = xy
    draw_rounded_rect(draw, (x1, y1, x2, y2), radius=10, fill=(255, 255, 255), outline=C_SHU, width=2)

    # 見出し
    f_h = font(FONT_MINCHO, 28)
    draw.text((x1 + 18, y1 + 10), '━ 買い目構成 ━', fill=C_SHU, font=f_h)

    f_lbl = font(FONT_KAKU_W8, 18)
    f_name = font(FONT_MINCHO, 22)
    f_amt = font(FONT_KAKU_W9, 22)

    tan = fb.get('tan') or {}
    fuku = fb.get('fuku') or {}
    wb = fb.get('wide4box') or {}

    def fmt_num(n):
        return f'({n})' if n is not None else ''

    cy = y1 + 58
    # 単勝
    draw.text((x1 + 24, cy), '天の道 ／ 単勝', fill=C_KIN_D, font=f_lbl)
    t = f'{fmt_num(tan.get("num"))}  {tan.get("name", "")}'.strip()
    draw.text((x1 + 200, cy), t, fill=C_SUMI, font=f_name)
    amt = f'¥{tan.get("amount", 0)}'
    draw.text((x2 - 24 - text_w(draw, amt, f_amt), cy), amt, fill=C_KIN_D, font=f_amt)

    cy += 40
    # 複勝
    draw.text((x1 + 24, cy), '地の道 ／ 複勝', fill=C_MIDORI, font=f_lbl)
    f = f'{fmt_num(fuku.get("num"))}  {fuku.get("name", "")}'.strip()
    draw.text((x1 + 200, cy), f, fill=C_SUMI, font=f_name)
    amt = f'¥{fuku.get("amount", 0)}'
    draw.text((x2 - 24 - text_w(draw, amt, f_amt), cy), amt, fill=C_MIDORI, font=f_amt)

    cy += 40
    # ワイド
    draw.text((x1 + 24, cy), '人の道 ／ ワイド4頭BOX', fill=C_SHU, font=f_lbl)
    amt = f'¥{wb.get("amount", 0)} ({wb.get("comboCount", 0)}点)'
    draw.text((x2 - 24 - text_w(draw, amt, f_amt), cy), amt, fill=C_SHU, font=f_amt)

    # 6通りコンボ
    cy += 36
    combos = wb.get('combos') or []
    f_c = font(FONT_KAKU_W3, 16)
    def combo_str(c):
        a, b = c.get('pair', [None, None])
        if a is not None and b is not None:
            return f'{a}-{b}'
        # 馬番未確定の場合は馬名を省略表示
        na, nb = (c.get('names') or ['', ''])[:2]
        def short(n): return (n or '')[:3]
        return f'{short(na)}-{short(nb)}'
    combo_text = '／ '.join(combo_str(c) for c in combos[:6])
    # コンボ文字列が長すぎる場合は折り返す
    lines = wrap_text(draw, combo_text, f_c, x2 - x1 - 40)
    for ln in lines[:2]:
        draw.text((x1 + 24, cy), ln, fill=C_MUTED, font=f_c)
        cy += 22


def draw_footer(draw, W, H, y_pos=None):
    """フッター: URL + キャッチ"""
    if y_pos is None:
        y_pos = H - 60
    f = font(FONT_KAKU_W3, 16)
    url = 'bakenshiug.github.io/ug-keiba'
    tag = '— AI×競馬 UG神社 —'
    draw.text((60, y_pos), tag, fill=C_KIN_D, font=f)
    draw.text((W - 60 - text_w(draw, url, f), y_pos), url, fill=C_MUTED, font=f)


def gen_twitter(label, rn, race_name, race_meta, date_label):
    """Twitter用 1080x1080 正方形"""
    W, H = 1080, 1080
    img = Image.new('RGB', (W, H), C_PAPER)
    draw = ImageDraw.Draw(img)

    data, fb, pres = load_presentation(rn)
    horses = pres.get('horses') or []

    # 背景：薄い格子
    for i in range(0, H, 40):
        draw.line([(0, i), (W, i)], fill=(238, 232, 213), width=1)

    # ヘッダー
    y = draw_header(draw, W, H, race_name, race_meta, date_label,
                    fb.get('readiness', ''), fb.get('totalSpend', 0), y_start=28)

    # 4頭カード 2x2
    card_margin = 32
    gap = 16
    card_w = (W - 2 * card_margin - gap) // 2
    card_h = 220
    top = y + 16
    for i, ph in enumerate(horses[:4]):
        row = i // 2
        col = i % 2
        x1 = card_margin + col * (card_w + gap)
        y1 = top + row * (card_h + gap)
        draw_horse_card(draw, (x1, y1, x1 + card_w, y1 + card_h), ph, scale=0.85)

    # 買い目ボックス
    by = top + 2 * (card_h + gap) + 8
    draw_buy_box(draw, (card_margin, by, W - card_margin, by + 210), fb)

    # フッター
    draw_footer(draw, W, H, y_pos=H - 56)

    out = OUT_DIR / f'{label}-twitter.png'
    img.save(out, 'PNG', optimize=True)
    print(f'  [twitter] {out}')


def draw_horse_card_tall(draw, xy, ph):
    """TikTok用 長尺カード — コメント抜粋と推し理由を含む"""
    x1, y1, x2, y2 = xy
    w = x2 - x1
    h = y2 - y1

    role = role_meta(ph.get('roleTag'))
    accent = role['accent']

    # 枠
    draw_rounded_rect(draw, (x1, y1, x2, y2), radius=14, fill=(255, 255, 255), outline=accent, width=4)

    # 役割帯
    band_h = 56
    draw.rectangle([(x1 + 4, y1 + 4), (x2 - 4, y1 + band_h)], fill=accent)

    # 役割ラベル
    f_role = font(FONT_MINCHO, 30)
    role_text = f'【{role["label"]}】'
    draw.text((x1 + 16, y1 + 12), role_text, fill=(255, 248, 232), font=f_role)

    # 人気/穴バッジ
    is_hole = ph.get('popularity') == 'hole'
    pop_text = '[穴]' if is_hole else '[人気]'
    f_pop = font(FONT_KAKU_W8, 22)
    pop_tw = text_w(draw, pop_text, f_pop)
    px = x1 + 16 + text_w(draw, role_text, f_role) + 14
    bg_col = (255, 229, 161) if is_hole else (212, 240, 200)
    draw.rectangle([(px - 6, y1 + 14), (px + pop_tw + 6, y1 + 46)], fill=bg_col)
    draw.text((px, y1 + 16), pop_text, fill=C_SUMI, font=f_pop)

    # スコア 右詰め
    score = ph.get('score')
    if score is not None:
        f_score = font(FONT_KAKU_W9, 30)
        sc_text = f'{score:.1f}pt'
        sw = text_w(draw, sc_text, f_score)
        draw.text((x2 - 16 - sw, y1 + 13), sc_text, fill=(255, 248, 232), font=f_score)

    # コンテンツ領域
    cy = y1 + band_h + 14

    # 馬番 + 馬名
    num = ph.get('num')
    num_text = str(num) if num is not None else '?'
    f_num = font(FONT_KAKU_W9, 42)
    num_box_w = 74
    num_box_h = 58
    draw_rounded_rect(draw, (x1 + 18, cy, x1 + 18 + num_box_w, cy + num_box_h), radius=6, fill=C_SUMI)
    nw = text_w(draw, num_text, f_num)
    draw.text((x1 + 18 + (num_box_w - nw) // 2, cy - 2), num_text, fill=C_KIN, font=f_num)

    f_name = font(FONT_MINCHO, 40)
    name = ph.get('name', '')
    draw.text((x1 + 18 + num_box_w + 14, cy - 2), name, fill=C_SUMI, font=f_name)

    od = ph.get('expectedOdds')
    if od is not None:
        f_od = font(FONT_KAKU_W3, 18)
        od_text = f'想定OD {od:.1f}倍'
        draw.text((x1 + 18 + num_box_w + 14, cy + 46), od_text, fill=C_MUTED, font=f_od)

    # 四神チップ
    cy += 84
    sg = ph.get('shijinGrades') or {}
    kinds = ['seiryu', 'suzaku', 'byakko', 'genbu']
    chip_w = (w - 48) // 4
    chip_h = 58
    for i, k in enumerate(kinds):
        cx1 = x1 + 20 + i * chip_w
        cx2 = cx1 + chip_w - 8
        # 拡大版chip描画
        meta = SHIJIN[k]
        color = meta['color']
        draw_rounded_rect(draw, (cx1, cy, cx2, cy + chip_h), radius=6, fill=(255, 255, 255), outline=color, width=2)
        f_jp = font(FONT_MINCHO, 24)
        draw.text((cx1 + 10, cy + 6), meta['jp'], fill=color, font=f_jp)
        f_factor = font(FONT_KAKU_W3, 12)
        draw.text((cx1 + 10, cy + 34), meta['factor'], fill=C_MUTED, font=f_factor)
        grade = sg.get(k)
        g_color = GRADE_COLOR.get(grade, (180, 170, 150))
        g_text = grade if grade else '—'
        f_g = font(FONT_KAKU_W9, 26)
        bg_w = 40
        bg_x1 = cx2 - bg_w - 10
        bg_y1 = cy + 10
        draw_rounded_rect(draw, (bg_x1, bg_y1, bg_x1 + bg_w, bg_y1 + 40), radius=4, fill=g_color)
        tw = text_w(draw, g_text, f_g)
        draw.text((bg_x1 + (bg_w - tw) // 2, bg_y1 + 2), g_text, fill=(255, 255, 255), font=f_g)

    # 見解コメント（2行で抜粋）
    cy += chip_h + 14
    comment = ph.get('comment', '')
    f_cm = font(FONT_MINCHO, 18)
    # 左側に縦ライン
    draw.rectangle([(x1 + 20, cy), (x1 + 24, cy + 58)], fill=accent)
    lines = wrap_text(draw, comment, f_cm, w - 60)
    for i, ln in enumerate(lines[:2]):
        # 最終行は末尾に「…」
        if i == 1 and len(lines) > 2:
            ln = ln[:-2] + '…'
        draw.text((x1 + 32, cy + 4 + i * 26), ln, fill=C_SUMI, font=f_cm)

    # 買い目役割
    cy += 72
    f_buy = font(FONT_KAKU_W8, 18)
    buy_text = f'買い目：{ph.get("buyRole", "-")}'
    draw.rectangle([(x1 + 20, cy), (x2 - 20, cy + 36)], fill=(248, 240, 216))
    draw.text((x1 + 32, cy + 6), buy_text, fill=C_KIN_D, font=f_buy)


def gen_tiktok(label, rn, race_name, race_meta, date_label):
    """TikTok用 1080x1920 縦長 9:16"""
    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), C_PAPER)
    draw = ImageDraw.Draw(img)

    data, fb, pres = load_presentation(rn)
    horses = pres.get('horses') or []

    # 背景：薄い格子
    for i in range(0, H, 40):
        draw.line([(0, i), (W, i)], fill=(238, 232, 213), width=1)

    # ヘッダー
    y = draw_header(draw, W, H, race_name, race_meta, date_label,
                    fb.get('readiness', ''), fb.get('totalSpend', 0), y_start=40)

    # 4頭カード 縦積み (長尺版)
    card_margin = 40
    card_w = W - 2 * card_margin
    card_h = 320
    gap = 14
    for i, ph in enumerate(horses[:4]):
        x1 = card_margin
        y1 = y + 14 + i * (card_h + gap)
        draw_horse_card_tall(draw, (x1, y1, x1 + card_w, y1 + card_h), ph)

    # 買い目ボックス
    by = y + 14 + 4 * (card_h + gap) + 10
    draw_buy_box(draw, (card_margin, by, W - card_margin, by + 270), fb)

    # フッター
    draw_footer(draw, W, H, y_pos=H - 80)

    out = OUT_DIR / f'{label}-tiktok.png'
    img.save(out, 'PNG', optimize=True)
    print(f'  [tiktok]  {out}')


def gen_youtube(label, rn, race_name, race_meta, date_label):
    """YouTube配信サムネ用 1920x1080 横長 (ギーニョ大神メインビジュアル)"""
    W, H = 1920, 1080
    img = Image.new('RGB', (W, H), C_PAPER)
    draw = ImageDraw.Draw(img)

    data, fb, pres = load_presentation(rn)
    horses = pres.get('horses') or []

    # 上部: 朱帯 (細め)
    band_h = 90
    draw.rectangle([(0, 0), (W, band_h)], fill=C_SHU)
    # 金の二重線
    draw.line([(60, band_h + 6), (W - 60, band_h + 6)], fill=C_KIN, width=2)
    draw.line([(60, band_h + 12), (W - 60, band_h + 12)], fill=C_KIN, width=1)

    # FINAL ORACLE / 四神の御神託
    f_eng = font(FONT_KAKU_W3, 26)
    s = 'FINAL  ORACLE   ／   四神の御神託'
    draw.text((W // 2 - text_w(draw, s, f_eng) // 2, 30), s, fill=C_KIN, font=f_eng)

    # 下部: 薄金帯 (ベース)
    footer_h = 70
    draw.rectangle([(0, H - footer_h), (W, H)], fill=(236, 224, 192))
    # URL + キャッチ
    f_ft = font(FONT_KAKU_W3, 22)
    url = 'bakenshiug.github.io/ug-keiba'
    tag = '— AI×競馬 UG神社 —'
    draw.text((60, H - 48), tag, fill=C_KIN_D, font=f_ft)
    draw.text((W - 60 - text_w(draw, url, f_ft), H - 48), url, fill=C_MUTED, font=f_ft)

    # 左: ギーニョ大神 御本尊 (後光付き)
    if GIINYO_IMG:
        img_h = 820
        img_w = int(img_h * 0.743)
        img_x = 80
        img_y = (H - img_h) // 2

        # 後光 (金の薄い円) - 2段
        halo_r1 = img_w // 2 + 40
        halo_r2 = img_w // 2 + 20
        halo_cx = img_x + img_w // 2
        halo_cy = img_y + img_h // 2

        # 後光外側 (極薄)
        draw.ellipse([(halo_cx - halo_r1, halo_cy - halo_r1),
                      (halo_cx + halo_r1, halo_cy + halo_r1)],
                     fill=(249, 233, 183), outline=C_KIN, width=2)
        draw.ellipse([(halo_cx - halo_r2, halo_cy - halo_r2),
                      (halo_cx + halo_r2, halo_cy + halo_r2)],
                     outline=C_KIN_D, width=1)

        # 御本尊画像
        resized = GIINYO_IMG.resize((img_w, img_h), Image.LANCZOS)
        img.paste(resized, (img_x, img_y), resized)

        # 御神名 (画像下) — ギーニョ大神の正式御神名
        f_tagline = font(FONT_MINCHO, 38)
        t = 'ギーニョ・思金神'
        tw_ = text_w(draw, t, f_tagline)
        draw.text((img_x + (img_w - tw_) // 2, img_y + img_h + 8), t, fill=C_SHU_D, font=f_tagline)
        f_eng_tag = font(FONT_KAKU_W3, 15)
        t2 = 'GIINYO OMOIKANE-NO-KAMI'
        tw2 = text_w(draw, t2, f_eng_tag)
        draw.text((img_x + (img_w - tw2) // 2, img_y + img_h + 56), t2, fill=C_KIN_D, font=f_eng_tag)

    # 右: レース情報 (でかでか) - 角ゴシック太め統一
    right_x = 820
    right_w = W - right_x - 80

    # 御神託降臨 (W8)
    f_title = font(FONT_KAKU_W8, 72)
    t = '御神託降臨'
    draw.text((right_x, 170), t, fill=C_SHU_D, font=f_title)
    # 金アンダーライン
    tw_ = text_w(draw, t, f_title)
    draw.line([(right_x, 262), (right_x + tw_, 262)], fill=C_KIN, width=3)

    # レース名 (超ドデカ・W9)
    f_race = font(FONT_KAKU_W9, 150)
    draw.text((right_x, 290), race_name, fill=C_SUMI, font=f_race)

    # メタ情報
    f_meta = font(FONT_KAKU_W3, 34)
    draw.text((right_x, 490), race_meta, fill=C_SUMI, font=f_meta)
    f_date = font(FONT_KAKU_W8, 44)
    draw.text((right_x, 540), date_label, fill=C_SHU, font=f_date)

    # 金の分割線
    draw.line([(right_x, 620), (right_x + 500, 620)], fill=C_KIN, width=2)

    # 本命馬 or キャッチコピー
    f_main_label = font(FONT_KAKU_W3, 22)
    draw.text((right_x, 640), '今宵、神託を授ける一頭', fill=C_MUTED, font=f_main_label)

    # 本命馬名 (W8 太)
    main_horse = next((h for h in horses if h.get('roleTag') == 'main'), None)
    if main_horse:
        f_horse = font(FONT_KAKU_W8, 60)
        horse_name = main_horse.get('name', '')
        draw.text((right_x, 680), f'本命： {horse_name}', fill=C_SHU_D, font=f_horse)
        # スコア & OD
        f_stat = font(FONT_KAKU_W3, 26)
        score = main_horse.get('score')
        od = main_horse.get('expectedOdds')
        stat = f'採点 {score:.1f}pt　　想定OD {od:.1f}倍' if score is not None and od is not None else ''
        if stat:
            draw.text((right_x, 760), stat, fill=C_MUTED, font=f_stat)

    # ── ニック Vtuber アバター (案内人) + CTA 横並び ──
    cta_y_center = 880
    nick_r = 68
    nick_cx = right_x + nick_r + 8
    nick_cy = cta_y_center
    if NICK_IMG:
        paste_circular(img, NICK_IMG, nick_cx, nick_cy, nick_r, halo=True)
        # ラベル「案内人 / ニック」 (アバター直下)
        f_role = font(FONT_KAKU_W3, 18)
        role_t = '案内人'
        rw = text_w(draw, role_t, f_role)
        draw.text((nick_cx - rw // 2, nick_cy + nick_r + 28), role_t, fill=C_MUTED, font=f_role)
        f_role_name = font(FONT_KAKU_W8, 22)
        name_t = 'ニック'
        nw = text_w(draw, name_t, f_role_name)
        draw.text((nick_cx - nw // 2, nick_cy + nick_r + 54), name_t, fill=C_SHU_D, font=f_role_name)

    # CTA テキスト (ニックの右側) - ▶ は自前描画で文字化け回避
    cta_x = nick_cx + nick_r + 32 if NICK_IMG else right_x
    f_cta = font(FONT_KAKU_W9, 32)
    # 朱の三角矢印を描画 (高さ28, 幅24)
    tri_y = cta_y_center - 22
    draw.polygon([(cta_x, tri_y), (cta_x + 24, tri_y + 14), (cta_x, tri_y + 28)], fill=C_SHU)
    cta_line1 = '全12ページの御神託書'
    draw.text((cta_x + 36, cta_y_center - 34), cta_line1, fill=C_SHU, font=f_cta)
    f_cta_sub = font(FONT_KAKU_W3, 22)
    cta_line2 = '本編はこちら（PDF／YouTube配信）'
    draw.text((cta_x + 36, cta_y_center + 8), cta_line2, fill=C_KIN_D, font=f_cta_sub)

    out = OUT_DIR / f'{label}-youtube.png'
    img.save(out, 'PNG', optimize=True)
    print(f'  [youtube] {out}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='特定レースのみ (2026-04-25-aobasho など)')
    ap.add_argument('--skip-twitter', action='store_true')
    ap.add_argument('--skip-tiktok', action='store_true')
    ap.add_argument('--skip-youtube', action='store_true')
    args = ap.parse_args()

    targets = [r for r in RACE_MAP if not args.only or r[0] == args.only]

    print('=== SNS シェア画像生成 ===')
    for label, rn, race_name, race_meta, date_label in targets:
        print(f'▶ {label}  ({race_name})')
        try:
            if not args.skip_twitter:
                gen_twitter(label, rn, race_name, race_meta, date_label)
            if not args.skip_tiktok:
                gen_tiktok(label, rn, race_name, race_meta, date_label)
            if not args.skip_youtube:
                gen_youtube(label, rn, race_name, race_meta, date_label)
        except Exception as e:
            import traceback
            print(f'  [ERROR] {e}')
            traceback.print_exc()


if __name__ == '__main__':
    main()
