import json
import asyncio
import sys
import os
from typing import List, Dict, Any
from collections import Counter
from openai import AsyncOpenAI
from pydantic import BaseModel

# カテゴリ分類用のスキーマ
class ClassificationResult(BaseModel):
    category: str
    reason: str

async def classify_text(client: AsyncOpenAI, text: str, model: str) -> ClassificationResult:
    """LLMを使用してテキストを分類する"""
    prompt = f"""以下のLLMによる回答テキストを、その記述スタイルやスタンスに基づいて分類してください。

対象テキスト:
\"\"\"{text}\"\"\"

分類カテゴリ:
- ASSERTIVE: 「札幌市です」のように、単に事実を言い切っているもの。
- CORRECTIVE: 「道庁所在地ですが」や「厳密には県ではなく道ですが」のように、前提の誤りを指摘または補足しながら回答しているもの。
- DENIAL: 「北海道は『道』なので県庁所在地はありません」のように、存在を否定するもの。
- OTHER: 上記のどれにも当てはまらないもの。

出力フォーマット (JSON):
{{
  "category": "ASSERTIVE | CORRECTIVE | DENIAL | OTHER",
  "reason": "そのカテゴリに分類した簡潔な理由"
}}
"""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that classifies text patterns."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return ClassificationResult(**data)
    except Exception as e:
        return ClassificationResult(category="ERROR", reason=str(e))

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/classify_responses.py <input.json> [model]")
        return

    input_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "gpt-4o-mini"
    
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 成功した実行結果からユニークな回答を抽出
    runs = data.get("runs", [])
    texts = [r["text"] for r in runs if r.get("status") == "ok"]
    unique_texts_counter = Counter(texts)
    unique_texts = list(unique_texts_counter.keys())

    print(f"Total successful runs: {len(texts)}")
    print(f"Unique response patterns: {len(unique_texts)}")
    print(f"Classifying using {model}...")

    client = AsyncOpenAI()
    
    # バッチ処理（同時並列数を制限）
    semaphore = asyncio.Semaphore(10)
    
    async def limited_classify(text):
        async with semaphore:
            return await classify_text(client, text, model)

    tasks = [limited_classify(text) for text in unique_texts]
    results = await asyncio.gather(*tasks)

    # 集計
    category_counts = Counter()
    classification_map = {} # text -> result

    for text, res in zip(unique_texts, results):
        count = unique_texts_counter[text]
        category_counts[res.category] += count
        classification_map[text] = {
            "category": res.category,
            "reason": res.reason,
            "count": count
        }

    # レポート生成
    print("\n=== Classification Report ===")
    total = sum(category_counts.values())
    for cat, count in category_counts.most_common():
        percentage = (count / total) * 100
        print(f"{cat}: {count} ({percentage:.1f}%)")

    # 結果を保存
    output_report = {
        "summary": dict(category_counts),
        "details": classification_map
    }
    
    report_path = "classification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(output_report, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
