import json
import sys
import os
from collector.aggregator import Aggregator
from collector.serializer import CollectorOutput

def compress_existing_json(input_path, output_path, use_bpe=False, vocab_size=1000):
    print(f"Loading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Pydanticモデルを介して検証しつつロード
    output_obj = CollectorOutput(**data)
    
    aggregator = Aggregator()
    if use_bpe:
        from collector.bpe_manager import BPEManager
        print(f"Training custom BPE (vocab_size={vocab_size})...")
        texts = [r.text for r in output_obj.runs if r.status == "ok"]
        bpe = BPEManager(vocab_size=vocab_size)
        bpe.train(texts)
        print("Building token-level Trie...")
        for text in texts:
            tokens = bpe.tokenize(text)
            aggregator.add_tokens(tokens)
    else:
        print("Building character-level Trie and compressing paths...")
        runs_data = [r.model_dump() for r in output_obj.runs]
        aggregator.load_from_runs(runs_data)
    
    # パス圧縮を適用 (BPEの場合も分岐があればさらに圧縮可能)
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSON path")
    parser.add_argument("output", help="Output JSON path")
    parser.add_argument("--bpe", action="store_true", help="Use custom BPE compression")
    parser.add_argument("--vocab", type=int, default=1000, help="BPE vocabulary size")
    args = parser.parse_args()

    compress_existing_json(args.input, args.output, use_bpe=args.bpe, vocab_size=args.vocab)
