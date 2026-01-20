# LLM Stochastic Output Collector (Char-Graph)

## 概要
LLMが「確率的にテキストを生成している」ことを、**同一プロンプトをN回実行**して可視化するための実験用コレクタ。
各生成結果（テキスト）を保存し、同時に**文字単位の遷移グラフ（prefix tree / trie）**として集計します。

- **目的**: 記事用の実験データ作成（高並列・文字単位集計）
- **モデル**: `gpt-4.1-mini` (デフォルト) / その他OpenAI Chatモデル
- **実装**: Python 3.12+ (uv管理)
- **GitHub**: [ainem-m/llm-stochastic-collector](https://github.com/ainem-m/llm-stochastic-collector)

## 主要機能
- 単一プロンプトのN回繰り返し実行（並列制御可能）
- 文字単位の遷移グラフ（Trie）構築
- 深さ別の統計（エントロピー、出現頻度など）の自動計算
- **デバッグモード**: `logprobs` を収集し、トークンごとの詳細な確率分布を記録
- **レジューム機能**: プロンプトのハッシュ化により、中断された実行を再開したり試行回数を追加可能
- **チェックポイント**: 大規模な実行時、一定間隔ごとに中間結果を保存
- **パス圧縮 (Radix Tree)**: 分岐のない連続した文字の並びを一つのエッジ（文字列）にまとめ、可読性を向上
- **可視化**: 収集したデータをMermaid形式やGraphviz (PNG) でグラフ化する機能

## クイックスタート

### 準備
1. `uv` がインストールされていることを確認してください。
2. OpenAI APIキーを環境変数に設定します。
3. 可視化(PNG)を利用する場合は `brew install graphviz` が必要です。

### 実行
```bash
# 基本的な実行 (10回実行、並列数5)
uv run python -m collector --prompt "Hi" --n 10

# パス圧縮を有効にして実行 (グラフが整理された状態で保存されます)
uv run python -m collector --prompt "Hi" --n 10 --compress

# デバッグモード (logprobsを収集)
uv run python -m collector --prompt "Hi" --n 10 --debug
```

### 既存ファイルの整理
過去に取得したJSONファイルを後からパス圧縮して整理することも可能です。
```bash
PYTHONPATH=. uv run python scripts/compress_json.py input.json output.json
```

### 可視化
```bash
# Mermaid形式で出力
uv run python -m collector.visualizer --input out/run-xxx.json

# GraphvizでPNG画像を生成
uv run python -m collector.visualizer --input out/run-xxx.json --format png
```

## 引数詳細
- `--prompt`: 推論を実行するプロンプト（必須）
- `--n`: 試行回数（デフォルト: 10）
- `--concurrency`: 同時並列数（デフォルト: 5）
- `--model`: 使用するモデル名（デフォルト: gpt-4.1-mini）
- `--out`: 出力ファイルのパス（デフォルト: `out/run-YYYYMMDD-HHMMSS-{hash}.json`）
- `--temp`: Temperature（デフォルト: 1.0）
- `--max_tokens`: 最大出力トークン数（デフォルト: 50）
- `--debug`: デバッグモードを有効にし、`logprobs` を収集
- `--compress`: グラフのパス圧縮（Radix Tree）を有効化
- `--format`: (visualizerのみ) 出力形式。`mermaid` (デフォルト) または `png`

## 出力ファイル構造
```json
{
  "meta": { "run_id": "...", "created_at": "...", "notes": "Checkpoint/null" },
  "config": { "prompt": "...", "n": 50, ... },
  "runs": [
    { 
      "id": 0, 
      "text": "YES", 
      "status": "ok",
      "logprobs": [ { "token": "YES", "logprob": -0.01, "top_logprobs": [...] } ]
    },
    ...
  ],
  "graph": {
    "nodes": [ ... ],
    "edges": [ { "from": 0, "to": 1, "ch": "YES", "count": 50 }, ... ]
  },
  "stats": { ... }
}
```

## 参考（OpenAI Docs）
- [Responses API (logprobs)](https://platform.openai.com/docs/api-reference/chat/create#chat-create-logprobs)
- [gpt-4.1-mini](https://platform.openai.com/docs/models/gpt-4.1-mini)
