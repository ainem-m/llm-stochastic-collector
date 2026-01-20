以下は「最短で動く実験用コレクタ」を前提にした、リポジトリに置くMarkdown一式です。OpenAIは **Responses API** を主APIとして扱い ([OpenAI Platform][1])、モデルは **gpt-4.1-mini** ([OpenAI Platform][2])、高並列は **AsyncOpenAI +（必要なら）aiohttpバックエンド** を想定しています ([GitHub][3])。レート制限はアカウント依存なので、429を前提に自動リトライと並列数制御を設計に含めています ([OpenAI Platform][4])。

---

```markdown
<!-- filename: README.md -->
# LLM Stochastic Output Collector (Char-Graph)

## 概要
LLMが「確率的にテキストを生成している」ことを、**同一プロンプトをN回（最大10,000回）実行**して可視化するための実験用コレクタ。
各生成結果（テキスト）を保存し、同時に**文字単位の遷移グラフ（prefix tree / trie）**として集計する。

- 目的: 記事用の実験データ作成（配布・汎用化は目的外）
- モデル: `gpt-4.1-mini`（予定）
- 実装: Python + uv
- 出力: JSON（生データ + 集計グラフ + 統計）

## 主要機能
- 単一プロンプトをN回収集（最大10,000）
- 高並列でAPIを叩き最速収集（並列数は設定可能・自動調整も可）
- 生成結果の保存（必要ならサンプリング保存にも切替可能）
- 文字単位のグラフ集計（ノード=prefix、エッジ=次の1文字）
- 基本統計（分岐数、深さ別エントロピー、頻出パス、エラー率など）

## 非目標（このプロジェクトではやらない）
- logprobsの取得・解析
- Web UIや配布用パッケージング
- 複数プロンプトを一括でバッチ実行（将来拡張は可能だが優先度低）

## 想定ユースケース
- YES/NOや短文回答で「ごく稀に誤る」事例を収集し、頻度として提示
- 文字単位の分岐（例: "Y"→"E"→"S" vs "N"→"O"）をグラフで可視化

## クイックスタート（予定）
1. `OPENAI_API_KEY` を環境変数へ設定
2. `uv` で依存導入
3. `python -m collector run --prompt "...(<=50 chars)" --n 10000 --concurrency 50 --out out/run-YYYYMMDD-HHMMSS.json`

詳細は `docs/` を参照。

## 出力ファイル
- `out/run-*.json`  
  - `runs[]`: 各試行の生出力（またはサンプリング）
  - `graph`: 文字遷移グラフ（trie）
  - `stats`: 集計統計とエラー集計（設定時）

## 参考（OpenAI Docs）
- Responses API: https://platform.openai.com/docs/api-reference/responses
- gpt-4.1-mini: https://platform.openai.com/docs/models/gpt-4.1-mini
- Rate limits: https://platform.openai.com/docs/guides/rate-limits
```

```markdown
<!-- filename: docs/requirements.md -->
# 要件定義

## 1. 目的
同一プロンプトをN回生成し、LLM出力の揺らぎを
- **頻度（統計）**
- **文字遷移グラフ（グラフ構造）**
で示す。加えて、ごく稀なハルシネーション（期待回答からの逸脱）を実例として採集する。

## 2. スコープ
### In-scope
- 単一プロンプトに対するN回実行（最大10,000）
- 高並列実行
- 生成結果の保存（全件 or サンプリング）
- 文字単位のグラフ集計（trie）
- JSON出力

### Out-of-scope
- GUI / Web可視化
- logprobs取得
- 多プロンプト一括運用（将来拡張）
- 配布・インストーラ化

## 3. 機能要件
### 3.1 実行
- 入力: prompt（<=50文字想定）、N、並列数、モデル、生成パラメータ
- 出力: JSON（生結果 + 集計結果 + 実行メタデータ）

### 3.2 収集
- 同一設定でN回実行
- 失敗（429/5xx/timeout）時のリトライ
- 収集の進捗（ログ）と中断時の扱い（部分結果を残す）

### 3.3 集計（グラフ）
- 生成テキストをUnicode文字列として処理し、先頭から1文字ずつ遷移をカウント
- ノード: prefix（空文字から開始）
- エッジ: (prefix -> prefix+char) を count で保持
- 付随統計:
  - 深さdごとの分岐数、上位k文字、エントロピー
  - 最頻パス（mode出力）とその比率

### 3.4 ハルシネーション（逸脱）抽出（任意設定）
- ユーザー定義の「期待回答（正解集合）」を設定可能にする
- 生成結果が期待集合に入らない場合に "deviation" として記録し、例を収集
- 逸脱判定はまずは単純（完全一致/正規化一致）でよい

## 4. 非機能要件
- **最速収集**優先（拡張性は二の次）
- 10,000回で破綻しないメモリ・書き込み設計
- 再現性のため、実行時のパラメータ・ライブラリ情報をJSONに保存

## 5. 制約・前提
- OpenAI Responses API を使用
- 価格やレート制限はアカウント/モデルで変動するため、429を前提に制御する
- 出力長が長いとコストと時間が増えるため、max_output_tokens を小さめに制御できること

## 6. 未確定事項（埋めると仕様が確定）
- 出力の想定長（例: 1トークン相当/短文/数文）
- temperature/top_p をどうするか（揺らぎを見せたいならtemperature>0）
- 出力の正規化方針（例: 前後空白除去、改行除去、句読点統一など）
- 逸脱判定の定義（完全一致で十分か、正規化一致か）
- 生データ保存方針（全件保存 vs 逸脱のみ保存 vs 上位頻出のみ保存）
```

```markdown
<!-- filename: docs/design.md -->
# 設計（最短で完成させるための設計判断）

## 1. アーキテクチャ
### コンポーネント
- Runner: N回のAPI呼び出しを並列実行し、結果を受け取る
- Aggregator: 受け取った文字列を逐次trieへ反映
- Serializer: 途中経過/最終結果をJSONへ書き出す

### データフロー
1) 設定読み込み  
2) N個のタスクをキューへ投入  
3) ワーカーがResponses APIを呼び、`output_text` を得る  
4) Aggregatorへ渡してグラフ集計  
5) 生結果（必要に応じて）保存  
6) 完了後JSONを書き出し

## 2. OpenAI呼び出し方針
- API: Responses API
- store: 実験用途で再取得不要なら `store=false` を推奨（保存が必要ならtrue）
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
最初は「生の揺らぎ」を見せたいので **正規化なし** を基本。
ただし比較用に任意でオンにできると便利：
- strip: 前後空白除去
- newline: 改行を `\n` に統一
- collapse_spaces: 連続空白を1つに
- ascii_punct: 句読点の統一（用途次第）

## 5. 逸脱（ハルシネーション候補）検出
### 5.1 最短実装
- `expected_answers: [ ... ]` を設定
- 正規化ルール（任意）適用後に完全一致判定
- 一致しなければ `deviation=true` として保存

### 5.2 注意
- 「期待回答」をどう定義するかで逸脱率が大きく変わる
- LLMは余計な前置き（例: "答えはYESです"）を混ぜるため、正規化 or 出力制約が効く

## 6. コスト/速度のボトルネック
- 出力長（max_output_tokens）が最大の支配要因
- concurrency を上げすぎると429で逆に遅くなる
- 10,000回を短時間で回すなら、短出力・適切な並列数・キャッシュなし前提のコスト見積りが重要

## 7. Definition of Done（完成条件）
- N=10,000で最後まで完走できる（429が出ても最終的に収束）
- out.json がスキーマ通りに生成される
- `graph.edges[].count` 合計が「保存した（正規化後）文字数合計」と整合する
- deviation 設定時、逸脱例がJSONに保存される
```

````markdown
<!-- filename: docs/data_schema.md -->
# 出力JSONスキーマ（提案）

## 1. ルート
```json
{
  "meta": { ... },
  "config": { ... },
  "runs": [ ... ],
  "graph": { ... },
  "stats": { ... }
}
````

## 2. meta

* run_id: string（例: "2026-01-20T12:34:56+09:00"）
* created_at: string（ISO8601）
* library:

  * python: "3.12.x"
  * openai_sdk: "x.y.z"
* host:

  * os: string
  * cpu: string（任意）
* notes: string（任意）

## 3. config

* model: string（例: "gpt-4.1-mini"）
* prompt: string
* n: int
* concurrency: int
* request:

  * max_output_tokens: int
  * temperature: number|null
  * top_p: number|null
  * seed: int|null（再現性が欲しい場合のみ）
  * store: bool
* normalization:

  * enabled: bool
  * rules: object

## 4. runs（生データ）

※ 最短実装では「全件保存」を推奨（出力が短い前提）。長くなるなら `save_policy` を導入。

* id: int（0..N-1）
* text: string（生 or 正規化後テキスト）
* raw_text: string|null（正規化する場合のみ）
* status: "ok" | "error"
* error:

  * type: string
  * message: string
  * http_status: int|null
* usage（取れるなら）:

  * input_tokens: int|null
  * output_tokens: int|null
* deviation:

  * enabled: bool
  * is_deviation: bool|null
  * matched_expected: string|null

## 5. graph（trie）

```json
{
  "nodes": [
    { "id": 0, "depth": 0 },
    { "id": 1, "depth": 1 }
  ],
  "edges": [
    { "from": 0, "to": 1, "ch": "Y", "count": 9995 }
  ]
}
```

* nodes:

  * id: int
  * depth: int（prefix長）
* edges:

  * from/to: int（node id）
  * ch: string（1文字、改行は "\n" として格納）
  * count: int
  * p: number|null（後処理で count/親の総数 を入れてもよい）

## 6. stats

* totals:

  * ok: int
  * error: int
  * total_chars: int
* depth_stats: array

  * depth: int
  * total_transitions: int
  * unique_chars: int
  * top_chars: [{ch, count, p}]
  * entropy_bits: number
* deviations（enabled時）:

  * deviation_count: int
  * deviation_rate: number
  * examples: [{id, text}]（上位K件）

````

```markdown
<!-- filename: docs/experiment_protocol.md -->
# 実験プロトコル（記事向け）

## 1. 実験の狙い（読者に見せたい絵）
- 同じ質問でも、LLMは常に同一の文字列を返すわけではない（確率的生成）
- 一見「間違いようがない」問いでも、ごく低頻度で逸脱が起きる
- その揺らぎを「木（trie）」として見せると直感的に伝わる

## 2. 推奨のプロンプト設計
### 2.1 出力を短く縛る（最重要）
- 例: "Just answer YES or NO. (質問...)"
- 目的: 余計な前置きや言い換えを減らし、分岐が読める形になる

### 2.2 逸脱率を適度に上げたい場合
- 誘導（leading question）を混ぜる / 紛らわしいが正解は一意の質問にする
- ただし「読者が納得する正解」を用意できるものに限る

## 3. 推奨パラメータ
- max_output_tokens: 3〜10 程度（YES/NOなら極小）
- temperature:
  - 揺らぎを見せたい: 0.2〜0.8
  - 逸脱の稀少性を見せたい: 0.0〜0.2（ただし完全固定になり得る）
- top_p: 基本は1.0（温度を使うなら top_p は触らない）
- seed:
  - **使わない**: 確率性を見せる
  - **使う**: 「同条件なら固定化できる（ただしバックエンド変更で崩れる可能性）」の補足ネタ

## 4. Nと並列数の目安
- N=10,000（予定）
- concurrency: まず20〜50で開始し、429が多ければ下げる

## 5. 逸脱（deviation）定義例
### 5.1 完全一致（最短）
- expected_answers=["YES","NO"] のどちらかに完全一致しなければ逸脱
- 正規化を使うなら:
  - 前後空白除去
  - 改行除去
  - "YES." の句点を除く（用途次第）

## 6. 成果物（記事に載せるもの）
- 逸脱率（deviation_rate）
- 最頻出回答と頻度
- 深さ別の分岐（entropyやtop_chars）
- 逸脱例の生ログ（数件）
- 分岐木（別途、解析スクリプトで図化する前提）
````

```markdown
<!-- filename: docs/runbook.md -->
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
```

```markdown
<!-- filename: docs/backlog.md -->
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
```

---

## 補足（設計上の“決めどころ”だけ列挙）

* **出力長**（max_output_tokens）をどれくらいに縛るかで、コスト・時間・グラフの見やすさがほぼ決まります。
* **逸脱（ハルシネーション）判定**を「完全一致」で済ませるか、最低限の正規化を入れるか。
* **生データ保存**を全件にするか（短文なら全件でよい）、逸脱だけにするか。

この3点が未確定でも、上記MarkdownのP0で一旦完走できます。

[1]: https://platform.openai.com/docs/api-reference/responses?utm_source=chatgpt.com "Responses | OpenAI API Reference"
[2]: https://platform.openai.com/docs/models/gpt-4.1-mini?utm_source=chatgpt.com "GPT-4.1 mini Model | OpenAI API"
[3]: https://github.com/openai/openai-python "GitHub - openai/openai-python: The official Python library for the OpenAI API"
[4]: https://platform.openai.com/docs/guides/rate-limits?utm_source=chatgpt.com "Rate limits | OpenAI API"
