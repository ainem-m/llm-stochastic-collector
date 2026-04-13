import json
import argparse
import math
import graphviz
from typing import Dict, Any, List

def sanitize_label(text: str) -> str:
    """Graphvizでのクラッシュを防ぐために特殊文字をサニタイズする"""
    if not text:
        return ""
    # 非BMP文字 (絵文字など) を '?' に置換
    sanitized = "".join([c if ord(c) <= 0xFFFF else "?" for c in text])
    # Graphviz用のエスケープ
    return sanitized.replace("\n", "\\n").replace("\r", "\\r").replace('"', '\\"')

def generate_logprobs_graph(run_data: Dict[str, Any], output_path: str, fmt: str = "png", max_candidates: int = 5):
    dot = graphviz.Digraph(comment='Logprobs Visualization', format=fmt)
    dot.attr(rankdir='LR')
    
    # 開始ノード
    dot.node("start", label="START", shape="doublecircle")
    
    current_node_id = "start"
    logprobs_list = run_data.get("logprobs", [])
    
    if not logprobs_list:
        print("No logprobs found in the specified run.")
        return

    for i, step in enumerate(logprobs_list):
        # メイントークン（選ばれたもの）
        chosen_token = step.get("token", "")
        chosen_logprob = step.get("logprob", 0.0)
        chosen_prob = math.exp(chosen_logprob) * 100
        
        step_id = f"step_{i}"
        
        # 候補（Top Logprobs）の描画
        top_logprobs = step.get("top_logprobs", [])
        
        # 候補を描画（選ばれたもの以外）
        for rank, candidate in enumerate(top_logprobs[:max_candidates]):
            cand_token = candidate.get("token", "")
            cand_logprob = candidate.get("logprob", 0.0)
            cand_prob = math.exp(cand_logprob) * 100
            
            is_chosen = (cand_token == chosen_token)
            
            label_text = sanitize_label(cand_token)
            if not label_text.strip():
                 label_text = "(space)" if label_text == " " else repr(cand_token)

            edge_label = f"{label_text}\n{cand_prob:.1f}%"
            
            # メインストリームへのパス（実線）
            if is_chosen:
                # 次のノードを作成
                next_node_id = f"node_{i+1}"
                # 最終ステップの場合は終了っぽくする？いや、単に繋いでいく
                dot.node(next_node_id, label=str(i+1), shape="circle")
                
                dot.edge(current_node_id, next_node_id, label=edge_label, penwidth="2.0", color="blue")
                current_node_id = next_node_id # 次のステップの親になる
            else:
                # 枝分かれ（点線）
                # 枝分かれ先は終端ノード（リーフ）として描画
                alt_node_id = f"alt_{i}_{rank}"
                dot.node(alt_node_id, label="", shape="point", width="0.1")
                dot.edge(current_node_id, alt_node_id, label=edge_label, style="dotted", color="gray", fontsize="10")

    dot.render(output_path, cleanup=True)
    return f"{output_path}.{fmt}"

def main():
    parser = argparse.ArgumentParser(description="Visualize Logprobs from Collector Output")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--run-index", type=int, default=0, help="Index of the run to visualize (default: 0)")
    parser.add_argument("--out", default="logprobs_graph", help="Output filename base")
    parser.add_argument("--format", choices=["png", "svg"], default="png", help="Output format")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top candidates to show")

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    runs = data.get("runs", [])
    if not runs:
        print("No runs found in JSON.")
        return

    if args.run_index >= len(runs):
        print(f"Error: run-index {args.run_index} out of range (total {len(runs)} runs).")
        return

    target_run = runs[args.run_index]
    print(f"Visualizing Run ID: {target_run.get('id')} (Text: {target_run.get('text')[:20]}...)")

    output_file = generate_logprobs_graph(target_run, args.out, args.format, args.top_k)
    print(f"Graph generated: {output_file}")

if __name__ == "__main__":
    main()
