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

    def add_tokens(self, tokens: List[str]):
        """トークンのリストをアグリゲーターに追加する"""
        current = self.root
        for token in tokens:
            if token not in current.children:
                new_node = TrieNode(self._next_id, current.depth + 1)
                self._next_id += 1
                current.children[token] = new_node
                self.nodes.append(new_node)
                current.counts[token] = 0
            
            current.counts[token] += 1
            current = current.children[token]

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

    def get_compressed_graph_data(self) -> Tuple[List[dict], List[dict]]:
        """
        パス圧縮（Radix Tree）を適用したグラフデータを返す。
        分岐のない連続したノードを統合する。
        """
        compressed_nodes = []
        compressed_edges = []
        
        # 訪問済みノードセット（統合後のルート候補として管理）
        # 基本的に root から開始
        stack = [(self.root, self.root.node_id)]
        visited_nodes = {self.root.node_id}
        compressed_nodes.append({"id": self.root.node_id, "depth": self.root.depth})

        while stack:
            curr_node, curr_compressed_id = stack.pop()
            
            for char, child in curr_node.children.items():
                edge_label = char
                edge_count = curr_node.counts[char]
                next_node = child
                
                # 直収（子が1つだけで、かつその子への流入が出口と同じ）の間、圧縮を続ける
                # ただし、元の Trie なので child への流入は 1箇所のみであることが保証されている
                while len(next_node.children) == 1:
                    # 子ノードの唯一の遷移先を取得
                    next_char, nn = list(next_node.children.items())[0]
                    # もし next_node のカウントと nn へのカウントが同じ（漏れがない）なら圧縮
                    if next_node.counts[next_char] == edge_count:
                        edge_label += next_char
                        next_node = nn
                    else:
                        break
                
                # 新しいノードを登録（もしまだなら）
                if next_node.node_id not in visited_nodes:
                    compressed_nodes.append({"id": next_node.node_id, "depth": next_node.depth})
                    visited_nodes.add(next_node.node_id)
                    stack.append((next_node, next_node.node_id))
                
                compressed_edges.append({
                    "from": curr_compressed_id,
                    "to": next_node.node_id,
                    "ch": edge_label,
                    "count": edge_count
                })
                
        return compressed_nodes, compressed_edges

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
