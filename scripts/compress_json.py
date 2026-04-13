import json
import sys
import os
from collector.aggregator import Aggregator
from collector.serializer import CollectorOutput

def compress_existing_json(input_path, output_path):
    print(f"Loading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Pydanticモデルを介して検証しつつロード
    output_obj = CollectorOutput(**data)
    
    print("Building Trie and compressing paths...")
    aggregator = Aggregator()
    # 成功した実行結果のみをロード
    runs_data = [r.model_dump() for r in output_obj.runs]
    aggregator.load_from_runs(runs_data)
    
    # パス圧縮を適用
    new_nodes, new_edges = aggregator.get_compressed_graph_data()
    
    print(f"Original edges: {len(data['graph']['edges'])}")
    print(f"Compressed edges: {len(new_edges)}")
    
    # データを更新
    data["graph"]["nodes"] = new_nodes
    data["graph"]["edges"] = new_edges
    
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved compressed JSON to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compress_json.py <input.json> <output.json>")
        sys.exit(1)
    compress_existing_json(sys.argv[1], sys.argv[2])
