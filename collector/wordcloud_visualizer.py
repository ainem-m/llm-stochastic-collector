import json
import os
import math
import random
import argparse
from collections import Counter
from typing import Dict, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# カラーパレット
NEON_COLORS = ['#00FFAB', '#00D4FF', '#FF6EC7', '#FFD700', '#B388FF', '#64FFDA', '#FF8A65']
COOL_COLORS = ['#4dd0e1', '#4fc3f7', '#81d4fa', '#b39ddb', '#ce93d8', '#64ffda', '#80cbc4']
WARM_COLORS = ['#ff7043', '#ffa726', '#ffca28', '#ffee58', '#ef5350', '#ec407a', '#ab47bc']

PALETTES = {
    "neon": NEON_COLORS,
    "cool": COOL_COLORS,
    "warm": WARM_COLORS,
}

BG_DARK = "#1a1a2e"
BG_WHITE = "#ffffff"


def _make_color_func(palette_name: str = "neon"):
    """指定パレットからランダムに色を返すカラー関数を作成"""
    colors = PALETTES.get(palette_name, NEON_COLORS)
    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return random.choice(colors)
    return color_func


def _make_circle_mask(size: int) -> np.ndarray:
    """中央に密集させるための円形マスクを生成（numpy vectorized）"""
    y, x = np.ogrid[:size, :size]
    cx, cy = size // 2, size // 2
    r = size // 2 - 10
    dist = (x - cx) ** 2 + (y - cy) ** 2
    mask = np.where(dist <= r ** 2, 0, 255).astype(np.uint8)
    return mask


def generate_wordcloud(
    data: Dict[str, Any],
    output_path: str,
    font_path: Optional[str] = None,
    dark: bool = True,
    palette: str = "neon",
    show_counts: bool = False,
    scale: str = "log",
):
    """
    JSONデータから生成されたテキストの頻度を集計し、ワードクラウドを生成する。

    Args:
        data: CollectorのJSON出力
        output_path: 出力画像パス
        font_path: 日本語フォントパス
        dark: ダークテーマ (True) / ライトテーマ (False)
        palette: カラーパレット名 ("neon", "cool", "warm")
        show_counts: テキストに出現回数を付与するか
        scale: 頻度のスケーリング ("raw", "log", "sqrt")
    """
    runs = data.get("runs", [])
    texts = [run.get("text", "") for run in runs if run.get("status") == "ok"]

    if not texts:
        print("No successful runs found to generate word cloud.")
        return None

    # テキストの頻度を集計
    raw_counts = Counter(texts)

    # スケーリング（頻出語と稀少語のサイズ差を緩和）
    if scale == "log":
        counts = {k: math.log1p(v) for k, v in raw_counts.items()}
    elif scale == "sqrt":
        counts = {k: math.sqrt(v) for k, v in raw_counts.items()}
    else:
        counts = dict(raw_counts)

    # 出現回数をラベルに付与
    if show_counts:
        counts = {f"{k}({raw_counts[k]})": v for k, v in counts.items()}

    # フォント自動検出
    if not font_path:
        possible_fonts = [
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        ]
        for f in possible_fonts:
            if os.path.exists(f):
                font_path = f
                break

    bg_color = BG_DARK if dark else BG_WHITE

    # 円形マスク（中央密集レイアウト）
    mask = _make_circle_mask(1600)

    wc = WordCloud(
        width=1600,
        height=1600,
        background_color=bg_color,
        font_path=font_path,
        prefer_horizontal=0.5,      # 斜め・縦書きも混ぜる
        relative_scaling=0.5,
        max_words=100,
        margin=6,
        color_func=_make_color_func(palette),
        max_font_size=300,
        min_font_size=16,
        mask=mask,
        contour_width=0,
    )

    wc.generate_from_frequencies(counts)

    # 保存
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.patch.set_facecolor(bg_color)
    plt.tight_layout(pad=0)

    if not output_path.lower().endswith(".png"):
        output_path += ".png"

    plt.savefig(output_path, dpi=150, facecolor=bg_color, bbox_inches="tight")
    plt.close()

    # テキスト集計結果を .txt で保存
    txt_path = output_path.rsplit(".", 1)[0] + ".txt"
    total = sum(raw_counts.values())
    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write(f"Total runs: {total}\n")
        tf.write(f"Unique texts: {len(raw_counts)}\n")
        tf.write("-" * 40 + "\n")
        for text, count in raw_counts.most_common():
            pct = count / total * 100
            tf.write(f"{count:>8d}  ({pct:5.1f}%)  {text}\n")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Word Cloud from Collector JSON")
    parser.add_argument("--input", required=True, help="Path to the input JSON file")
    parser.add_argument("--out", default="wordcloud_output", help="Output filename (base)")
    parser.add_argument("--font", help="Path to a Japanese font file (.ttc or .ttf)")
    parser.add_argument("--light", action="store_true", help="Use light (white) background")
    parser.add_argument("--palette", choices=["neon", "cool", "warm"], default="neon",
                        help="Color palette (default: neon)")
    parser.add_argument("--counts", action="store_true", help="Show counts in labels")
    parser.add_argument("--scale", choices=["raw", "log", "sqrt"], default="log",
                        help="Frequency scaling (default: log)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    path = generate_wordcloud(
        data, args.out,
        font_path=args.font,
        dark=not args.light,
        palette=args.palette,
        show_counts=args.counts,
        scale=args.scale,
    )
    if path:
        print(f"Word cloud saved to {path}")
