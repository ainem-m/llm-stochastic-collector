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
```

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
