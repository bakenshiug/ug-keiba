#!/usr/bin/env python3
"""
YouTubeバナー/アイコン生成 v2（調整版）

修正点:
  - アイコン: 顔アップ(600x600相当の範囲)にズーム
  - バナーV2: キャラを右寄せ、タイトルを左エリアに独立配置、⛩はAppleColorEmojiで合成
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path
import random

SRC = Path("/Users/buntawakase/Desktop/Gemini_Generated_Image_cfntgbcfntgbcfnt.jpeg")
OUT_DIR = Path("/Users/buntawakase/Desktop/ug-keiba/assets/yt")
OUT_DIR.mkdir(parents=True, exist_ok=True)

src = Image.open(SRC).convert("RGB")
W, H = src.size  # 1190x1004
print(f"元画像: {W}x{H}")

# ===================================================================
# 1. アイコン 800x800（顔アップ）
# ===================================================================
# 顔の推定中心: x=W//2=595, y=H*0.22=220 あたり
face_cx = W // 2
face_cy = int(H * 0.25)
side = 700  # 顔周辺700px正方形
left = face_cx - side // 2
top = max(0, face_cy - side // 2)
right = left + side
bot = top + side
if right > W:
    right = W; left = W - side
if bot > H:
    bot = H; top = H - side

icon_sq = src.crop((left, top, right, bot))
icon_800 = icon_sq.resize((800, 800), Image.LANCZOS)

# 朱色の円形フレーム装飾を足す（YouTube円形クロップを意識した外周のみ）
SHU = (155, 45, 48)
KIN = (201, 169, 97)

# 外周に朱色の丸ボーダー風（やや控えめ）
mask = Image.new("L", (800, 800), 0)
mdraw = ImageDraw.Draw(mask)
mdraw.ellipse((0, 0, 800, 800), fill=255)

# 背景を朱に塗りつぶした版を用意し、元画像を円形マスクで重ねる
bg_shu = Image.new("RGB", (800, 800), SHU)
composed = Image.composite(icon_800, bg_shu, mask)

icon_path = OUT_DIR / "yt_icon_800.png"
composed.save(icon_path, optimize=True)
print(f"✅ アイコン: {icon_path.name} ({icon_path.stat().st_size/1024:.0f}KB)")

# 円形マスクなし素版も残す
icon_800.save(OUT_DIR / "yt_icon_800_raw.png", optimize=True)

# ===================================================================
# 2. バナー 2048x1152（中央キャラ＋左右朱グラデ）v1は据え置き
# ===================================================================
TARGET_W, TARGET_H = 2048, 1152
scale = TARGET_H / H
new_h = TARGET_H
new_w = int(W * scale)
char = src.resize((new_w, new_h), Image.LANCZOS)

def build_gradient_bg(w, h, center_mix=0.35):
    """朱色のグラデ＋和紙ノイズ背景"""
    SHU = (155, 45, 48)
    SHU_DK = (95, 22, 22)
    bg = Image.new("RGB", (w, h), SHU_DK)
    d = ImageDraw.Draw(bg)
    for x in range(w):
        r = abs((x / w) - 0.5) * 2
        R = int(SHU[0] * (1 - r * center_mix) + SHU_DK[0] * (r * center_mix))
        G = int(SHU[1] * (1 - r * center_mix) + SHU_DK[1] * (r * center_mix))
        B = int(SHU[2] * (1 - r * center_mix) + SHU_DK[2] * (r * center_mix))
        d.line([(x, 0), (x, h)], fill=(R, G, B))
    noise = Image.new("L", (w // 4, h // 4), 128)
    px = noise.load()
    random.seed(42)
    for y in range(noise.size[1]):
        for xx in range(noise.size[0]):
            px[xx, y] = 128 + random.randint(-10, 10)
    noise = noise.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.8))
    return Image.blend(bg, Image.merge("RGB", (noise, noise, noise)), 0.09)

def paste_with_fade(bg, char_img, x_pos, edge_fade=180):
    """キャラ貼り付け＋左右エッジをbg色にフェード"""
    bg2 = bg.copy()
    bg2.paste(char_img, (x_pos, 0))
    # フェードオーバーレイ
    W_, H_ = bg2.size
    char_w = char_img.size[0]
    fade = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    SHU_DK = (95, 22, 22)
    for i in range(edge_fade):
        alpha = int(255 * (1 - i / edge_fade) ** 1.6)
        fd.line([(x_pos + i, 0), (x_pos + i, H_)],
                fill=(*SHU_DK, alpha))
        fd.line([(x_pos + char_w - i, 0), (x_pos + char_w - i, H_)],
                fill=(*SHU_DK, alpha))
    return Image.alpha_composite(bg2.convert("RGBA"), fade).convert("RGB")

# V1: キャラ中央
bg1 = build_gradient_bg(TARGET_W, TARGET_H)
banner_v1 = paste_with_fade(bg1, char, (TARGET_W - new_w) // 2)
banner_v1.save(OUT_DIR / "yt_banner_2048x1152.jpg", quality=90, optimize=True)

# ===================================================================
# 3. バナーV2: キャラ右寄せ、左にタイトル
# ===================================================================
# キャラを右から200px余白で配置
RIGHT_MARGIN = 180
char_x_v2 = TARGET_W - new_w - RIGHT_MARGIN
bg2 = build_gradient_bg(TARGET_W, TARGET_H)
banner_v2 = paste_with_fade(bg2, char, char_x_v2)

draw = ImageDraw.Draw(banner_v2)

# フォント
font_paths = {
    "mincho": "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
    "sans": "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "emoji": "/System/Library/Fonts/Apple Color Emoji.ttc",
}
try:
    font_main = ImageFont.truetype(font_paths["mincho"], 130)
    font_sub = ImageFont.truetype(font_paths["mincho"], 56)
    font_tag = ImageFont.truetype(font_paths["sans"], 34)
except Exception:
    font_main = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_tag = ImageFont.load_default()

# セーフエリア中央: x=406〜1642, y=407〜745
# 左エリア（キャラと被らない）: x=120〜700 目安
title_x = 150
title_y = 370
KIN = (201, 169, 97)
IVORY = (255, 251, 232)

# 影を軽く（読みやすさup）
def text_with_shadow(xy, text, font, fill, shadow=(0,0,0,160), off=3):
    x, y = xy
    draw.text((x+off, y+off), text, font=font, fill=shadow[:3])
    draw.text((x, y), text, font=font, fill=fill)

text_with_shadow((title_x, title_y), "UG競馬", font_main, IVORY)
text_with_shadow((title_x, title_y + 155), "ワイド神宮", font_main, KIN)

# 区切り装飾（金線）
draw.line([(title_x, title_y + 310), (title_x + 360, title_y + 310)], fill=KIN, width=2)

# サブタイトル
text_with_shadow((title_x, title_y + 330),
                 "AI神託×本格馬券師",
                 font_tag, (244, 228, 184))

# 鳥居マーク（Pillow図形で簡易描画：文字⛩は明朝に無いため）
def draw_torii(img, cx, cy, w=70, h=80, color=KIN, th=6):
    d = ImageDraw.Draw(img)
    # 笠木（上段横棒）
    d.rectangle([cx - w // 2 - 8, cy - h // 2, cx + w // 2 + 8, cy - h // 2 + th + 2], fill=color)
    # 島木（下段横棒）
    d.rectangle([cx - w // 2 - 2, cy - h // 2 + th + 6, cx + w // 2 + 2, cy - h // 2 + th * 2 + 6], fill=color)
    # 貫（中段）
    d.rectangle([cx - w // 2 + 4, cy - 5, cx + w // 2 - 4, cy + 5], fill=color)
    # 左柱
    d.rectangle([cx - w // 2, cy - h // 2 + th * 2 + 6, cx - w // 2 + th, cy + h // 2], fill=color)
    # 右柱
    d.rectangle([cx + w // 2 - th, cy - h // 2 + th * 2 + 6, cx + w // 2, cy + h // 2], fill=color)

draw_torii(banner_v2, title_x + 45, title_y - 70, w=80, h=90, th=7)

banner_v2.save(OUT_DIR / "yt_banner_2048x1152_titled.jpg", quality=92, optimize=True)

print(f"\n📏 最終チェック:")
for f in sorted(OUT_DIR.iterdir()):
    if f.is_file():
        im = Image.open(f)
        print(f"  {f.name:40s} {im.size[0]}x{im.size[1]}  {f.stat().st_size/1024:.0f}KB")
