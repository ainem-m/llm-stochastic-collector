from typing import Dict, List, Optional, Tuple

class TrieNode:
    def __init__(self, node_id: int, depth: int):
        self.node_id = node_id
        self.depth = depth
        self.children: Dict[str, 'TrieNode'] = {}
        self.counts: Dict[str, int] = {}

class Aggregator:
    def __init__(self):
        self.nodes: List[TrieNode] = []
        self.root = TrieNode(0, 0)
        self.nodes.append(self.root)
        self._next_id = 1

    def load_from_runs(self, runs: List[dict]):
        """
        既存の実行結果（runs）をアグリゲーターに読み込む。
        """
        for run in runs:
            if run.get("status") == "ok":
                self.add_text(run.get("text", ""))

    def add_text(self, text: str):
        current = self.root
        for char in text:
            if char not in current.children:
                new_node = TrieNode(self._next_id, current.depth + 1)
                self._next_id += 1
                current.children[char] = new_node
                self.nodes.append(new_node)
                current.counts[char] = 0
            
            current.counts[char] += 1
            current = current.children[char]

    def get_graph_data(self) -> Tuple[List[dict], List[dict]]:
        nodes_data = [{"id": node.node_id, "depth": node.depth} for node in self.nodes]
        edges_data = []
        for node in self.nodes:
            for char, child in node.children.items():
                edges_data.append({
                    "from": node.node_id,
                    "to": child.node_id,
                    "ch": char,
                    "count": node.counts[char]
                })
        return nodes_data, edges_data

    def calculate_stats(self) -> dict:
        # 簡易的な統計計算の実装
        total_ok = 0 # 外部で管理
        total_error = 0 # 外部で管理
        
        depth_map: Dict[int, List[TrieNode]] = {}
        max_depth = 0
        for node in self.nodes:
            depth_map.setdefault(node.depth, []).append(node)
            if node.depth > max_depth:
                max_depth = node.depth

        depth_stats = []
        import math
        for d in range(max_depth + 1):
            nodes_at_d = depth_map.get(d, [])
            total_transitions = sum(sum(node.counts.values()) for node in nodes_at_d)
            if total_transitions == 0:
                continue
            
            # 各文字の出現回数を集計
            char_counts: Dict[str, int] = {}
            for node in nodes_at_d:
                for char, count in node.counts.items():
                    char_counts[char] = char_counts.get(char, 0) + count
            
            unique_chars = len(char_counts)
            top_chars = sorted(
                [{"ch": ch, "count": cnt, "p": cnt/total_transitions} for ch, cnt in char_counts.items()],
                key=lambda x: x["count"], reverse=True
            )[:5]
            
            entropy = 0.0
            for cnt in char_counts.values():
                p = cnt / total_transitions
                entropy -= p * math.log2(p)
                
            depth_stats.append({
                "depth": d,
                "total_transitions": total_transitions,
                "unique_chars": unique_chars,
                "top_chars": top_chars,
                "entropy_bits": entropy
            })

        return {
            "depth_stats": depth_stats
        }
