# Backlog（完成優先）

## P0: 動くものを最速で作る
- [x] uvプロジェクト雛形作成（pyproject / lock）
- [x] CLI引数読み込み
- [x] Chat Completions API 呼び出し（AsyncOpenAI）
- [x] concurrency 制御（Semaphore）
- [x] 結果取得（text）→ runs に格納
- [x] trie 集計（nodes/edges: id方式）
- [x] JSON書き出し（meta/config/runs/graph/stats）
- [x] 429/5xx のリトライ確認（SDKデフォルト + ログ）
- [x] レジューム
- [x] チェックポイント保存

## P1: 記事向けに使いやすく
- [ ] 実験アーティファクトの公開導線整理
- [ ] 再現性ドキュメントの整備
- [x] depth_stats（entropy, top_chars）計算
- [x] 可視化スクリプトの追加
- [x] パス圧縮グラフ出力

## P2: 余裕があれば
- [ ] concurrency 自動調整（429率ベース）
- [ ] 逸脱判定（expected_answers + 正規化）
- [ ] runs の保存ポリシー（全件/逸脱のみ/サンプリング）
- [ ] 図化用の別スクリプト（dot/graphml/sankey用データ）※本件ではコード化しない
