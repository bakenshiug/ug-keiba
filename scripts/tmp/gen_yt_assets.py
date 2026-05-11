#!/usr/bin/env python3
"""
YouTubeバナー/アイコン生成スクリプト（試作版）

元素材: /Users/buntawakase/Desktop/Gemini_Generated_Image_cfntgbcfntgbcfnt.jpeg (1190x1004)
出力先: /Users/buntawakase/Desktop/ug-keiba/assets/yt/

- yt_icon_800.png           : YouTubeアイコン用 800x800 正方形
- yt_banner_2048x1152.jpg   : YouTubeバナー用 2048x1152（16:9横長）シンプル版
- yt_banner_2048x1152_v2.jpg: バナー タイトル入り案
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path

SRC = Path("/Users/buntawakase/Desktop/Gemini_Generated_Image_cfntgbcfntgbcfnt.jpeg")
OUT_DIR = Path("/Users/buntawakase/Desktop/ug-keiba/assets/yt")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ===================================================================
# 1. アイコン 800x800（中央正方形クロップ → 800x800）
# ===================================================================
src = Image.open(SRC).convert("RGB")
w, h = src.size  # 1190x1004
print(f"元画像: {w}x{h}")

# 中央正方形クロップ（1004x1004）→ 顔中心寄りに少し上にシフト
side = min(w, h)  # 1004
cx = w // 2       # 595
cy = int(h * 0.46)  # 上寄り（顔にフォーカス）
top = max(0, cy - side // 2)
bot = top + side
if bot > h:
    bot = h
    top = h - side
left = max(0, cx - side // 2)
right = left + side
if right > w:
    right = w
    left = w - side

icon_sq = src.crop((left, top, right, bot))
icon_800 = icon_sq.resize((800, 800), Image.LANCZOS)

# 円形境界を意識した軽い周辺フェードは追加しない（YouTube側で自動円形クロップ）
icon_path = OUT_DIR / "yt_icon_800.png"
icon_800.save(icon_path, optimize=True)
print(f"✅ アイコン: {icon_path.name} ({icon_path.stat().st_size/1024:.0f}KB)")

# ===================================================================
# 2. バナー 2048x1152（中央キャラ＋朱グラデ左右拡張）
# ===================================================================
# 目標: 2048x1152 (16:9)
TARGET_W, TARGET_H = 2048, 1152

# キャラ画像を縦1152に合わせてリサイズ（元1190x1004 → scale h→1152）
scale = TARGET_H / h
new_h = TARGET_H
new_w = int(w * scale)  # 1365くらい
char = src.resize((new_w, new_h), Image.LANCZOS)

# 朱色グラデ背景（左→中央→右）を作成
SHU = (155, 45, 48)        # --shu
SHU_DK = (95, 22, 22)      # 深い朱
SUMI = (26, 26, 26)        # --sumi

banner = Image.new("RGB", (TARGET_W, TARGET_H), SHU_DK)
draw = ImageDraw.Draw(banner)

# 左右グラデ（SHU_DK → SHU → SHU_DK）
for x in range(TARGET_W):
    ratio = abs((x / TARGET_W) - 0.5) * 2  # 0(中央)〜1(端)
    r = int(SHU[0] * (1 - ratio * 0.65) + SHU_DK[0] * (ratio * 0.65))
    g = int(SHU[1] * (1 - ratio * 0.65) + SHU_DK[1] * (ratio * 0.65))
    b = int(SHU[2] * (1 - ratio * 0.65) + SHU_DK[2] * (ratio * 0.65))
    draw.line([(x, 0), (x, TARGET_H)], fill=(r, g, b))

# 和紙風ノイズ（薄い）
import random
noise = Image.new("L", (TARGET_W // 4, TARGET_H // 4), 128)
pix = noise.load()
random.seed(42)
for y in range(noise.size[1]):
    for x in range(noise.size[0]):
        pix[x, y] = 128 + random.randint(-8, 8)
noise = noise.resize((TARGET_W, TARGET_H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.5))
banner = Image.blend(banner, Image.merge("RGB", (noise, noise, noise)), 0.08)

# キャラを中央に合成（元JPEGの背景は使わず、キャラ部分をマスク...できないのでそのまま中央貼り付け）
# 元画像は背景込みなので、中央に貼ると神社背景も見える（これはこれで神宮感）
char_x = (TARGET_W - new_w) // 2
banner.paste(char, (char_x, 0))

# 左右端に朱色グラデを重ねて馴染ませる（フェード）
fade = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
fade_draw = ImageDraw.Draw(fade)
edge_width = 200
for i in range(edge_width):
    alpha = int(255 * (1 - i / edge_width))
    # 左
    fade_draw.line([(char_x + i, 0), (char_x + i, TARGET_H)],
                   fill=(SHU_DK[0], SHU_DK[1], SHU_DK[2], alpha))
    # 右
    fade_draw.line([(char_x + new_w - i, 0), (char_x + new_w - i, TARGET_H)],
                   fill=(SHU_DK[0], SHU_DK[1], SHU_DK[2], alpha))
banner = Image.alpha_composite(banner.convert("RGBA"), fade).convert("RGB")

banner.save(OUT_DIR / "yt_banner_2048x1152.jpg", quality=90, optimize=True)
print(f"✅ バナー: yt_banner_2048x1152.jpg ({(OUT_DIR / 'yt_banner_2048x1152.jpg').stat().st_size/1024:.0f}KB)")

# ===================================================================
# 3. バナー タイトル入り案（左側にタイトル配置）
# ===================================================================
banner_v2 = banner.copy()
draw2 = ImageDraw.Draw(banner_v2)

# フォント探索
font_candidates = [
    "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
    "/System/Library/Fonts/Supplemental/HiraginoSerif.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]
font_big = None
font_small = None
for fp in font_candidates:
    try:
        font_big = ImageFont.truetype(fp, 100)
        font_small = ImageFont.truetype(fp, 36)
        print(f"  フォント使用: {fp}")
        break
    except Exception:
        continue

if font_big:
    KIN = (201, 169, 97)
    # 左側エリアに縦書き風（横組）タイトル
    # セーフエリア中央は x=406〜1642, y=407〜745
    # タイトルは左オフセット
    title_x = 160
    title_y = 430
    draw2.text((title_x, title_y), "⛩ UG競馬", font=font_big, fill="#fffbe8")
    draw2.text((title_x, title_y + 120), "ワイド神宮", font=font_big, fill=KIN)
    draw2.text((title_x, title_y + 265), "AI神託×本格馬券師", font=font_small, fill="#f4e4b8")

banner_v2.save(OUT_DIR / "yt_banner_2048x1152_titled.jpg", quality=90, optimize=True)
print(f"✅ バナーV2: yt_banner_2048x1152_titled.jpg ({(OUT_DIR / 'yt_banner_2048x1152_titled.jpg').stat().st_size/1024:.0f}KB)")

print("\n📏 最終チェック:")
for f in sorted(OUT_DIR.iterdir()):
    if f.is_file():
        im = Image.open(f)
        print(f"  {f.name:40s} {im.size[0]}x{im.size[1]}  {f.stat().st_size/1024:.0f}KB")
