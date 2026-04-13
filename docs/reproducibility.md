# Reproducibility

このプロジェクトで公開する実験結果は、API ベースの確率的生成を対象にしています。したがって、ここでの「再現性」は同一 JSON の完全再生成ではなく、実験条件を固定したうえで傾向を追試できることを意味します。

## 公開対象
- 実験名: first-tooth
- 実験結果: [artifacts/20260122-first-tooth/run-20260122-125553-c50fdbf98a23d7737df7deece017cd1b07bd2df0520ec0bf1b4db6eb6d821e79.json](../artifacts/20260122-first-tooth/run-20260122-125553-c50fdbf98a23d7737df7deece017cd1b07bd2df0520ec0bf1b4db6eb6d821e79.json)
- 実行日時: 2026-01-22 12:55:53 JST
- 対応コミット: `f6acf449de3b57007ddbd86679d0b41a951f3b2f`

## 実験条件
- モデル: `gpt-4.1-mini`
- プロンプト: `日本人において生まれて始めて萌出する歯の歯種は？前置きをせず歯種のみで答えること。回答形式：上顎乳側切歯`
- 試行回数: `10000`
- 並列数: `5`
- `max_output_tokens`: `20`
- `temperature`: `1.0`
- `top_p`: `null`
- `seed`: `null`
- `store`: `false`
- 正規化: 無効
- 実行環境: Python `3.13.1`

## 追試手順
1. `uv` をインストールする。
2. OpenAI API キーを環境変数 `OPENAI_API_KEY` に設定する。
3. 依存関係を固定どおりに同期する。
4. 同一条件で collector を実行する。

```bash
uv sync
export OPENAI_API_KEY=...
uv run python -m collector \
  --prompt "日本人において生まれて始めて萌出する歯の歯種は？前置きをせず歯種のみで答えること。回答形式：上顎乳側切歯" \
  --n 10000 \
  --concurrency 5 \
  --model gpt-4.1-mini \
  --max_tokens 20 \
  --temp 1.0 \
  --out out/reproduced-first-tooth.json
```

## 比較方法
完全一致ではなく、以下の指標で比較することを推奨します。

- 上位回答の頻度順位
- 上位回答の相対頻度
- 一意な回答数
- 文字遷移グラフの主要分岐
- `stats.totals.ok` と `stats.totals.error`

## この run の主要結果
- 成功数: `10000`
- エラー数: `0`
- 一意な回答数: `17`
- 上位 5 回答:
  - `下顎乳中切歯`: `8788`
  - `下顎中切歯`: `744`
  - `下顎乳中央切歯`: `326`
  - `下顎中央切歯`: `73`
  - `下顎乳側切歯`: `34`

## 限界
- `seed` が設定されていないため、同一 JSON の再生成は保証しません。
- SaaS モデルの更新やサーバ側の変更により、将来同一条件でも分布が変わる可能性があります。
- 並列実行はレート制限や内部スケジューリングの影響を受ける可能性があります。
