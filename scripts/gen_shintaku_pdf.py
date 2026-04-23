#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四神の御神託 PDFレポート生成スクリプト
=====================================
使用: python3 scripts/gen_shintaku_pdf.py [--only <race-label>]

入力:
  docs/data/race-notes/{race}.json の finalBets.presentation

出力:
  docs/img/pdf/{race}-shintaku.pdf (A4縦)

構成:
  1枚目: 表紙 + 4頭サマリ + 買い目
  2枚目: 落選の儀 + 採点詳細
"""
import json
import argparse
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
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

# 日本語フォント登録（reportlab 同梱の CID フォント使用: Hiragino .ttc は CFF アウトラインで非対応のため）
# Heisei Min W3 = 明朝、Heisei Kaku Gothic W5 = 角ゴシック（単一ウェイトのみ利用可）
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
# 既存コードが参照するフォント名エイリアス
FONT_MIN    = 'HeiseiMin-W3'
FONT_KAKU_L = 'HeiseiKakuGo-W5'
FONT_KAKU_M = 'HeiseiKakuGo-W5'
FONT_KAKU_B = 'HeiseiKakuGo-W5'

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

GRADE_COLOR = {
    'S': HexColor('#C49A3D'),
    'A': HexColor('#2F5C3B'),
    'B': HexColor('#2D4A6E'),
    'C': HexColor('#A06654'),
    'D': HexColor('#3E3A36'),
}

SHIJIN = {
    'seiryu':  {'jp': '青龍', 'factor': '言霊',  'color': C_MIDORI},
    'suzaku':  {'jp': '朱雀', 'factor': '神眼',  'color': C_SHU},
    'byakko':  {'jp': '白虎', 'factor': 'ラップ', 'color': C_KIN_D},
    'genbu':   {'jp': '玄武', 'factor': '外厩',  'color': HexColor('#1E1E1E')},
}

ROLE_META = {
    'main':    {'label': '本命',   'accent': C_SHU},
    'counter': {'label': '対抗',   'accent': C_KIN_D},
    'support': {'label': '押さえ', 'accent': C_MIDORI},
    'hole':    {'label': '穴',     'accent': HexColor('#6E4A1F')},
}


def load_pres(rn):
    p = BASE / 'docs/data/race-notes' / f'{rn}.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    fb = data.get('finalBets') or {}
    pres = fb.get('presentation')
    if not pres:
        raise RuntimeError(f'{rn}: presentation 未生成')
    return data, fb, pres


def string_width(c, text, font_name, size):
    return c.stringWidth(text, font_name, size)


def wrap_jp(c, text, font_name, size, max_w):
    """日本語想定テキスト折り返し"""
    lines = []
    line = ''
    for ch in text:
        if ch == '\n':
            lines.append(line)
            line = ''
            continue
        test = line + ch
        if string_width(c, test, font_name, size) > max_w:
            lines.append(line)
            line = ch
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def draw_shijin_chip(c, x, y, w, h, kind, grade):
    meta = SHIJIN[kind]
    color = meta['color']
    c.setStrokeColor(color)
    c.setLineWidth(1)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)
    # 漢字
    c.setFillColor(color)
    c.setFont('HeiseiMin-W3', 10)
    c.drawString(x + 2*mm, y + h - 5*mm, meta['jp'])
    # ファクター
    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 5.5)
    c.drawString(x + 2*mm, y + 1.8*mm, meta['factor'])
    # グレード
    g_color = GRADE_COLOR.get(grade, HexColor('#B4AA96'))
    g_text = grade if grade else '—'
    bg_w = 7*mm
    bg_h = 5*mm
    bg_x = x + w - bg_w - 1.5*mm
    bg_y = y + (h - bg_h) / 2
    c.setFillColor(g_color)
    c.roundRect(bg_x, bg_y, bg_w, bg_h, 1*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont('HeiseiKakuGo-W5', 10)
    tw = string_width(c, g_text, 'HeiseiKakuGo-W5', 10)
    c.drawString(bg_x + (bg_w - tw) / 2, bg_y + 1.2*mm, g_text)


def draw_page_header(c, W, H, race_name, race_meta, date_label):
    # 上部朱帯
    band_h = 40*mm
    c.setFillColor(C_SHU)
    c.rect(0, H - band_h, W, band_h, stroke=0, fill=1)

    # 金線2本
    c.setStrokeColor(C_KIN)
    c.setLineWidth(0.6)
    c.line(15*mm, H - band_h - 2*mm, W - 15*mm, H - band_h - 2*mm)
    c.line(15*mm, H - band_h - 4*mm, W - 15*mm, H - band_h - 4*mm)

    # FINAL ORACLE / 四神の御神託
    c.setFillColor(C_KIN)
    c.setFont('HeiseiKakuGo-W5', 8)
    t = 'FINAL ORACLE  ／  四神の御神託'
    tw = string_width(c, t, 'HeiseiKakuGo-W5', 8)
    c.drawString((W - tw) / 2, H - 10*mm, t)

    # 御神託降臨
    c.setFillColor(C_WHITE)
    c.setFont('HeiseiMin-W3', 24)
    t = '御神託降臨'
    tw = string_width(c, t, 'HeiseiMin-W3', 24)
    c.drawString((W - tw) / 2, H - 22*mm, t)

    # レース名
    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont('HeiseiMin-W3', 18)
    tw = string_width(c, race_name, 'HeiseiMin-W3', 18)
    c.drawString((W - tw) / 2, H - 32*mm, race_name)

    # メタ情報
    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont('HeiseiKakuGo-W5', 10)
    meta_text = f'{race_meta}  ／  {date_label}'
    tw = string_width(c, meta_text, 'HeiseiKakuGo-W5', 10)
    c.drawString((W - tw) / 2, H - 38*mm, meta_text)

    return H - band_h - 10*mm


def draw_horse_box(c, x, y, w, h, ph):
    """1頭分カード (A4用, 幅≒90mm×高さ60mm想定)"""
    role = ROLE_META.get(ph.get('roleTag'), ROLE_META['support'])
    accent = role['accent']

    # 枠
    c.setStrokeColor(accent)
    c.setLineWidth(1.2)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)

    # 役割帯
    band_h = 8*mm
    c.setFillColor(accent)
    c.rect(x + 0.3*mm, y + h - band_h - 0.3*mm, w - 0.6*mm, band_h, stroke=0, fill=1)

    # 役割ラベル
    c.setFillColor(C_WHITE)
    c.setFont('HeiseiMin-W3', 10)
    c.drawString(x + 3*mm, y + h - 6*mm, f'【{role["label"]}】')

    # 人気/穴
    is_hole = ph.get('popularity') == 'hole'
    pop_text = '[穴]' if is_hole else '[人気]'
    c.setFillColor(HexColor('#FFE5A1') if is_hole else HexColor('#D4F0C8'))
    pop_x = x + 18*mm
    c.roundRect(pop_x, y + h - 7*mm, 10*mm, 5*mm, 0.5*mm, stroke=0, fill=1)
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiKakuGo-W5', 7)
    c.drawString(pop_x + 1.3*mm, y + h - 5.4*mm, pop_text)

    # スコア右
    score = ph.get('score')
    if score is not None:
        c.setFillColor(HexColor('#F5EDD6'))
        c.setFont('HeiseiKakuGo-W5', 12)
        t = f'{score:.1f}pt'
        tw = string_width(c, t, 'HeiseiKakuGo-W5', 12)
        c.drawString(x + w - tw - 3*mm, y + h - 6*mm, t)

    # 馬番 + 馬名
    cy = y + h - band_h - 9*mm
    num = ph.get('num')
    num_text = str(num) if num is not None else '?'
    c.setFillColor(C_SUMI)
    c.roundRect(x + 3*mm, cy - 2*mm, 11*mm, 9*mm, 1*mm, stroke=0, fill=1)
    c.setFillColor(C_KIN)
    c.setFont('HeiseiKakuGo-W5', 14)
    tw = string_width(c, num_text, 'HeiseiKakuGo-W5', 14)
    c.drawString(x + 3*mm + (11*mm - tw)/2, cy + 0.5*mm, num_text)

    c.setFillColor(C_SUMI)
    c.setFont('HeiseiMin-W3', 13)
    c.drawString(x + 17*mm, cy + 0.8*mm, ph.get('name', ''))

    od = ph.get('expectedOdds')
    if od is not None:
        c.setFillColor(C_MUTED)
        c.setFont('HeiseiKakuGo-W5', 7)
        c.drawString(x + 17*mm, cy - 2.5*mm, f'想定OD {od:.1f}')

    # 四神チップ
    cy -= 14*mm
    chip_w = (w - 6*mm) / 4
    chip_h = 10*mm
    sg = ph.get('shijinGrades') or {}
    for i, k in enumerate(['seiryu','suzaku','byakko','genbu']):
        cx = x + 3*mm + i * chip_w
        draw_shijin_chip(c, cx, cy, chip_w - 0.7*mm, chip_h, k, sg.get(k))

    # 買い目役割
    cy -= 5*mm
    c.setFillColor(HexColor('#F8F0D8'))
    c.rect(x + 3*mm, cy - 2.5*mm, w - 6*mm, 4.5*mm, stroke=0, fill=1)
    c.setFillColor(C_KIN_D)
    c.setFont('HeiseiKakuGo-W5', 7)
    c.drawString(x + 4*mm, cy - 1*mm, f'買い目：{ph.get("buyRole","-")}')


def draw_horse_detail_page(c, W, H, ph, idx):
    """1頭分詳細ページ (1ページ専有) — 長文コメント + 推し理由/リスク"""
    role = ROLE_META.get(ph.get('roleTag'), ROLE_META['support'])
    accent = role['accent']

    # 上部役割帯
    c.setFillColor(accent)
    c.rect(0, H - 18*mm, W, 18*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont('HeiseiMin-W3', 20)
    c.drawString(15*mm, H - 12*mm, f'【{role["label"]}】  第{idx+1}候補')

    c.setFillColor(HexColor('#F5EDD6'))
    c.setFont('HeiseiKakuGo-W5', 9)
    c.drawString(15*mm, H - 16*mm, f'pick {ph.get("pickOrder","-")}/4  ／  scoreboard rank{ph.get("rank","-")}  ／  想定OD {ph.get("expectedOdds","-")}倍')

    score = ph.get('score')
    if score is not None:
        c.setFillColor(C_KIN)
        c.setFont('HeiseiKakuGo-W5', 22)
        t = f'{score:.1f}pt'
        tw = string_width(c, t, 'HeiseiKakuGo-W5', 22)
        c.drawString(W - tw - 15*mm, H - 13*mm, t)

    # 馬番 + 馬名 大書き
    cy = H - 32*mm
    num = ph.get('num')
    num_text = str(num) if num is not None else '?'
    c.setFillColor(C_SUMI)
    c.roundRect(15*mm, cy - 6*mm, 18*mm, 14*mm, 1.5*mm, stroke=0, fill=1)
    c.setFillColor(C_KIN)
    c.setFont('HeiseiKakuGo-W5', 22)
    tw = string_width(c, num_text, 'HeiseiKakuGo-W5', 22)
    c.drawString(15*mm + (18*mm - tw)/2, cy - 1*mm, num_text)

    c.setFillColor(C_SUMI)
    c.setFont('HeiseiMin-W3', 26)
    c.drawString(37*mm, cy - 1*mm, ph.get('name', ''))

    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 9)
    meta_parts = []
    if ph.get('jockey'):  meta_parts.append(f'騎手 {ph.get("jockey")}')
    if ph.get('trainer'): meta_parts.append(f'厩舎 {ph.get("trainer")}')
    if ph.get('gaikyuLabel'): meta_parts.append(f'外厩 {ph.get("gaikyuLabel")}')
    if ph.get('sire'): meta_parts.append(f'父 {ph.get("sire")}')
    if meta_parts:
        c.drawString(37*mm, cy - 8*mm, '　'.join(meta_parts))

    # 四神バー
    cy -= 18*mm
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiKakuGo-W5', 9)
    c.drawString(15*mm, cy + 11*mm, '━ 四神の判定 ━')

    chip_w = (W - 30*mm) / 4
    chip_h = 14*mm
    sg = ph.get('shijinGrades') or {}
    for i, k in enumerate(['seiryu','suzaku','byakko','genbu']):
        cx = 15*mm + i * chip_w
        draw_shijin_chip(c, cx, cy - 3*mm, chip_w - 3*mm, chip_h, k, sg.get(k))

    # 見解コメント
    cy -= 22*mm
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiKakuGo-W5', 10)
    c.drawString(15*mm, cy + 6*mm, '━ 見解 ━')

    # 左縁ライン
    c.setFillColor(accent)
    c.rect(15*mm, cy - 30*mm, 1*mm, 32*mm, stroke=0, fill=1)

    c.setFillColor(C_SUMI)
    c.setFont('HeiseiMin-W3', 11)
    comment = ph.get('comment', '')
    lines = wrap_jp(c, comment, 'HeiseiMin-W3', 11, W - 38*mm)
    for i, ln in enumerate(lines[:10]):
        c.drawString(19*mm, cy + 2*mm - i * 5*mm, ln)

    # 推し理由 + リスク
    cy -= 50*mm
    col_w = (W - 35*mm) / 2

    # 推し理由
    c.setFillColor(accent)
    c.setFont('HeiseiKakuGo-W5', 10)
    c.drawString(15*mm, cy + 6*mm, '✓ 推し理由')
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiKakuGo-W5', 10)
    for i, r in enumerate((ph.get('reasons') or [])[:4]):
        c.drawString(17*mm, cy - i * 5*mm, f'・{r}')

    # リスク
    risk_x = 15*mm + col_w + 5*mm
    c.setFillColor(C_SHU)
    c.setFont('HeiseiKakuGo-W5', 10)
    c.drawString(risk_x, cy + 6*mm, '⚠ リスク')
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiKakuGo-W5', 10)
    for i, r in enumerate((ph.get('risks') or [])[:3]):
        # リスクは折り返し
        lines_r = wrap_jp(c, r, 'HeiseiKakuGo-W5', 10, col_w - 5*mm)
        for j, ln in enumerate(lines_r[:2]):
            prefix = '・' if j == 0 else '　'
            c.drawString(risk_x + 2*mm, cy - (i * 2 + j) * 5*mm, f'{prefix}{ln}')

    # 買い目役割
    cy -= 40*mm
    c.setFillColor(HexColor('#F8F0D8'))
    c.setStrokeColor(C_KIN_D)
    c.setLineWidth(0.5)
    c.setDash(2, 2)
    c.rect(15*mm, cy, W - 30*mm, 8*mm, stroke=1, fill=1)
    c.setDash()
    c.setFillColor(C_KIN_D)
    c.setFont('HeiseiKakuGo-W5', 11)
    c.drawString(19*mm, cy + 2.5*mm, f'買い目役割：{ph.get("buyRole","-")}')


def draw_buy_section(c, x, y, w, h, fb):
    """買い目ブロック"""
    c.setStrokeColor(C_SHU)
    c.setLineWidth(1.2)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)

    c.setFillColor(C_SHU)
    c.setFont('HeiseiMin-W3', 12)
    c.drawString(x + 4*mm, y + h - 7*mm, '━ 買い目構成 ━')

    tan = fb.get('tan') or {}
    fuku = fb.get('fuku') or {}
    wb = fb.get('wide4box') or {}

    def fmt_num(n):
        return f'({n})' if n is not None else ''

    row_h = 6.5*mm
    cy = y + h - 13*mm

    # 単勝
    c.setFillColor(C_KIN_D)
    c.setFont('HeiseiKakuGo-W5', 9)
    c.drawString(x + 5*mm, cy, '天の道 ／ 単勝')
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiMin-W3', 10)
    c.drawString(x + 40*mm, cy, f'{fmt_num(tan.get("num"))}  {tan.get("name","")}'.strip())
    c.setFillColor(C_KIN_D)
    c.setFont('HeiseiKakuGo-W5', 11)
    amt = f'¥{tan.get("amount",0)}'
    tw = string_width(c, amt, 'HeiseiKakuGo-W5', 11)
    c.drawString(x + w - tw - 5*mm, cy, amt)

    cy -= row_h
    # 複勝
    c.setFillColor(C_MIDORI)
    c.setFont('HeiseiKakuGo-W5', 9)
    c.drawString(x + 5*mm, cy, '地の道 ／ 複勝')
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiMin-W3', 10)
    c.drawString(x + 40*mm, cy, f'{fmt_num(fuku.get("num"))}  {fuku.get("name","")}'.strip())
    c.setFillColor(C_MIDORI)
    c.setFont('HeiseiKakuGo-W5', 11)
    amt = f'¥{fuku.get("amount",0)}'
    tw = string_width(c, amt, 'HeiseiKakuGo-W5', 11)
    c.drawString(x + w - tw - 5*mm, cy, amt)

    cy -= row_h
    # ワイド
    c.setFillColor(C_SHU)
    c.setFont('HeiseiKakuGo-W5', 9)
    c.drawString(x + 5*mm, cy, '人の道 ／ ワイド4頭BOX')
    c.setFillColor(C_SHU)
    c.setFont('HeiseiKakuGo-W5', 11)
    amt = f'¥{wb.get("amount",0)} ({wb.get("comboCount",0)}点)'
    tw = string_width(c, amt, 'HeiseiKakuGo-W5', 11)
    c.drawString(x + w - tw - 5*mm, cy, amt)

    # 6通り
    cy -= 5*mm
    combos = wb.get('combos') or []
    def combo_str(co):
        a, b = co.get('pair', [None, None])
        if a is not None and b is not None:
            return f'{a}-{b}'
        na, nb = (co.get('names') or ['', ''])[:2]
        def short(n): return (n or '')[:3]
        return f'{short(na)}-{short(nb)}'
    txt = '／ '.join(combo_str(c0) for c0 in combos[:6])
    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 8)
    lines = wrap_jp(c, txt, 'HeiseiKakuGo-W5', 8, w - 10*mm)
    for ln in lines[:2]:
        c.drawString(x + 5*mm, cy, ln)
        cy -= 4*mm


def draw_dropped_section(c, x, y, w, h, pres):
    """落選の儀"""
    c.setStrokeColor(C_MUTED)
    c.setLineWidth(0.4)
    c.setFillColor(C_WHITE)
    c.roundRect(x, y, w, h, 2*mm, stroke=1, fill=1)

    c.setFillColor(C_SUMI)
    c.setFont('HeiseiMin-W3', 12)
    c.drawString(x + 4*mm, y + h - 7*mm, '━ 落選の儀 ━')

    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 8)
    c.drawString(x + 30*mm, y + h - 7*mm, f'（買わない馬 {len(pres.get("dropped", []))}頭）')

    cy = y + h - 13*mm
    row_h = 4.8*mm
    max_rows = int((h - 15*mm) / row_h)
    for d in pres.get('dropped', [])[:max_rows]:
        # 順位
        c.setFillColor(C_MUTED)
        c.setFont('HeiseiKakuGo-W5', 7)
        c.drawString(x + 4*mm, cy, f'{d.get("rank","?")}位')
        # 馬番
        num = d.get('num')
        num_text = str(num) if num is not None else '?'
        c.setFillColor(HexColor('#4A4A4A'))
        c.roundRect(x + 12*mm, cy - 0.5*mm, 6*mm, 3.8*mm, 0.5*mm, stroke=0, fill=1)
        c.setFillColor(HexColor('#E8E0C8'))
        c.setFont('HeiseiKakuGo-W5', 7)
        tw = string_width(c, num_text, 'HeiseiKakuGo-W5', 7)
        c.drawString(x + 12*mm + (6*mm - tw)/2, cy + 0.5*mm, num_text)
        # 馬名
        c.setFillColor(C_SUMI)
        c.setFont('HeiseiMin-W3', 9)
        c.drawString(x + 20*mm, cy + 0.2*mm, d.get('name',''))
        # スコア
        c.setFillColor(C_MUTED)
        c.setFont('HeiseiKakuGo-W5', 7)
        if d.get('score') is not None:
            c.drawString(x + 60*mm, cy + 0.2*mm, f'{d["score"]:.1f}pt')
        # ノート
        c.setFillColor(C_SUMI)
        c.setFont('HeiseiKakuGo-W5', 8)
        note = d.get('note','')
        lines = wrap_jp(c, note, 'HeiseiKakuGo-W5', 8, w - 80*mm)
        c.drawString(x + 75*mm, cy + 0.2*mm, lines[0] if lines else '')
        cy -= row_h


def draw_scoreboard_page(c, W, H, fb, pres):
    """採点詳細ページ"""
    c.setFillColor(C_SHU)
    c.rect(0, H - 12*mm, W, 12*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont('HeiseiMin-W3', 16)
    c.drawString(15*mm, H - 9*mm, '採点詳細  ／  全馬スコアボード')

    cfg = fb.get('config') or {}
    weights = cfg.get('weights') or {}
    pts = cfg.get('gradePoints') or {}

    # 凡例
    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 8)
    legend = (f'重み: 言霊×{weights.get("relComment",2)} ／ 神眼×{weights.get("shingan",1.5)} '
              f'／ ラップ×{weights.get("lapFactors",1)} ／ 外厩×{weights.get("gaikyuFactor",0.5)}'
              f'　　点数: S={pts.get("S",5)}, A={pts.get("A",3)}, B={pts.get("B",0)}, C={pts.get("C",-2)}, D={pts.get("D",-4)}')
    c.drawString(15*mm, H - 17*mm, legend)

    # ヘッダ行
    cy = H - 25*mm
    c.setStrokeColor(C_SUMI)
    c.setLineWidth(0.8)
    c.line(15*mm, cy + 5*mm, W - 15*mm, cy + 5*mm)

    cols_x = [15*mm, 23*mm, 35*mm, 75*mm, 92*mm, 109*mm, 126*mm, 143*mm, 162*mm]
    headers = ['順', '馬番', '馬名', '言霊', '神眼', 'ラップ', '外厩', '総合', 'OD']
    c.setFillColor(C_SUMI)
    c.setFont('HeiseiKakuGo-W5', 8)
    for cx, h in zip(cols_x, headers):
        c.drawString(cx, cy + 7*mm, h)

    c.line(15*mm, cy + 3*mm, W - 15*mm, cy + 3*mm)

    # データ行
    cy -= 3*mm
    row_h = 4.8*mm
    c.setLineWidth(0.25)
    c.setStrokeColor(HexColor('#DCD4BE'))
    for s in fb.get('scoreboard', []):
        if cy < 15*mm: break  # ページ外
        bd = s.get('breakdown') or {}
        c.setFillColor(C_SHU)
        c.setFont('HeiseiKakuGo-W5', 8)
        c.drawString(cols_x[0], cy, str(s.get('rank','?')))

        # 馬番バッジ
        num = s.get('num')
        num_text = str(num) if num is not None else '?'
        c.setFillColor(C_SUMI)
        c.roundRect(cols_x[1], cy - 0.8*mm, 6*mm, 4*mm, 0.5*mm, stroke=0, fill=1)
        c.setFillColor(C_KIN)
        c.setFont('HeiseiKakuGo-W5', 7)
        tw = string_width(c, num_text, 'HeiseiKakuGo-W5', 7)
        c.drawString(cols_x[1] + (6*mm - tw)/2, cy + 0.3*mm, num_text)

        c.setFillColor(C_SUMI)
        c.setFont('HeiseiMin-W3', 9)
        c.drawString(cols_x[2], cy, s.get('name',''))

        # 各ファクターグレード
        for i, k in enumerate(['relComment','shingan','lapFactors','gaikyuFactor']):
            gr = (bd.get(k) or {}).get('grade')
            g_color = GRADE_COLOR.get(gr, HexColor('#5D5A56'))
            g_text = gr if gr else '—'
            cx = cols_x[3 + i]
            c.setFillColor(g_color)
            c.roundRect(cx, cy - 0.6*mm, 6*mm, 3.8*mm, 0.3*mm, stroke=0, fill=1)
            c.setFillColor(C_WHITE)
            c.setFont('HeiseiKakuGo-W5', 7)
            tw = string_width(c, g_text, 'HeiseiKakuGo-W5', 7)
            c.drawString(cx + (6*mm - tw)/2, cy + 0.3*mm, g_text)

        # 総合
        c.setFillColor(C_SUMI)
        c.setFont('HeiseiKakuGo-W5', 9)
        c.drawString(cols_x[7], cy, f'{s.get("score",0):.2f}')

        # OD
        c.setFillColor(C_MUTED)
        c.setFont('HeiseiKakuGo-W5', 8)
        od = s.get('expectedOdds')
        c.drawString(cols_x[8], cy, f'{od:.1f}' if od else '-')

        c.line(15*mm, cy - 1.5*mm, W - 15*mm, cy - 1.5*mm)
        cy -= row_h


def generate_pdf(label, rn, race_name, race_meta, date_label):
    out = OUT_DIR / f'{label}-shintaku.pdf'
    data, fb, pres = load_pres(rn)
    horses = pres.get('horses') or []

    W, H = A4
    c = canvas.Canvas(str(out), pagesize=A4)

    # ─── ページ1: 表紙 + 4頭サマリ + 買い目 ───
    c.setFillColor(C_PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    y_after_header = draw_page_header(c, W, H, race_name, race_meta, date_label)

    # 4頭サマリ 2x2 グリッド
    margin = 12*mm
    gap = 4*mm
    card_w = (W - 2*margin - gap) / 2
    card_h = 55*mm
    for i, ph in enumerate(horses[:4]):
        row = i // 2
        col = i % 2
        x = margin + col * (card_w + gap)
        y = y_after_header - 4*mm - card_h - row * (card_h + gap)
        draw_horse_box(c, x, y, card_w, card_h, ph)

    # 買い目
    by = y_after_header - 4*mm - 2 * (card_h + gap) - 6*mm
    buy_h = 32*mm
    draw_buy_section(c, margin, by - buy_h, W - 2*margin, buy_h, fb)

    # フッター: 揃い率など
    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 7)
    footer = (f'揃い率 {fb.get("readiness","")} ({fb.get("readinessPct",0)}%)  '
              f'／ 神眼 {fb.get("shinganCoverage","")}  '
              f'／ logic: {fb.get("logicVersion","")}  '
              f'／ 生成: {fb.get("generatedAt","")}')
    c.drawString(margin, 8*mm, footer)

    c.setFillColor(C_KIN_D)
    c.setFont('HeiseiKakuGo-W5', 7)
    url = 'bakenshiug.github.io/ug-keiba'
    tw = string_width(c, url, 'HeiseiKakuGo-W5', 7)
    c.drawString(W - margin - tw, 8*mm, url)

    # ─── ページ2-5: 各馬詳細 ───
    for i, ph in enumerate(horses[:4]):
        c.showPage()
        c.setFillColor(C_PAPER)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        draw_horse_detail_page(c, W, H, ph, i)

        c.setFillColor(C_MUTED)
        c.setFont('HeiseiKakuGo-W5', 7)
        c.drawString(margin, 8*mm, f'{race_name}  第{i+1}候補詳細  ({i+2}/{4+2})')
        c.setFillColor(C_KIN_D)
        c.drawString(W - margin - tw, 8*mm, url)

    # ─── ページ6: 落選 + 採点 ───
    c.showPage()
    c.setFillColor(C_PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    draw_scoreboard_page(c, W, H, fb, pres)

    # フッター（ページ6）
    c.setFillColor(C_MUTED)
    c.setFont('HeiseiKakuGo-W5', 7)
    c.drawString(margin, 8*mm, f'{race_name}  採点詳細  (6/6)')
    c.setFillColor(C_KIN_D)
    c.drawString(W - margin - tw, 8*mm, url)

    # ─── ページ7: 落選の儀（1ページ専有） ───
    c.showPage()
    c.setFillColor(C_PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    # ヘッダ
    c.setFillColor(C_SHU)
    c.rect(0, H - 12*mm, W, 12*mm, stroke=0, fill=1)
    c.setFillColor(C_WHITE)
    c.setFont('HeiseiMin-W3', 16)
    c.drawString(15*mm, H - 9*mm, '落選の儀  ／  買わない馬一覧')

    dropped_h = H - 24*mm
    draw_dropped_section(c, margin, 15*mm, W - 2*margin, dropped_h, pres)

    c.save()
    print(f'  [pdf] {out}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='特定レースのみ')
    args = ap.parse_args()

    targets = [r for r in RACE_MAP if not args.only or r[0] == args.only]
    print('=== 四神の御神託 PDFレポート生成 ===')
    for label, rn, race_name, race_meta, date_label in targets:
        print(f'▶ {label}  ({race_name})')
        try:
            generate_pdf(label, rn, race_name, race_meta, date_label)
        except Exception as e:
            import traceback
            print(f'  [ERROR] {e}')
            traceback.print_exc()


if __name__ == '__main__':
    main()
