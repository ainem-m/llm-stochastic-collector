# 出力JSONスキーマ（現行実装ベース）

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

* run_id: string（例: `"20260122-125553"`）
* created_at: string（ISO8601）
* library:

  * python: `"3.13.x"`
  * openai: `"v2"`
* host:

  * os: string
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
* raw_text: string|null
* status: "ok" | "error"
* error:

  * type: string
  * message: string
  * http_status: int|null
* usage（取れるなら）:

  * input_tokens: int|null
  * output_tokens: int|null
* deviation: object|null（現実装では通常 `null`）
* logprobs: array|null（`--debug` 時のみ）

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
* deviations: object|null（現実装では通常 `null`）
