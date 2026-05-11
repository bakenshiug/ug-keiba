#!/usr/bin/env python3
"""
YouTubeバナー v3: セーフエリア対応版

YouTubeバナー表示域:
  - テレビ:       2048×1152 全部表示
  - デスクトップ: 2560×423 帯（上下 364px ずつ削られる）
  - モバイル:     1546×423 帯
  - セーフエリア: 中央 1235×338 px（全デバイス共通）

v2の問題:
  - キャラ全身が縦いっぱい配置 → PC表示で顔も足も切れる
  - タイトルがキャラに被る

v3の設計:
  - キャラ = バストアップクロップ＋縦800pxに縮小して右半分配置
  - 顔中心をバナー縦中央(y=576)に合わせる → セーフエリア内に必ず入る
  - タイトル = 左エリアにゆったり、セーフエリア内に完全収容
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

# ===================================================================
# バナー 2048×1152（セーフエリア対応）
# ===================================================================
TARGET_W, TARGET_H = 2048, 1152
SAFE_Y_TOP = 407
SAFE_Y_BOT = 745
SAFE_CY = (SAFE_Y_TOP + SAFE_Y_BOT) // 2  # 576

# キャラ：バストアップ（顔＋胸）クロップ
# 元1190×1004 → (200, 0, 1000, 700) = 800×700
CHAR_CROP = (200, 0, 1000, 700)
char_bust = src.crop(CHAR_CROP)
cw, ch = char_bust.size
print(f"キャラバストアップ: {cw}x{ch}")

# 縦800pxにリサイズ（顔がセーフエリア内に納まる最大サイズ）
CHAR_H = 800
CHAR_W = int(cw * CHAR_H / ch)  # ≒914
char_final = char_bust.resize((CHAR_W, CHAR_H), Image.LANCZOS)
print(f"キャラ配置サイズ: {CHAR_W}x{CHAR_H}")

# 顔中心座標（元クロップ内 y≈200）→ リサイズ後 y_face
y_face_in_crop = int(200 * CHAR_H / ch)  # ≒229
# バナーに置く：顔がセーフエリア中央(y=576)に来る位置
char_y = SAFE_CY - y_face_in_crop  # ≒347

# 右寄せ：右余白 180
RIGHT_MARGIN = 180
char_x = TARGET_W - RIGHT_MARGIN - CHAR_W  # ≒954

print(f"キャラ配置座標: x={char_x}, y={char_y}")
print(f"顔中心バナー座標: x={char_x + CHAR_W//2}, y={char_y + y_face_in_crop}")

# ===================================================================
# 背景：朱色グラデ＋和紙ノイズ
# ===================================================================
SHU = (155, 45, 48)
SHU_DK = (85, 20, 20)
KIN = (201, 169, 97)
IVORY = (255, 251, 232)

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

# ===================================================================
# キャラ合成＋左右フェード
# ===================================================================
banner = bg.copy()
banner.paste(char_final, (char_x, char_y))

# キャラ画像の上下にも朱色背景が見える → 上下の境界をフェード
fade = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
fd = ImageDraw.Draw(fade)
edge = 120

# 左右フェード
for i in range(edge):
    alpha = int(255 * (1 - i / edge) ** 1.8)
    fd.line([(char_x + i, char_y), (char_x + i, char_y + CHAR_H)],
            fill=(*SHU_DK, alpha))
    fd.line([(char_x + CHAR_W - i, char_y), (char_x + CHAR_W - i, char_y + CHAR_H)],
            fill=(*SHU_DK, alpha))

# 上下フェード（キャラの上端下端が朱背景に溶けるように）
for i in range(edge):
    alpha = int(255 * (1 - i / edge) ** 1.8)
    fd.line([(char_x, char_y + i), (char_x + CHAR_W, char_y + i)],
            fill=(*SHU_DK, alpha))
    fd.line([(char_x, char_y + CHAR_H - i), (char_x + CHAR_W, char_y + CHAR_H - i)],
            fill=(*SHU_DK, alpha))

banner = Image.alpha_composite(banner.convert("RGBA"), fade).convert("RGB")

# ===================================================================
# タイトル（左エリア・セーフエリア内）
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

# タイトル基準座標（モバイル表示域 x=251〜1797 内に収める）
# モバイル最小表示: 1546×423 → 左右251pxずつ削れる
TITLE_X = 290
# セーフエリア y=407〜745、中央576
# 2行タイトル(120px×2、行間20)=260px、サブ(36px + margin20)=56px、計316px
# センター合わせ: start = 576 - 316//2 = 418
TITLE_Y_TOP = 418

def text_with_shadow(xy, text, font, fill, off=3):
    x, y = xy
    draw.text((x + off, y + off), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)

text_with_shadow((TITLE_X, TITLE_Y_TOP), "UG競馬", font_big, IVORY)
text_with_shadow((TITLE_X, TITLE_Y_TOP + 140), "ワイド神宮", font_big, KIN)

# 金線
draw.line([(TITLE_X, TITLE_Y_TOP + 275), (TITLE_X + 400, TITLE_Y_TOP + 275)],
          fill=KIN, width=2)

# サブタイトル
text_with_shadow((TITLE_X, TITLE_Y_TOP + 290),
                 "AI神託 × 本格馬券師",
                 font_sub, (244, 228, 184))

# 鳥居マーク（装飾）
def draw_torii(img, cx, cy, w=70, h=80, color=KIN, th=5):
    d2 = ImageDraw.Draw(img)
    d2.rectangle([cx - w // 2 - 8, cy - h // 2, cx + w // 2 + 8, cy - h // 2 + th + 2], fill=color)
    d2.rectangle([cx - w // 2 - 2, cy - h // 2 + th + 5, cx + w // 2 + 2, cy - h // 2 + th * 2 + 5], fill=color)
    d2.rectangle([cx - w // 2 + 4, cy - 3, cx + w // 2 - 4, cy + 3], fill=color)
    d2.rectangle([cx - w // 2, cy - h // 2 + th * 2 + 5, cx - w // 2 + th, cy + h // 2], fill=color)
    d2.rectangle([cx + w // 2 - th, cy - h // 2 + th * 2 + 5, cx + w // 2, cy + h // 2], fill=color)

draw_torii(banner, TITLE_X + 50, TITLE_Y_TOP - 80, w=80, h=95, th=6)

# ===================================================================
# セーフエリア視覚化（確認用・コメントアウト可）
# ===================================================================
DEBUG_SAFE = False
if DEBUG_SAFE:
    d3 = ImageDraw.Draw(banner)
    d3.rectangle([406, 407, 1642, 745], outline=(255, 255, 0), width=3)

banner.save(OUT_DIR / "yt_banner_2048x1152_titled.jpg", quality=92, optimize=True)

# デバッグ用（セーフエリア枠入り）
banner_dbg = banner.copy()
d3 = ImageDraw.Draw(banner_dbg)
d3.rectangle([406, 407, 1642, 745], outline=(255, 230, 0), width=4)
# PC表示域（上下364px削る）
d3.line([(0, 364), (TARGET_W, 364)], fill=(0, 200, 255), width=3)
d3.line([(0, 788), (TARGET_W, 788)], fill=(0, 200, 255), width=3)
banner_dbg.save(OUT_DIR / "yt_banner_2048x1152_debug.jpg", quality=88)

print(f"\n📏 出力結果:")
for f in sorted(OUT_DIR.glob("yt_banner_*.jpg")):
    im = Image.open(f)
    print(f"  {f.name:45s} {im.size[0]}x{im.size[1]}  {f.stat().st_size/1024:.0f}KB")
