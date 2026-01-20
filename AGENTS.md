# AGENTS.md

このファイルは、AIコーディングアシスタントがこのプロジェクトを理解し、効果的に支援するための情報を提供します。

## プロジェクト概要
**LLM Stochastic Output Collector (Char-Graph)** は、LLMの確率的テキスト生成を可視化するための実験用コレクタです。同一プロンプトを最大10,000回実行し、文字単位の遷移グラフ（trie）として集計します。

## 技術スタック
- **言語**: Python 3.12+
- **パッケージ管理**: uv
- **API**: OpenAI Responses API
- **モデル**: gpt-4.1-mini
- **非同期処理**: AsyncOpenAI + asyncio

## ディレクトリ構造
```
prompt_multiple/
├── README.md           # プロジェクト概要
├── AGENTS.md           # このファイル（AI向けガイド）
├── docs/
│   ├── requirements.md     # 要件定義
│   ├── design.md           # 設計ドキュメント
│   ├── data_schema.md      # 出力JSONスキーマ
│   ├── experiment_protocol.md  # 実験プロトコル
│   ├── runbook.md          # 実行・運用メモ
│   └── backlog.md          # 開発バックログ
├── collector/          # メインモジュール（予定）
│   ├── __init__.py
│   ├── runner.py       # N回API呼び出し並列実行
│   ├── aggregator.py   # trie集計
│   └── serializer.py   # JSON書き出し
└── out/                # 出力ディレクトリ
    └── run-*.json      # 実行結果
```

## 主要コンポーネント
1. **Runner**: N回のAPI呼び出しを並列実行（AsyncIO + Semaphore）
2. **Aggregator**: 文字列をtrieへ集計
3. **Serializer**: JSON形式で結果を出力

## 実装時の注意点
### OpenAI API
- `store=false` で一時的な実験用途に最適化
- 429エラー対応: SDKの自動リトライ + 並列数調整
- `max_output_tokens` は小さく設定（コスト/時間削減）

### 並列処理
- `asyncio.Semaphore` で同時実行数を制限
- 429比率に応じて動的に並列数を調整（オプション）

### 逸脱検出
- `expected_answers` との完全一致で判定
- 正規化オプション: strip, newline統一, 句読点除去

## コマンド例
```bash
# 依存インストール
uv sync

# 実行
python -m collector run \
  --prompt "Just answer YES or NO. Is the sky blue?" \
  --n 10000 \
  --concurrency 50 \
  --out out/run-$(date +%Y%m%d-%H%M%S).json
```

## 参考リンク
- [Responses API](https://platform.openai.com/docs/api-reference/responses)
- [gpt-4.1-mini](https://platform.openai.com/docs/models/gpt-4.1-mini)
- [Rate limits](https://platform.openai.com/docs/guides/rate-limits)

## 開発優先度
`docs/backlog.md` を参照。P0タスクを最優先で完了させること。
