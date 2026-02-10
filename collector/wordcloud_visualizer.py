import json
import os
import argparse
from collections import Counter
from typing import Dict, Any
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def generate_wordcloud(data: Dict[str, Any], output_path: str, font_path: str = None):
    """
    JSONデータから生成されたテキストの頻度を集計し、ワードクラウドを生成する。
    """
    runs = data.get("runs", [])
    texts = [run.get("text", "") for run in runs if run.get("status") == "ok"]
    
    if not texts:
        print("No successful runs found to generate word cloud.")
        return None

    # テキストの頻度を集計
    counts = Counter(texts)
    
    # ワードクラウドの設定
    # MacOSの標準的なフォントパスをデフォルト候補とする
    if not font_path:
        # 一般的なMacの日本語フォントパス
        possible_fonts = [
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
        ]
        for f in possible_fonts:
            if os.path.exists(f):
                font_path = f
                break

    wc = WordCloud(
        width=800, 
        height=400, 
        background_color="white",
        font_path=font_path,
        prefer_horizontal=0.9
    )
    
    # 頻度から生成
    wc.generate_from_frequencies(counts)
    
    # 保存
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    
    # 拡張子がなければ追加
    if not output_path.lower().endswith(".png"):
        output_path += ".png"
        
    plt.savefig(output_path)
    plt.close()
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Word Cloud from Collector JSON")
    parser.add_argument("--input", required=True, help="Path to the input JSON file")
    parser.add_argument("--out", default="wordcloud_output", help="Output filename (base)")
    parser.add_argument("--font", help="Path to a Japanese font file (.ttc or .ttf)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        exit(1)
        
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    path = generate_wordcloud(data, args.out, args.font)
    if path:
        print(f"Word cloud saved to {path}")
