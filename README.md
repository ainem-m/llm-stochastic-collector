# LLM Stochastic Output Collector (Char-Graph)

## 概要
LLMが「確率的にテキストを生成している」ことを、**同一プロンプトをN回実行**して可視化するための実験用コレクタ。
各生成結果（テキスト）を保存し、同時に**文字単位の遷移グラフ（prefix tree / trie）**として集計します。

- **目的**: 記事用の実験データ作成（高並列・文字単位集計）
- **モデル**: `gpt-4.1-mini` (デフォルト) / その他OpenAI Chatモデル
- **実装**: Python 3.12+ (uv管理)
- **出力**: JSON（生データ + 文字遷移グラフ + 統計）

## 主要機能
- 単一プロンプトのN回繰り返し実行（並列制御可能）
- 文字単位の遷移グラフ（Trie）構築
- 深さ別の統計（エントロピー、出現頻度など）の自動計算
- 失敗（429等）時のリトライ管理

## クイックスタート

### 準備
1. `uv` がインストールされていることを確認してください。
2. OpenAI APIキーを環境変数に設定します。
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

### 実行
```bash
# 基本的な実行 (10回実行、並列数5)
uv run python -m collector --prompt "北海道の県庁所在地は札幌である。YES or NO?" --n 10 --concurrency 5

# 詳細設定 (モデル指定、出力先指定)
uv run python -m collector \
  --prompt "北海道の県庁所在地は札幌である。YES or NO?" \
  --n 50 \
  --concurrency 10 \
  --model gpt-4o-mini \
  --out out/result.json
```

## 引数詳細
- `--prompt`: 推論を実行するプロンプト（必須）
- `--n`: 試行回数（デフォルト: 10）
- `--concurrency`: 同時並列数（デフォルト: 5）
- `--model`: 使用するモデル名（デフォルト: gpt-4.1-mini）
- `--out`: 出力ファイルのパス（デフォルト: `out/run-YYYYMMDD-HHMMSS.json`）
- `--temp`: Temperature（デフォルト: 1.0）
- `--max_tokens`: 最大出力トークン数（デフォルト: 50）

## 出力ファイル構造
```json
{
  "meta": { "run_id": "...", "created_at": "..." },
  "config": { "prompt": "...", "n": 50, ... },
  "runs": [
    { "id": 0, "text": "YES", "usage": { ... }, "status": "ok" },
    ...
  ],
  "graph": {
    "nodes": [ { "id": 0, "depth": 0 }, ... ],
    "edges": [ { "from": 0, "to": 1, "ch": "Y", "count": 50 }, ... ]
  },
  "stats": {
    "totals": { "ok": 50, "error": 0, "total_chars": 150 },
    "depth_stats": [ ... ]
  }
}
```

## 参考（OpenAI Docs）
- [Responses API](https://platform.openai.com/docs/api-reference/responses)
- [gpt-4.1-mini](https://platform.openai.com/docs/models/gpt-4.1-mini)
- [Rate limits](https://platform.openai.com/docs/guides/rate-limits)
