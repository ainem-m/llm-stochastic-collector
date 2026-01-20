# 実行・運用メモ

## 1. 環境変数
- OPENAI_API_KEY: 必須
- （任意）OPENAI_PROJECT / OPENAI_ORGANIZATION: プロジェクト分離したい場合

## 2. 推奨設定（まず動かす）
- prompt: 短い固定（<=50文字）
- n: 1000 → 10000へ段階的に
- max_output_tokens: 小さめ
- concurrency: 20開始

## 3. 失敗しがちなポイント
- concurrencyを上げすぎて429が頻発 → トータル時間が悪化
- 出力が長い → コストと時間が跳ねる
- 正規化なしだと分岐が増えすぎる → 可視化が読みづらい（必要なら正規化）

## 4. コスト見積り（概算の立て方）
- 総トークン = N * (input_tokens + output_tokens)
- 価格はモデル・プランで変動するので、最新の料金表を参照して計算すること
  - 参考: https://platform.openai.com/docs/pricing

## 5. 収集中断時の扱い
- 途中経過を `out.partial.json` に定期フラッシュ（最短実装でも推奨）
- 完了時に `out.json` として確定版を書き出す
