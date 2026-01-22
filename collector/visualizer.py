import json
import os
from typing import Dict, Any
import graphviz

def generate_mermaid(data: Dict[str, Any]) -> str:
    """JSONデータからMermaid形式のグラフ文字列を生成する"""
    lines = ["graph LR"]
    
    # 実際にはノード名はprefixを表示したい場合もあるが、まずはIDベースで簡潔に
    # graph.edgesを使う
    graph = data.get("graph", {})
    edges = graph.get("edges", [])
    
    for edge in edges:
        from_id = edge["from"]
        to_id = edge["to"]
        label = edge["ch"]
        count = edge["count"]
        
        label = edge["ch"].replace("\n", "\\n").replace("\r", "\\r")
        if label == " ":
            label = "(space)"
            
        # Mermaid形式: from_id -- "char (count)" --> to_id
        lines.append(f'    node{from_id} -- "{label} ({count})" --> node{to_id}')
        
    return "\n".join(lines)

def generate_graphviz(data: Dict[str, Any], output_path: str = "graph", fmt: str = "png"):
    """JSONデータからGraphvizを使用してグラフ画像を生成する"""
    dot = graphviz.Digraph(comment='Char-Graph Visualization', format=fmt)
    dot.attr(rankdir='LR')
    
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    # ノード追加
    for node in nodes:
        node_id = str(node["id"])
        dot.node(node_id, label=node_id)
        
    # エッジ追加
    max_count = max([e["count"] for e in edges]) if edges else 1
    
    for edge in edges:
        from_id = str(edge["from"])
        to_id = str(edge["to"])
        count = edge["count"]
        
        # 特殊文字（特に絵文字など）が dot -Tpng をクラッシュさせることがあるためサニタイズ
        # 非BMP文字 (絵文字など) を '?' に置換
        raw_ch = edge["ch"]
        sanitized_ch = "".join([c if ord(c) <= 0xFFFF else "?" for c in raw_ch])
        
        label = sanitized_ch.replace("\n", "\\n").replace("\r", "\\r")
        if label == " ":
            label = "(space)"
            
        # 太さを出現頻度に比例させる
        penwidth = str(max(1, (count / max_count) * 5))
        
        dot.edge(from_id, to_id, label=f"{label} ({count})", penwidth=penwidth)
        
    dot.render(output_path, cleanup=True)
    return f"{output_path}.{fmt}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualize Char-Graph JSON")
    parser.add_argument("--input", required=True, help="Path to the input JSON file")
    parser.add_argument("--format", choices=["mermaid", "png", "svg"], default="png", help="Output format")
    parser.add_argument("--out", default="graph_output", help="Output filename (base)")
    
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if args.format == "mermaid":
        print(generate_mermaid(data))
    else:
        path = generate_graphviz(data, args.out, args.format)
        print(f"Graph rendered to {path}")
