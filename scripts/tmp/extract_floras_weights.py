#!/usr/bin/env python3
"""
フローラS 16頭分のJRDB txt から前走馬体重を抽出
出力: {"horseName": {"prev1_weight": 410, "prev1_delta": -6, "prev2_weight": 416, ...}}
"""
import re
import json
from pathlib import Path

TXT_DIR = Path("/Users/buntawakase/Desktop/ug-keiba/analysis/2026-04-26-floras/txt-extracted")

# パターン: JRDB過去走テーブルの「体重 増減 [漢字1文字]」
# 体重3桁(380-560) + 増減(-99〜+99 or --) + 漢字1文字（馬場状態or誤認）
# 先行数字は直前に数字/小数点がないことで誤爆防止
WEIGHT_PAT = re.compile(r'(?<![\d.])(\d{3})\s+(-?\d{1,2}|--)\s+([\u4E00-\u9FFF])', re.MULTILINE)

def extract(txt_path):
    content = txt_path.read_text(encoding='utf-8')
    weights = []
    seen = set()  # 同じ位置の重複防止
    for m in WEIGHT_PAT.finditer(content):
        w = int(m.group(1))
        if 380 <= w <= 560:
            delta = None if m.group(2) == '--' else int(m.group(2))
            key = (m.start(), w)
            if key in seen:
                continue
            seen.add(key)
            weights.append({'weight': w, 'delta': delta, 'cond_raw': m.group(3)})
    return weights

def main():
    results = {}
    for txt_file in sorted(TXT_DIR.glob("*.txt")):
        name = txt_file.stem
        weights = extract(txt_file)
        results[name] = weights
        prev1 = weights[0] if weights else None
        prev1_str = f"{prev1['weight']}kg({prev1['delta']:+d})" if prev1 and prev1['delta'] is not None else (f"{prev1['weight']}kg(—)" if prev1 else "—")
        small_flag = "🔴小柄" if prev1 and prev1['weight'] <= 420 else ""
        print(f"  {name:20s} 前走:{prev1_str} {small_flag}  (全{len(weights)}走検出)")
    # 保存
    out_path = Path("/Users/buntawakase/Desktop/ug-keiba/scripts/tmp/floras_weights.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n保存: {out_path}")

if __name__ == "__main__":
    main()
