# 設計（最短で完成させるための設計判断）

## 1. アーキテクチャ
### コンポーネント
- Runner: N回のAPI呼び出しを並列実行し、結果を受け取る
- Aggregator: 受け取った文字列を逐次trieへ反映
- Serializer: 途中経過/最終結果をJSONへ書き出す

### データフロー
1) 設定読み込み  
2) N個のタスクをキューへ投入  
3) ワーカーが Chat Completions API を呼び、`message.content` を得る  
4) Aggregatorへ渡してグラフ集計  
5) 生結果（必要に応じて）保存  
6) 完了後JSONを書き出し

## 2. OpenAI呼び出し方針
- API: Chat Completions API
- `AsyncOpenAI.chat.completions.create(...)` を使用
- store: 実験用途で再取得不要なら `store=false` を指定
- stream: false（高速化より実装簡潔さ優先）
- retries: SDKのデフォルトリトライに加え、429頻発時は並列数を落とす

## 3. 並列実行・レート制限戦略
### 3.1 並列実行
- AsyncIOを基本とし、同時in-flight数を `concurrency` で制限（Semaphore）
- 進捗: 完了数/失敗数/再試行数を一定間隔でログ出力

### 3.2 429 / 5xx 対応
- SDKの自動リトライ（指数バックオフ）を前提にする
- 追加で「429が一定割合を超えたら concurrency を段階的に下げる」簡易制御を入れる（最短で効く）

例: 直近200試行で429比率が>5%なら concurrency を -10%、<1%なら +5%（上限あり）

## 4. 文字遷移グラフ（trie）仕様
### 4.1 定義
- rootノード: prefix=""（空文字）
- 各出力文字列 s に対し、i=0..len(s)-1 で
  - prefix = s[:i]
  - next = s[i]
  - edge(prefix, prefix+next) の count++

### 4.2 実装上の表現（ID方式）
JSONサイズと速度のため、prefix文字列を毎回持つより
- node_id を連番付与
- edge: from_id, to_id, ch, count
とする。

### 4.3 正規化（デフォルトは「しない」）
現実装では **正規化なし**。生成された文字列をそのまま集計する。

## 5. 逸脱（ハルシネーション候補）検出
現実装では未対応。必要な場合は出力 JSON を後段で解析して頻度外れ値や期待回答との差分を評価する。

## 6. コスト/速度のボトルネック
- 出力長（max_output_tokens）が最大の支配要因
- concurrency を上げすぎると429で逆に遅くなる
- 10,000回を短時間で回すなら、短出力・適切な並列数・レジューム前提のコスト見積りが重要

## 7. Definition of Done（完成条件）
- N=10,000で最後まで完走できる（429が出ても最終的に収束）
- out.json がスキーマ通りに生成される
- `graph.edges[].count` 合計が「保存した（正規化後）文字数合計」と整合する
- `--debug` 有効時、`logprobs` がJSONに保存される
