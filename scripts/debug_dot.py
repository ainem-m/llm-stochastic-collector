import json
import graphviz
from typing import Dict, Any

def get_dot_source(data: Dict[str, Any]):
    dot = graphviz.Digraph(comment='Char-Graph Visualization', format='png')
    dot.attr(rankdir='LR')
    
    graph = data.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    for node in nodes:
        node_id = str(node["id"])
        dot.node(node_id, label=node_id)
        
    max_count = max([e["count"] for e in edges]) if edges else 1
    for edge in edges:
        from_id = str(edge["from"])
        to_id = str(edge["to"])
        label = edge["ch"].replace("\n", "\\n").replace("\r", "\\r")
        count = edge["count"]
        penwidth = str(max(1, (count / max_count) * 5))
        dot.edge(from_id, to_id, label=f"{label} ({count})", penwidth=penwidth)
    return dot.source

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    print(get_dot_source(data))
