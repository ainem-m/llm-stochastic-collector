# Backlog（完成優先）

## P0: 動くものを最速で作る
- [ ] uvプロジェクト雛形作成（pyproject / lock）
- [ ] 設定（CLI引数 or config.json）読み込み
- [ ] Responses API 呼び出し（AsyncOpenAI）
- [ ] concurrency 制御（Semaphore）
- [ ] 結果取得（text）→ runs に格納
- [ ] trie 集計（nodes/edges: id方式）
- [ ] JSON書き出し（meta/config/runs/graph/stats）
- [ ] 429/5xx のリトライ確認（SDKデフォルト + ログ）

## P1: 記事向けに使いやすく
- [ ] deviation 判定（expected_answers + 正規化）
- [ ] depth_stats（entropy, top_chars）計算
- [ ] 逸脱例の上位K抽出
- [ ] 途中フラッシュ（partial）実装

## P2: 余裕があれば
- [ ] concurrency 自動調整（429率ベース）
- [ ] runs の保存ポリシー（全件/逸脱のみ/サンプリング）
- [ ] 図化用の別スクリプト（dot/graphml/sankey用データ）※本件ではコード化しない
