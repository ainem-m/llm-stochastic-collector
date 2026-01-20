import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from typing import List

from openai import AsyncOpenAI
from collector.runner import Runner
from collector.aggregator import Aggregator
from collector.serializer import (
    CollectorOutput, MetaInfo, ConfigInfo, RequestConfig, 
    NormalizationConfig, GraphInfo, StatsInfo, Node, Edge, RunResult,
    ErrorInfo
)

async def main():
    parser = argparse.ArgumentParser(description="LLM Stochastic Output Collector")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt to run")
    parser.add_argument("--n", type=int, default=10, help="Number of repetitions")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrency level")
    parser.add_argument("--model", type=str, default="gpt-4.1-mini", help="Model name")
    parser.add_argument("--out", type=str, help="Output JSON path")
    parser.add_argument("--temp", type=float, default=1.0, help="Temperature")
    parser.add_argument("--max_tokens", type=int, default=50, help="Max output tokens")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (collect logprobs)")
    
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = AsyncOpenAI(api_key=api_key)
    aggregator = Aggregator()

    def on_result(text, result):
        aggregator.add_text(text)

    request_params = {
        "temperature": args.temp,
        "max_tokens": args.max_tokens,
        "store": False
    }
    
    if args.debug:
        request_params["logprobs"] = True
        request_params["top_logprobs"] = 5

    runner = Runner(
        client=client,
        model=args.model,
        prompt=args.prompt,
        n=args.n,
        concurrency=args.concurrency,
        request_params=request_params,
        on_result=on_result
    )

    print(f"Starting collection: model={args.model}, n={args.n}, concurrency={args.concurrency}")
    raw_results = await runner.run()

    # 集計処理
    nodes_data, edges_data = aggregator.get_graph_data()
    trie_stats = aggregator.calculate_stats()

    # 最終的なJSONデータの構築
    ok_count = sum(1 for r in raw_results if r["status"] == "ok")
    error_count = len(raw_results) - ok_count

    output = CollectorOutput(
        meta=MetaInfo(
            run_id=datetime.now().strftime("%Y%m%d-%H%M%S"),
            library={
                "python": sys.version.split()[0],
                "openai": "v2" # 簡易化
            },
            host={"os": sys.platform}
        ),
        config=ConfigInfo(
            model=args.model,
            prompt=args.prompt,
            n=args.n,
            concurrency=args.concurrency,
            request=RequestConfig(
                max_output_tokens=args.max_tokens,
                temperature=args.temp,
                store=False
            ),
            normalization=NormalizationConfig(enabled=False)
        ),
        runs=[
            RunResult(
                id=r["id"],
                text=r.get("text", ""),
                status=r["status"],
                error=ErrorInfo(**r["error"]) if "error" in r else None,
                usage=r.get("usage"),
                logprobs=r.get("logprobs")
            ) for r in raw_results
        ],
        graph=GraphInfo(
            nodes=[Node(**n) for n in nodes_data],
            edges=[Edge(**e) for e in edges_data]
        ),
        stats=StatsInfo(
            totals={"ok": ok_count, "error": error_count, "total_chars": sum(len(r.get("text", "")) for r in raw_results)},
            depth_stats=trie_stats["depth_stats"]
        )
    )

    out_path = args.out or f"out/run-{output.meta.run_id}.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output.model_dump_json(indent=2, by_alias=True))

    print(f"Done. Output saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
