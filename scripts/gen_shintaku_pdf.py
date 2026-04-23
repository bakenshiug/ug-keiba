#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四神の御神託 PDFレポート生成スクリプト (YouTube横向き版)
========================================================
使用: python3 scripts/gen_shintaku_pdf.py [--only <race-label>]

入力:
  docs/data/race-notes/{race}.json の finalBets.presentation

出力:
  docs/img/pdf/{race}-shintaku.pdf (A4横)

構成 (A4横 297×210mm, 全7ページ):
  1枚目: 表紙 + 4頭サマリ(1×4横並び) + 買い目
  2-5枚目: 各馬詳細 (四神レーダーチャート + 見解 + 推し理由/リスク)
  6枚目: 全馬スコアボード
  7枚目: 落選の儀

デザイン:
  本格95% + ちゃっかり5% のギーニョ節でフッター/見出しに小ネタを散りばめる。
"""
import json
import math
import random
import argparse
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

BASE = Path('/Users/buntawakase/Desktop/ug-keiba')
OUT_DIR = BASE / 'docs/img/pdf'
OUT_DIR.mkdir(parents=True, exist_ok=True)

RACE_MAP = [
    ('2026-04-25-aobasho',  '2026-04-25-tokyo-11r', '青葉賞',    'G2 東京芝2400m',  '2026/04/25 土'),
    ('2026-04-26-floras',   '2026-04-26-tokyo-11r', 'フローラS', 'G2 東京芝2000m',  '2026/04/26 日'),
    ('2026-04-26-milers-c', '2026-04-26-kyoto-11r', 'マイラーズC','G2 京都芝1600m', '2026/04/26 日'),
]

# 日本語フォント登録（reportlab 同梱 CID フォント）
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
F_MIN = 'HeiseiMin-W3'
F_KAK = 'HeiseiKakuGo-W5'

# 神社風カラー
C_PAPER   = HexColor('#F4EEDD')
C_SUMI    = HexColor('#1A1A1A')
C_SHU     = HexColor('#9B2D30')
C_SHU_D   = HexColor('#7A1E1E')
C_KIN     = HexColor('#C9A961')
C_KIN_D   = HexColor('#8B7530')
C_MIDORI  = HexColor('#1F4D2E')
C_MUTED   = HexColor('#7F7564')
C_WHITE   = HexColor('#FFFFFF')
C_FAINT   = HexColor('#E7DFC8')

GRADE_COLOR = {
    'S': HexColor('#C49A3D'),
    'A': HexColor('#2F5C3B'),
    'B': HexColor('#2D4A6E'),
    'C': HexColor('#A06654'),
    'D': HexColor('#3E3A36'),
}

# レーダー値 (S=5...D=1, 不明=0)
GRADE_VALUE = {'S': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}

SHIJIN = {
    'seiryu':  {'jp': '青龍', 'factor': '言霊',  'color': C_MIDORI,          'dir_deg': 0  },  # 東=右
    'suzaku':  {'jp': '朱雀', 'factor': '神眼',  'color': C_SHU,             'dir_deg': 270},  # 南=下
    'byakko':  {'jp': '白虎', 'factor': 'ラップ', 'color': C_KIN_D,           'dir_deg': 180},  # 西=左
    'genbu':   {'jp': '玄武', 'factor': '外厩',  'color': HexColor('#1E1E1E'),'dir_deg': 90 },  # 北=上
}

ROLE_META = {
    'main':    {'label': '本命',   'accent': C_SHU,              'accent_light': HexColor('#E8D3D4')},
    'counter': {'label': '対抗',   'accent': C_KIN_D,            'accent_light': HexColor('#EEE4C9')},
    'support': {'label': '押さえ', 'accent': C_MIDORI,           'accent_light': HexColor('#D4E1D9')},
    'hole':    {'label': '穴',     'accent': HexColor('#6E4A1F'),'accent_light': HexColor('#EFE0CA')},
}

# ─── ギーニョ節ユーモア (本格95%+ちゃっかり5%) ───
HUMOR_SUBTITLES = [
    '御神託は希望を運びます。でも着順は、馬が決める。',
    '拝んで当てる、信じて笑う、外れて来週。',
    '宮司も回収率を気にしているらしい。',
    '馬券は引いて握る、ご縁は結んで放す。',
    '信じる者は報われる。たぶん。ときどき。',
]
HUMOR_DROPPED_NOTES = {
    'default':   '今回は見送り。次走、また。',
    'ana_miss':  '穴だけど、穴の形をしていない。',
    'low_rel':   '言霊が弱め。次で化ける可能性は残す。',
    'low_gk':    '外厩データが薄い。在厩仕上げ待ち。',
    'low_lap':   'ラップ脚質が噛み合わない。',
    'overrated': '人気先行の気配、お見送り。',
    'mental':    '気配の揺らぎを感じる。今回はパス。',
}
HUMOR_FOOTERS = [
    '※御神託は結果を保証しません。信じる者に、次走あり。',
    '※本書は祈祷書であって必勝法ではありません。',
    '※外れたら、また境内でお会いしましょう。',
]

RNG = random.Random(42)  # 再現性のため固定seed(フッター用)
_RACE_COUNTER = {'i': 0}  # サブタイトル巡回用


def _sanitize_deep(obj):
    """ネストした dict/list を再帰的に sanitize (文字列のみ対象)"""
    if isinstance(obj, str):
        return sanitize(obj)
    if isinstance(obj, list):
        return [_sanitize_deep(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sanitize_deep(v) for k, v in obj.items()}
    return obj


def load_pres(rn):
    p = BASE / 'docs/data/race-notes' / f'{rn}.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    fb = data.get('finalBets') or {}
    pres = fb.get('presentation')
    if not pres:
        raise RuntimeError(f'{rn}: presentation 未生成')
    # 絵文字を CID フォント対応表記に置換(PDF専用)
    fb = _sanitize_deep(fb)
    pres = _sanitize_deep(pres)
    return data, fb, pres


# CID フォントが対応していない絵文字をテキストラベルに置換する
PDF_EMOJI_MAP = {
    '\U0001F409': '[青龍]',  # 🐉
    '\U0001F426': '[朱雀]',  # 🐦
    '\U0001F405': '[白虎]',  # 🐅
    '\U0001F422': '[玄武]',  # 🐢
    '\u26e9':     '[社]',    # ⛩
    '\u2600':     '',        # ☀
    '\U0001F33F': '',        # 🌿
    '\U0001F91D': '',        # 🤝
    '\U0001F525': '',        # 🔥
    '\u2b50':     '',        # ⭐
}

def sanitize(text):
    """CID フォントで描画できない絵文字を置換"""
    if not text:
        return ''
    for k, v in PDF_EMOJI_MAP.items():
        text = text.replace(k, v)
    return text


def sw(c, text, font, size):
    return c.stringWidth(sanitize(text), font, size)


def wrap_jp(c, text, font, size, max_w):
    text = sanitize(text)
    lines = []
    line = ''
    for ch in text:
        if ch == '\n':
            lines.append(line); line = ''; continue
        test = line + ch
        if sw(c, test, font, size) > max_w:
            lines.append(line); line = ch
        else:
            line = test
    if line:
        lines.append(line)
    return lines


# ══════════════════════════════════════════════════════════════════
# 四神レーダーチャート（四角形マトリックス）
# ══════════════════════════════════════════════════════════════════
def draw_radar(c, cx, cy, r, grades, accent):
    """
    四神の4角形レーダーチャート
      cx,cy: 中心座標(points)
      r:     最大値(グレードS)の半径(points)
      grades: {'seiryu':'S','suzaku':'A',...}
      accent: 本命色
    北=玄武/外厩, 東=青龍/言霊, 南=朱雀/神眼, 西=白虎/ラップ の順で4点を結ぶ
    """
    order = ['genbu', 'seiryu', 'suzaku', 'byakko']
    angles_deg = [90, 0, 270, 180]  # 上・右・下・左
    angles = [math.radians(a) for a in angles_deg]

    # 薄い背景(五角形風のガイド)
    levels = [1, 2, 3, 4, 5]
    for lv in levels:
        rr = r * lv / 5
        c.setStrokeColor(HexColor('#D8CFB7'))
        c.setLineWidth(0.3)
        c.setDash(1, 1)
        pts = []
        for ang in angles:
            px = cx + rr * math.cos(ang)
            py = cy + rr * math.sin(ang)
            pts.append((px, py))
        p = c.beginPath()
        p.moveTo(*pts[0])
        for px, py in pts[1:]:
            p.lineTo(px, py)
        p.close()
        c.drawPath(p, stroke=1, fill=0)
    c.setDash()

    # 軸線
    c.setStrokeColor(HexColor('#B8AE92'))
    c.setLineWidth(0.4)
    for ang in angles:
        px = cx + r * math.cos(ang)
        py = cy + r * math.sin(ang)
        c.line(cx, cy, px, py)

    # 実データ多角形
    data_pts = []
    for key, ang in zip(order, angles):
        grade = grades.get(key)
        val = GRADE_VALUE.get(grade, 0)
        rr = r * val / 5
        data_pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))

    # 塗り
    c.setFillColor(accent)
    c.setFillAlpha(0.22)
    c.setStrokeColor(accent)
    c.setLineWidth(1.4)
    p = c.beginPath()
    p.moveTo(*data_pts[0])
    for px, py in data_pts[1:]:
        p.lineTo(px, py)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1)

    # 頂点マーカー
    for (px, py), key in zip(data_pts, order):
        grade = grades.get(key)
        if grade:
            g_color = GRADE_COLOR.get(grade, C_MUTED)
            c.setFillColor(g_color)
            c.circle(px, py, 1.8*mm, stroke=0, fill=1)
            c.setFillColor(C_WHITE)
            c.setFont(F_KAK, 6.5)
            tw = sw(c, grade, F_KAK, 6.5)
            c.drawString(px - tw/2, py - 1.1*mm, grade)

    # 軸ラベル (四神名 + ファクター)
    label_r = r + 6*mm
    for key, ang_deg, ang in zip(order, angles_deg, angles):
        meta = SHIJIN[key]
        lx = cx + label_r * math.cos(ang)
        ly = cy + label_r * math.sin(ang)
        c.setFillColor(meta['color'])
        c.setFont(F_MIN, 10)
        t = meta['jp']
        tw = sw(c, t, F_MIN, 10)
        # 軸方向に応じて位置微調整
        if ang_deg == 90:    # 上
            c.drawString(lx - tw/2, ly + 0.5*mm, t)
            c.setFillColor(C_MUTED); c.setFont(F_KAK, 6.5)
            c.drawString(lx - sw(c, meta['factor'], F_KAK, 6.5)/2, ly - 2.5*mm, meta['factor'])
        elif ang_deg == 270: # 下
            c.drawString(lx - tw/2, ly - 3*mm, t)
            c.setFillColor(C_MUTED); c.setFont(F_KAK, 6.5)
            c.drawString(lx - sw(c, meta['factor'], F_KAK, 6.5)/2, ly - 5.5*mm, meta['factor'])
        elif ang_deg == 0:   # 右
            c.drawString(lx + 1*mm, ly - 1*mm, t)
            c.setFillColor(C_MUTED); c.setFont(F_KAK, 6.5)
            c.drawString(lx + 1*mm, ly - 4*mm, meta['factor'])
        else:                # 左
            fw = sw(c, meta['factor'], F_KAK, 6.5)
            c.drawString(lx - tw - 1*mm, ly - 1*mm, t)
            c.setFillColor(C_MUTED); c.setFont(F_KAK, 6.5)
            c.drawString(lx - fw - 1*mm, ly - 4*mm, meta['factor'])


# ══════════════════════════════════════════════════════════════════
# 四神チップ (軽量版 - サマリ/スコアボード用)
# ══════════════════════════════════════════════════════════════════
def draw_shijin_chip(c, x, y, w, h, kind, grade):
    meta = SHIJIN[kind]
    color = meta['color']
    c.setStrokeColor(color)
    c.setLineWidth(1)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)
    c.setFillColor(color)
    c.setFont(F_MIN, 10)
    c.drawString(x + 2*mm, y + h - 5*mm, meta['jp'])
    c.setFillColor(C_MUTED)
    c.setFont(F_KAK, 5.5)
    c.drawString(x + 2*mm, y + 1.8*mm, meta['factor'])
    g_color = GRADE_COLOR.get(grade, HexColor('#B4AA96'))
    g_text = grade if grade else '—'
    bg_w = 7*mm; bg_h = 5*mm
    bg_x = x + w - bg_w - 1.5*mm
    bg_y = y + (h - bg_h) / 2
    c.setFillColor(g_color)
    c.roundRect(bg_x, bg_y, bg_w, bg_h, 1*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont(F_KAK, 10)
    tw = sw(c, g_text, F_KAK, 10)
    c.drawString(bg_x + (bg_w - tw) / 2, bg_y + 1.2*mm, g_text)


# ══════════════════════════════════════════════════════════════════
# ヘッダ・フッタ
# ══════════════════════════════════════════════════════════════════
def draw_cover_header(c, W, H, race_name, race_meta, date_label, subtitle):
    band_h = 34*mm
    c.setFillColor(C_SHU)
    c.rect(0, H - band_h, W, band_h, stroke=0, fill=1)

    c.setStrokeColor(C_KIN)
    c.setLineWidth(0.6)
    c.line(15*mm, H - band_h - 2*mm, W - 15*mm, H - band_h - 2*mm)
    c.line(15*mm, H - band_h - 4*mm, W - 15*mm, H - band_h - 4*mm)

    c.setFillColor(C_KIN)
    c.setFont(F_KAK, 8)
    t = 'FINAL ORACLE  ／  四神の御神託'
    tw = sw(c, t, F_KAK, 8)
    c.drawString((W - tw) / 2, H - 8*mm, t)

    c.setFillColor(C_WHITE)
    c.setFont(F_MIN, 22)
    t = '御神託降臨'
    tw = sw(c, t, F_MIN, 22)
    c.drawString((W - tw) / 2, H - 18*mm, t)

    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont(F_MIN, 16)
    t = f'{race_name}'
    tw = sw(c, t, F_MIN, 16)
    c.drawString((W - tw) / 2, H - 26*mm, t)

    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont(F_KAK, 9)
    meta_text = f'{race_meta}  ／  {date_label}'
    tw = sw(c, meta_text, F_KAK, 9)
    c.drawString((W - tw) / 2, H - 31*mm, meta_text)

    # 小さなサブタイトル(ユーモア)
    c.setFillColor(HexColor('#C9A961'))
    c.setFont(F_MIN, 7.5)
    tw = sw(c, subtitle, F_MIN, 7.5)
    c.drawString((W - tw) / 2, H - band_h - 8*mm, subtitle)

    return H - band_h - 14*mm


def draw_detail_header(c, W, H, ph, idx, race_name):
    """各馬詳細ページ上部"""
    role = ROLE_META.get(ph.get('roleTag'), ROLE_META['support'])
    accent = role['accent']

    band_h = 22*mm
    c.setFillColor(accent)
    c.rect(0, H - band_h, W, band_h, stroke=0, fill=1)

    # 役割ラベル
    c.setFillColor(C_WHITE)
    c.setFont(F_MIN, 22)
    c.drawString(15*mm, H - 14*mm, f'【{role["label"]}】  第{idx+1}候補')

    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont(F_KAK, 9)
    od = ph.get('expectedOdds')
    od_txt = f'{od:.1f}倍' if od is not None else '—'
    c.drawString(15*mm, H - 19*mm,
                 f'pick {ph.get("pickOrder","-")}/4  ／  scoreboard rank{ph.get("rank","-")}  ／  想定OD {od_txt}')

    # レース名(右上)
    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont(F_KAK, 9)
    t = f'{race_name}'
    tw = sw(c, t, F_KAK, 9)
    c.drawString(W - 15*mm - tw, H - 19*mm, t)

    # スコア右
    score = ph.get('score')
    if score is not None:
        c.setFillColor(C_KIN)
        c.setFont(F_KAK, 20)
        t = f'{score:.1f}pt'
        tw = sw(c, t, F_KAK, 20)
        c.drawString(W - tw - 15*mm, H - 12*mm, t)

    return H - band_h


def draw_footer(c, W, race_name, page_idx, page_total, footer_quip, url):
    c.setFillColor(C_MUTED)
    c.setFont(F_KAK, 7)
    c.drawString(15*mm, 8*mm, f'{race_name}  ({page_idx}/{page_total})')
    # 中央ユーモア引用
    c.setFillColor(HexColor('#A39680'))
    c.setFont(F_MIN, 7)
    tw = sw(c, footer_quip, F_MIN, 7)
    c.drawString((W - tw) / 2, 8*mm, footer_quip)
    # URL
    c.setFillColor(C_KIN_D)
    c.setFont(F_KAK, 7)
    tw = sw(c, url, F_KAK, 7)
    c.drawString(W - 15*mm - tw, 8*mm, url)


# ══════════════════════════════════════════════════════════════════
# 表紙: 4頭サマリ(横並び)
# ══════════════════════════════════════════════════════════════════
def draw_summary_card(c, x, y, w, h, ph):
    role = ROLE_META.get(ph.get('roleTag'), ROLE_META['support'])
    accent = role['accent']
    accent_light = role['accent_light']

    c.setStrokeColor(accent)
    c.setLineWidth(1.2)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)

    # 上部役割帯
    band_h = 8*mm
    c.setFillColor(accent)
    c.rect(x + 0.3*mm, y + h - band_h - 0.3*mm, w - 0.6*mm, band_h, stroke=0, fill=1)

    c.setFillColor(C_WHITE)
    c.setFont(F_MIN, 11)
    c.drawString(x + 3*mm, y + h - 6*mm, f'【{role["label"]}】')

    is_hole = ph.get('popularity') == 'hole'
    pop_text = '[穴]' if is_hole else '[人気]'
    c.setFillColor(HexColor('#FFE5A1') if is_hole else HexColor('#D4F0C8'))
    pop_x = x + 20*mm
    c.roundRect(pop_x, y + h - 7*mm, 10*mm, 5*mm, 0.5*mm, stroke=0, fill=1)
    c.setFillColor(C_SUMI)
    c.setFont(F_KAK, 7)
    c.drawString(pop_x + 1.3*mm, y + h - 5.4*mm, pop_text)

    score = ph.get('score')
    if score is not None:
        c.setFillColor(HexColor('#F5EDD6'))
        c.setFont(F_KAK, 12)
        t = f'{score:.1f}pt'
        tw = sw(c, t, F_KAK, 12)
        c.drawString(x + w - tw - 3*mm, y + h - 6*mm, t)

    # 馬番 + 馬名
    cy = y + h - band_h - 10*mm
    num = ph.get('num')
    num_text = str(num) if num is not None else '?'
    c.setFillColor(C_SUMI)
    c.roundRect(x + 3*mm, cy - 2*mm, 11*mm, 9*mm, 1*mm, stroke=0, fill=1)
    c.setFillColor(C_KIN)
    c.setFont(F_KAK, 14)
    tw = sw(c, num_text, F_KAK, 14)
    c.drawString(x + 3*mm + (11*mm - tw)/2, cy + 0.5*mm, num_text)

    c.setFillColor(C_SUMI)
    c.setFont(F_MIN, 13)
    name = ph.get('name', '')
    max_name_w = w - 20*mm
    # 長い馬名はサイズ縮め
    size = 13
    while sw(c, name, F_MIN, size) > max_name_w and size > 8:
        size -= 0.5
    c.drawString(x + 17*mm, cy + 0.8*mm, name)

    od = ph.get('expectedOdds')
    if od is not None:
        c.setFillColor(C_MUTED)
        c.setFont(F_KAK, 7)
        c.drawString(x + 17*mm, cy - 2.8*mm, f'想定OD {od:.1f}')

    # ミニレーダー(カード下部に)
    rcx = x + w/2
    rcy = y + h/2 - 8*mm
    radius = min(w, h) * 0.22
    sg = ph.get('shijinGrades') or {}
    draw_radar(c, rcx, rcy, radius, sg, accent)

    # 買い目役割
    c.setFillColor(accent_light)
    c.rect(x + 0.3*mm, y + 0.3*mm, w - 0.6*mm, 6*mm, stroke=0, fill=1)
    c.setFillColor(C_SUMI)
    c.setFont(F_KAK, 7)
    buy = ph.get('buyRole', '-')
    # 長文の場合は切る
    max_buy_w = w - 6*mm
    while sw(c, f'買い目：{buy}', F_KAK, 7) > max_buy_w and len(buy) > 6:
        buy = buy[:-1]
    c.drawString(x + 3*mm, y + 2.2*mm, f'買い目：{buy}')


# ══════════════════════════════════════════════════════════════════
# 詳細ページ: 3カラム (左=レーダー+基本情報, 中=見解, 右=推し理由/リスク)
# ══════════════════════════════════════════════════════════════════
def draw_detail_page(c, W, H, ph, idx, race_name, page_idx, page_total, footer_quip, url):
    role = ROLE_META.get(ph.get('roleTag'), ROLE_META['support'])
    accent = role['accent']
    accent_light = role['accent_light']

    top_y = draw_detail_header(c, W, H, ph, idx, race_name)

    # 馬番 + 馬名 (上部ヘッダ直下)
    name_y = top_y - 18*mm
    num = ph.get('num')
    num_text = str(num) if num is not None else '?'
    c.setFillColor(C_SUMI)
    c.roundRect(15*mm, name_y - 4*mm, 20*mm, 15*mm, 1.5*mm, stroke=0, fill=1)
    c.setFillColor(C_KIN)
    c.setFont(F_KAK, 24)
    tw = sw(c, num_text, F_KAK, 24)
    c.drawString(15*mm + (20*mm - tw)/2, name_y + 0.5*mm, num_text)

    c.setFillColor(C_SUMI)
    c.setFont(F_MIN, 28)
    c.drawString(40*mm, name_y + 1.5*mm, ph.get('name', ''))

    # メタ情報
    c.setFillColor(C_MUTED)
    c.setFont(F_KAK, 9)
    meta_parts = []
    if ph.get('jockey'):  meta_parts.append(f'騎手 {ph.get("jockey")}')
    if ph.get('trainer'): meta_parts.append(f'厩舎 {ph.get("trainer")}')
    if ph.get('gaikyuLabel'): meta_parts.append(f'外厩 {ph.get("gaikyuLabel")}')
    if ph.get('sire'): meta_parts.append(f'父 {ph.get("sire")}')
    if meta_parts:
        c.drawString(40*mm, name_y - 5.5*mm, '　'.join(meta_parts))

    # ══ 3カラムエリア ══
    area_top = name_y - 14*mm
    area_bottom = 25*mm
    area_h = area_top - area_bottom

    # カラム境界 (A4横 297mm 内訳: 15 + 95 + 4 + 105 + 4 + 59 + 15 = 297)
    col_L_w = 95*mm     # 左: レーダー
    col_M_w = 105*mm    # 中: 見解
    col_R_w = W - 30*mm - col_L_w - col_M_w - 8*mm  # 右: 推し理由/リスク
    col_L_x = 15*mm
    col_M_x = col_L_x + col_L_w + 4*mm
    col_R_x = col_M_x + col_M_w + 4*mm

    # ── 左カラム: レーダーチャート ──
    c.setFillColor(C_WHITE)
    c.setStrokeColor(C_FAINT)
    c.setLineWidth(0.6)
    c.roundRect(col_L_x, area_bottom, col_L_w, area_h, 2*mm, stroke=1, fill=1)

    # 見出し
    c.setFillColor(C_SUMI)
    c.setFont(F_MIN, 11)
    c.drawString(col_L_x + 4*mm, area_top - 6*mm, '━ 四神レーダー ━')

    # レーダー
    rcx = col_L_x + col_L_w / 2
    rcy = area_bottom + area_h / 2 - 3*mm
    radius = min(col_L_w, area_h - 20*mm) * 0.35
    sg = ph.get('shijinGrades') or {}
    draw_radar(c, rcx, rcy, radius, sg, accent)

    # グレード凡例(下部)
    legend_y = area_bottom + 6*mm
    c.setFillColor(C_MUTED)
    c.setFont(F_KAK, 6.5)
    t = 'S=5, A=4, B=3, C=2, D=1 (中心=0)'
    tw = sw(c, t, F_KAK, 6.5)
    c.drawString(col_L_x + (col_L_w - tw)/2, legend_y, t)

    # ── 中央カラム: 見解 ──
    c.setFillColor(C_WHITE)
    c.setStrokeColor(C_FAINT)
    c.setLineWidth(0.6)
    c.roundRect(col_M_x, area_bottom, col_M_w, area_h, 2*mm, stroke=1, fill=1)

    c.setFillColor(accent)
    c.rect(col_M_x, area_top - 8*mm, 1.2*mm, area_h - 4*mm, stroke=0, fill=1)

    c.setFillColor(C_SUMI)
    c.setFont(F_MIN, 12)
    c.drawString(col_M_x + 5*mm, area_top - 6*mm, '━ 見解 ━')

    c.setFillColor(C_SUMI)
    c.setFont(F_MIN, 11)
    comment = ph.get('comment', '')
    lines = wrap_jp(c, comment, F_MIN, 11, col_M_w - 12*mm)
    line_y = area_top - 14*mm
    for ln in lines[:15]:
        c.drawString(col_M_x + 6*mm, line_y, ln)
        line_y -= 5.5*mm

    # ── 右カラム: 推し理由 / リスク ──
    c.setFillColor(C_WHITE)
    c.setStrokeColor(C_FAINT)
    c.setLineWidth(0.6)
    c.roundRect(col_R_x, area_bottom, col_R_w, area_h, 2*mm, stroke=1, fill=1)

    # 推し理由 (上半分)
    reasons = (ph.get('reasons') or [])[:4]
    reason_h = area_h * 0.55
    reason_top = area_top - 6*mm
    c.setFillColor(accent)
    c.setFont(F_KAK, 10)
    c.drawString(col_R_x + 4*mm, reason_top, '✓ 推し理由')

    c.setFillColor(C_SUMI)
    c.setFont(F_KAK, 9)
    ry = reason_top - 6*mm
    for r in reasons:
        lines_r = wrap_jp(c, r, F_KAK, 9, col_R_w - 12*mm)
        for j, ln in enumerate(lines_r[:2]):
            prefix = '・' if j == 0 else '　'
            c.drawString(col_R_x + 5*mm, ry, f'{prefix}{ln}')
            ry -= 5*mm
        ry -= 0.8*mm

    # リスク (下半分)
    risks = (ph.get('risks') or [])[:3]
    risk_top = area_bottom + area_h * 0.45
    c.setFillColor(C_SHU)
    c.setFont(F_KAK, 10)
    c.drawString(col_R_x + 4*mm, risk_top, '⚠ リスク')

    c.setFillColor(C_SUMI)
    c.setFont(F_KAK, 9)
    ry = risk_top - 6*mm
    for r in risks:
        lines_r = wrap_jp(c, r, F_KAK, 9, col_R_w - 12*mm)
        for j, ln in enumerate(lines_r[:2]):
            prefix = '・' if j == 0 else '　'
            c.drawString(col_R_x + 5*mm, ry, f'{prefix}{ln}')
            ry -= 5*mm
        ry -= 0.8*mm

    # ── 買い目役割バー (下部) ──
    bar_h = 8*mm
    bar_y = area_bottom - bar_h - 3*mm
    c.setFillColor(accent_light)
    c.setStrokeColor(accent)
    c.setLineWidth(0.6)
    c.setDash(3, 2)
    c.rect(15*mm, bar_y, W - 30*mm, bar_h, stroke=1, fill=1)
    c.setDash()
    c.setFillColor(accent)
    c.setFont(F_KAK, 11)
    t = f'買い目役割：{ph.get("buyRole","-")}'
    c.drawString(20*mm, bar_y + 2.8*mm, t)

    draw_footer(c, W, race_name, page_idx, page_total, footer_quip, url)


# ══════════════════════════════════════════════════════════════════
# 買い目 (表紙用, 横長バー)
# ══════════════════════════════════════════════════════════════════
def draw_buy_bar(c, x, y, w, h, fb):
    c.setStrokeColor(C_SHU)
    c.setLineWidth(1.2)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)

    c.setFillColor(C_SHU)
    c.setFont(F_MIN, 12)
    c.drawString(x + 4*mm, y + h - 6*mm, '━ 買い目構成 ／ 三方よし ━')

    tan = fb.get('tan') or {}
    fuku = fb.get('fuku') or {}
    wb = fb.get('wide4box') or {}

    def fmt_num(n):
        return f'({n})' if n is not None else ''

    # 3カラム横並び
    col_w = (w - 8*mm) / 3
    cols = [
        ('天の道 ／ 単勝',        C_KIN_D,  tan,  f'¥{tan.get("amount",0)}'),
        ('地の道 ／ 複勝',        C_MIDORI, fuku, f'¥{fuku.get("amount",0)}'),
        ('人の道 ／ ワイド4頭BOX', C_SHU,    wb,   f'¥{wb.get("amount",0)} ({wb.get("comboCount",0)}点)'),
    ]
    for i, (title, color, obj, amt) in enumerate(cols):
        cx = x + 4*mm + i * col_w
        c.setFillColor(color)
        c.setFont(F_KAK, 9)
        c.drawString(cx, y + h - 13*mm, title)

        # 対象馬/金額
        c.setFillColor(C_SUMI)
        c.setFont(F_MIN, 10)
        if i < 2:  # 単勝/複勝
            name = obj.get('name', '-')
            label = f'{fmt_num(obj.get("num"))}  {name}'.strip()
            c.drawString(cx, y + h - 19*mm, label)

        c.setFillColor(color)
        c.setFont(F_KAK, 13)
        tw = sw(c, amt, F_KAK, 13)
        c.drawString(cx + col_w - tw - 4*mm, y + h - 14*mm, amt)

    # 組み合わせ6通り (下部)
    combos = wb.get('combos') or []
    def combo_str(co):
        a, b = co.get('pair', [None, None])
        if a is not None and b is not None:
            return f'{a}-{b}'
        na, nb = (co.get('names') or ['', ''])[:2]
        return f'{(na or "")[:3]}-{(nb or "")[:3]}'
    txt = '／ '.join(combo_str(co) for co in combos[:6])
    c.setFillColor(C_MUTED)
    c.setFont(F_KAK, 8)
    c.drawString(x + 4*mm, y + 3*mm, f'ワイド組合せ: {txt}')


# ══════════════════════════════════════════════════════════════════
# スコアボード (横向き)
# ══════════════════════════════════════════════════════════════════
def draw_scoreboard_page(c, W, H, fb, race_name):
    c.setFillColor(C_SHU)
    c.rect(0, H - 15*mm, W, 15*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont(F_MIN, 18)
    c.drawString(15*mm, H - 10*mm, '採点詳細  ／  全馬スコアボード')
    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont(F_KAK, 9)
    tw = sw(c, race_name, F_KAK, 9)
    c.drawString(W - 15*mm - tw, H - 10*mm, race_name)

    cfg = fb.get('config') or {}
    weights = cfg.get('weights') or {}
    pts = cfg.get('gradePoints') or {}

    c.setFillColor(C_MUTED)
    c.setFont(F_KAK, 8)
    legend = (f'重み: 言霊×{weights.get("relComment",2)} ／ 神眼×{weights.get("shingan",1.5)} '
              f'／ ラップ×{weights.get("lapFactors",1)} ／ 外厩×{weights.get("gaikyuFactor",0.5)}'
              f'　　点数: S={pts.get("S",5)}, A={pts.get("A",3)}, B={pts.get("B",0)}, C={pts.get("C",-2)}, D={pts.get("D",-4)}')
    c.drawString(15*mm, H - 20*mm, legend)

    # ヘッダ (legend から十分離す)
    cy = H - 32*mm
    c.setStrokeColor(C_SUMI)
    c.setLineWidth(0.8)
    c.line(15*mm, cy + 6*mm, W - 15*mm, cy + 6*mm)

    cols_x = [15*mm, 25*mm, 40*mm, 115*mm, 135*mm, 155*mm, 175*mm, 200*mm, 230*mm, 260*mm]
    headers = ['順', '馬番', '馬名', '言霊', '神眼', 'ラップ', '外厩', '総合', '想定OD', '役割']
    c.setFillColor(C_SUMI)
    c.setFont(F_KAK, 8)
    for cx, h in zip(cols_x, headers):
        c.drawString(cx, cy + 2*mm, h)

    c.line(15*mm, cy - 0.5*mm, W - 15*mm, cy - 0.5*mm)

    cy -= 5*mm
    row_h = 5.2*mm
    c.setLineWidth(0.25)
    c.setStrokeColor(HexColor('#DCD4BE'))
    for s in fb.get('scoreboard', []):
        if cy < 18*mm: break
        bd = s.get('breakdown') or {}
        c.setFillColor(C_SHU)
        c.setFont(F_KAK, 9)
        c.drawString(cols_x[0], cy, str(s.get('rank','?')))

        num = s.get('num')
        num_text = str(num) if num is not None else '?'
        c.setFillColor(C_SUMI)
        c.roundRect(cols_x[1], cy - 0.8*mm, 7*mm, 4.2*mm, 0.5*mm, stroke=0, fill=1)
        c.setFillColor(C_KIN)
        c.setFont(F_KAK, 8)
        tw = sw(c, num_text, F_KAK, 8)
        c.drawString(cols_x[1] + (7*mm - tw)/2, cy + 0.4*mm, num_text)

        c.setFillColor(C_SUMI)
        c.setFont(F_MIN, 10)
        c.drawString(cols_x[2], cy, s.get('name',''))

        for i, k in enumerate(['relComment','shingan','lapFactors','gaikyuFactor']):
            gr = (bd.get(k) or {}).get('grade')
            if gr:
                g_color = GRADE_COLOR.get(gr, HexColor('#5D5A56'))
                g_text = gr
                cx = cols_x[3 + i]
                c.setFillColor(g_color)
                c.roundRect(cx, cy - 0.6*mm, 7*mm, 4*mm, 0.3*mm, stroke=0, fill=1)
                c.setFillColor(C_WHITE)
                c.setFont(F_KAK, 8)
                tw = sw(c, g_text, F_KAK, 8)
                c.drawString(cx + (7*mm - tw)/2, cy + 0.4*mm, g_text)
            else:
                # 無評価は薄い枠のみ
                cx = cols_x[3 + i]
                c.setStrokeColor(HexColor('#D0C7AD'))
                c.setLineWidth(0.4)
                c.setFillColor(HexColor('#F4EEDD'))
                c.roundRect(cx, cy - 0.6*mm, 7*mm, 4*mm, 0.3*mm, stroke=1, fill=1)
                c.setFillColor(HexColor('#B8AC8E'))
                c.setFont(F_KAK, 8)
                tw = sw(c, '-', F_KAK, 8)
                c.drawString(cx + (7*mm - tw)/2, cy + 0.4*mm, '-')

        c.setFillColor(C_SUMI)
        c.setFont(F_KAK, 10)
        c.drawString(cols_x[7], cy, f'{s.get("score",0):.2f}')

        c.setFillColor(C_MUTED)
        c.setFont(F_KAK, 9)
        od = s.get('expectedOdds')
        c.drawString(cols_x[8], cy, f'{od:.1f}' if od else '-')

        # 役割(採用なら色付け)
        role_tag = s.get('role')
        role_label = {'main':'本命','counter':'対抗','support':'押','hole':'穴'}.get(role_tag, '')
        if role_label:
            role_color = ROLE_META.get(role_tag, {}).get('accent', C_MUTED)
            c.setFillColor(role_color)
            c.setFont(F_KAK, 8)
            c.drawString(cols_x[9], cy, f'[{role_label}]')

        c.line(15*mm, cy - 1.8*mm, W - 15*mm, cy - 1.8*mm)
        cy -= row_h


# ══════════════════════════════════════════════════════════════════
# 落選の儀
# ══════════════════════════════════════════════════════════════════
def draw_dropped_page(c, W, H, pres, race_name):
    c.setFillColor(C_SHU)
    c.rect(0, H - 15*mm, W, 15*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont(F_MIN, 18)
    c.drawString(15*mm, H - 10*mm, '落選の儀  ／  今回は見送り')

    dropped = pres.get('dropped') or []
    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont(F_KAK, 9)
    c.drawString(W - 60*mm, H - 10*mm, f'（買わない馬 {len(dropped)}頭）')

    # 2カラム配置 (バランス重視: ceil(n/2) を col0 に)
    col_w = (W - 30*mm - 6*mm) / 2
    col_x = [15*mm, 15*mm + col_w + 6*mm]
    cy_start = H - 25*mm
    row_h = 7*mm
    rows_per_col_max = int((cy_start - 20*mm) / row_h)

    total = min(len(dropped), rows_per_col_max * 2)
    half = (total + 1) // 2

    c.setFillColor(C_MUTED)
    c.setFont(F_MIN, 8)
    c.drawString(15*mm, H - 18*mm, '※落選馬にも物語がある。でも、今回は静かに見送る。')

    for i, d in enumerate(dropped[:total]):
        col = 0 if i < half else 1
        row = i if col == 0 else (i - half)
        x = col_x[col]
        cy = cy_start - row * row_h

        # 薄い背景
        if row % 2 == 1:
            c.setFillColor(HexColor('#EDE4CB'))
            c.rect(x, cy - 2*mm, col_w, row_h - 0.5*mm, stroke=0, fill=1)

        c.setFillColor(C_MUTED)
        c.setFont(F_KAK, 7)
        c.drawString(x + 1*mm, cy, f'{d.get("rank","?")}位')

        num = d.get('num')
        num_text = str(num) if num is not None else '?'
        c.setFillColor(HexColor('#4A4A4A'))
        c.roundRect(x + 8*mm, cy - 0.5*mm, 7*mm, 4.5*mm, 0.5*mm, stroke=0, fill=1)
        c.setFillColor(HexColor('#E8E0C8'))
        c.setFont(F_KAK, 7.5)
        tw = sw(c, num_text, F_KAK, 7.5)
        c.drawString(x + 8*mm + (7*mm - tw)/2, cy + 0.7*mm, num_text)

        c.setFillColor(C_SUMI)
        c.setFont(F_MIN, 10)
        c.drawString(x + 18*mm, cy + 0.5*mm, d.get('name', ''))

        c.setFillColor(C_MUTED)
        c.setFont(F_KAK, 7.5)
        if d.get('score') is not None:
            c.drawString(x + 58*mm, cy + 0.5*mm, f'{d["score"]:.1f}pt')

        # ノート (カスタム → デフォルト)
        note = d.get('note') or pick_humor_note(d)
        c.setFillColor(HexColor('#5D5A56'))
        c.setFont(F_KAK, 8)
        lines = wrap_jp(c, note, F_KAK, 8, col_w - 75*mm)
        c.drawString(x + 75*mm, cy + 0.5*mm, lines[0] if lines else '')


def pick_humor_note(d):
    """落選馬のフォールバック一言"""
    isAna = d.get('isAna')
    score = d.get('score') or 0
    if isAna and score < 3:
        return HUMOR_DROPPED_NOTES['ana_miss']
    if score < 2:
        return HUMOR_DROPPED_NOTES['low_rel']
    if score < 5:
        return HUMOR_DROPPED_NOTES['low_gk']
    return HUMOR_DROPPED_NOTES['default']


# ══════════════════════════════════════════════════════════════════
# メイン生成
# ══════════════════════════════════════════════════════════════════
def generate_pdf(label, rn, race_name, race_meta, date_label):
    out = OUT_DIR / f'{label}-shintaku.pdf'
    data, fb, pres = load_pres(rn)
    horses = pres.get('horses') or []

    page_size = landscape(A4)   # 842 × 595 pt ≒ 297 × 210 mm
    W, H = page_size
    c = canvas.Canvas(str(out), pagesize=page_size)

    # サブタイトルはレース毎に順次巡回(3レースで3通り見える)
    subtitle = HUMOR_SUBTITLES[_RACE_COUNTER['i'] % len(HUMOR_SUBTITLES)]
    _RACE_COUNTER['i'] += 1
    # フッターは 7ページ分で 3通り (0,1,2,0,1,2,0) 循環
    footer_quips = [HUMOR_FOOTERS[i % len(HUMOR_FOOTERS)] for i in range(7)]
    url = 'bakenshiug.github.io/ug-keiba'
    total_pages = 7

    # ─── ページ1: 表紙 + 4頭サマリ(1×4) + 買い目 ───
    c.setFillColor(C_PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    y_after_header = draw_cover_header(c, W, H, race_name, race_meta, date_label, subtitle)

    # 4頭を横並び(1×4)
    margin = 12*mm
    gap = 4*mm
    card_w = (W - 2*margin - 3*gap) / 4
    card_h = 88*mm
    cards_top_y = y_after_header - 4*mm
    for i, ph in enumerate(horses[:4]):
        x = margin + i * (card_w + gap)
        y = cards_top_y - card_h
        draw_summary_card(c, x, y, card_w, card_h, ph)

    # 買い目バー
    by_top = cards_top_y - card_h - 6*mm
    buy_h = 30*mm
    draw_buy_bar(c, margin, by_top - buy_h, W - 2*margin, buy_h, fb)

    draw_footer(c, W, race_name, 1, total_pages, footer_quips[0], url)

    # ─── ページ2-5: 各馬詳細 ───
    for i, ph in enumerate(horses[:4]):
        c.showPage()
        c.setFillColor(C_PAPER)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        draw_detail_page(c, W, H, ph, i, race_name, i + 2, total_pages, footer_quips[i + 1], url)

    # ─── ページ6: スコアボード ───
    c.showPage()
    c.setFillColor(C_PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    draw_scoreboard_page(c, W, H, fb, race_name)
    draw_footer(c, W, race_name, 6, total_pages, footer_quips[5], url)

    # ─── ページ7: 落選の儀 ───
    c.showPage()
    c.setFillColor(C_PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    draw_dropped_page(c, W, H, pres, race_name)
    draw_footer(c, W, race_name, 7, total_pages, footer_quips[6], url)

    c.save()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None, help='特定レースのみ生成 (例: 2026-04-25-aobasho)')
    args = ap.parse_args()

    print('=== 四神の御神託 PDFレポート生成 (YouTube横向き版) ===')
    for label, rn, race_name, race_meta, date_label in RACE_MAP:
        if args.only and args.only != label:
            continue
        try:
            print(f'▶ {label}  ({race_name})')
            out = generate_pdf(label, rn, race_name, race_meta, date_label)
            print(f'  [pdf] {out}')
        except Exception as e:
            print(f'  [err] {label}: {e}')


if __name__ == '__main__':
    main()
