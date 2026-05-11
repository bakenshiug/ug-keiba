#!/usr/bin/env python3
"""
YouTubeバナー v4: 鳥居削除＋楕円ラジアルマスクで自然な溶け込み
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path
import random

SRC = Path("/Users/buntawakase/Desktop/Gemini_Generated_Image_cfntgbcfntgbcfnt.jpeg")
OUT_DIR = Path("/Users/buntawakase/Desktop/ug-keiba/assets/yt")
OUT_DIR.mkdir(parents=True, exist_ok=True)

src = Image.open(SRC).convert("RGB")
W, H = src.size
print(f"元画像: {W}x{H}")

TARGET_W, TARGET_H = 2048, 1152
SAFE_CY = 576

SHU = (155, 45, 48)
SHU_DK = (85, 20, 20)
KIN = (201, 169, 97)
KIN_LT = (224, 200, 142)
IVORY = (255, 251, 232)

# ===================================================================
# キャラ：バストアップクロップ→縦800にリサイズ
# ===================================================================
CHAR_CROP = (200, 0, 1000, 700)  # 800×700
char_bust = src.crop(CHAR_CROP)
CHAR_H = 800
CHAR_W = int(char_bust.size[0] * CHAR_H / char_bust.size[1])  # 914
char_final = char_bust.resize((CHAR_W, CHAR_H), Image.LANCZOS)

# 顔中心y (リサイズ後) ≈229
y_face = int(200 * CHAR_H / char_bust.size[1])
char_y = SAFE_CY - y_face  # 347
char_x = TARGET_W - 180 - CHAR_W  # 954

# ===================================================================
# 楕円ラジアルマスク（縁を柔らかくフェード）
# ===================================================================
mask = Image.new("L", (CHAR_W, CHAR_H), 0)
md = ImageDraw.Draw(mask)
# 楕円を少し大きめに描いて、ぼかしで縁を自然に
pad_x, pad_y = -30, -10  # 楕円内側オフセット
md.ellipse((pad_x, pad_y, CHAR_W - pad_x, CHAR_H - pad_y), fill=255)
# 強めぼかし → 縁のフェード幅を稼ぐ
mask = mask.filter(ImageFilter.GaussianBlur(70))

char_rgba = char_final.convert("RGBA")
char_rgba.putalpha(mask)

# ===================================================================
# 背景：朱グラデ＋和紙ノイズ
# ===================================================================
bg = Image.new("RGB", (TARGET_W, TARGET_H), SHU_DK)
d = ImageDraw.Draw(bg)
for x in range(TARGET_W):
    r = abs((x / TARGET_W) - 0.5) * 2
    R = int(SHU[0] * (1 - r * 0.35) + SHU_DK[0] * (r * 0.35))
    G = int(SHU[1] * (1 - r * 0.35) + SHU_DK[1] * (r * 0.35))
    B = int(SHU[2] * (1 - r * 0.35) + SHU_DK[2] * (r * 0.35))
    d.line([(x, 0), (x, TARGET_H)], fill=(R, G, B))

# 和紙ノイズ
noise = Image.new("L", (TARGET_W // 4, TARGET_H // 4), 128)
px = noise.load()
random.seed(42)
for y in range(noise.size[1]):
    for xx in range(noise.size[0]):
        px[xx, y] = 128 + random.randint(-10, 10)
noise = noise.resize((TARGET_W, TARGET_H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.8))
bg = Image.blend(bg, Image.merge("RGB", (noise, noise, noise)), 0.09)

# キャラ合成（楕円マスクで縁自然）
banner = bg.convert("RGBA")
banner.paste(char_rgba, (char_x, char_y), char_rgba)
banner = banner.convert("RGB")

# ===================================================================
# タイトル（鳥居削除、金装飾線で代替）
# ===================================================================
draw = ImageDraw.Draw(banner)

font_mincho_path = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"
font_sans_path = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
try:
    font_big = ImageFont.truetype(font_mincho_path, 120)
    font_sub = ImageFont.truetype(font_sans_path, 36)
except Exception:
    font_big = ImageFont.load_default()
    font_sub = ImageFont.load_default()

TITLE_X = 290
TITLE_Y_TOP = 418  # セーフエリア内

def text_shadow(xy, text, font, fill, off=3):
    x, y = xy
    draw.text((x + off, y + off), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)

# 上部装飾線（鳥居の代わり・二重金線）
TITLE_TOP_Y = TITLE_Y_TOP - 30
draw.line([(TITLE_X, TITLE_TOP_Y), (TITLE_X + 500, TITLE_TOP_Y)], fill=KIN, width=3)
draw.line([(TITLE_X, TITLE_TOP_Y + 7), (TITLE_X + 500, TITLE_TOP_Y + 7)], fill=KIN_LT, width=1)

# タイトル本体
text_shadow((TITLE_X, TITLE_Y_TOP), "UG競馬", font_big, IVORY)
text_shadow((TITLE_X, TITLE_Y_TOP + 140), "ワイド神宮", font_big, KIN)

# 下部装飾線
draw.line([(TITLE_X, TITLE_Y_TOP + 283), (TITLE_X + 500, TITLE_Y_TOP + 283)], fill=KIN_LT, width=1)
draw.line([(TITLE_X, TITLE_Y_TOP + 290), (TITLE_X + 500, TITLE_Y_TOP + 290)], fill=KIN, width=3)

# サブタイトル
text_shadow((TITLE_X, TITLE_Y_TOP + 305),
            "AI神託 × 本格馬券師",
            font_sub, (244, 228, 184))

# 保存
out_path = OUT_DIR / "yt_banner_2048x1152_titled.jpg"
banner.save(out_path, quality=92, optimize=True)

# デバッグ版（セーフエリア枠入り）
banner_dbg = banner.copy()
d3 = ImageDraw.Draw(banner_dbg)
d3.rectangle([406, 407, 1642, 745], outline=(255, 230, 0), width=4)
d3.line([(0, 364), (TARGET_W, 364)], fill=(0, 200, 255), width=3)
d3.line([(0, 788), (TARGET_W, 788)], fill=(0, 200, 255), width=3)
banner_dbg.save(OUT_DIR / "yt_banner_2048x1152_debug.jpg", quality=88)

print(f"\n📏 出力結果:")
for f in sorted(OUT_DIR.glob("yt_banner_*.jpg")):
    im = Image.open(f)
    print(f"  {f.name:45s} {im.size[0]}x{im.size[1]}  {f.stat().st_size/1024:.0f}KB")
