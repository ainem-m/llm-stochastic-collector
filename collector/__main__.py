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
from collector.cache_manager import calculate_prompt_hash, find_latest_run
from collector.serializer import (
    CollectorOutput, MetaInfo, ConfigInfo, RequestConfig, 
    NormalizationConfig, GraphInfo, StatsInfo, Node, Edge, RunResult,
    ErrorInfo, LogprobContent
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

    # ハッシュの計算
    config_dict = {
        "model": args.model,
        "prompt": args.prompt,
        "temp": args.temp,
        "max_tokens": args.max_tokens,
        "debug": args.debug
    }
    prompt_hash = calculate_prompt_hash(config_dict)
    
    # 既存ファイルの検索とロード
    out_dir = "out"
    existing_file = find_latest_run(out_dir, prompt_hash)
    existing_runs = []
    
    if existing_file:
        print(f"Existing run found: {existing_file}. Resuming...")
        try:
            with open(existing_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                output_model = CollectorOutput(**data)
                existing_runs = [r.model_dump() for r in output_model.runs if r.status == "ok"]
                aggregator.load_from_runs(existing_runs)
                print(f"Loaded {len(existing_runs)} successful runs.")
        except Exception as e:
            print(f"Warning: Failed to load existing file: {e}. Starting fresh.")

    # 必要回数の計算
    needed_n = max(0, args.n - len(existing_runs))
    
    if needed_n == 0:
        print(f"Already have {len(existing_runs)} runs. No more runs needed.")
        raw_results = []
    else:
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

        def save_output(all_runs, is_checkpoint=False):
            # 集計
            nodes_data, edges_data = aggregator.get_graph_data()
            trie_stats = aggregator.calculate_stats()
            
            ok_count = sum(1 for r in all_runs if r.get("status") == "ok")
            error_count = len(all_runs) - ok_count
            
            output = CollectorOutput(
                meta=MetaInfo(
                    run_id=datetime.now().strftime("%Y%m%d-%H%M%S"),
                    library={"python": sys.version.split()[0], "openai": "v2"},
                    host={"os": sys.platform},
                    notes="Checkpoint" if is_checkpoint else None
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
                        id=i,  # 全体で一意なIDに振り直し
                        text=r.get("text", ""),
                        status=r.get("status", "ok"),
                        error=ErrorInfo(**r["error"]) if r.get("error") else None,
                        usage=r.get("usage"),
                        logprobs=r.get("logprobs")
                    ) for i, r in enumerate(all_runs)
                ],
                graph=GraphInfo(
                    nodes=[Node(**n) for n in nodes_data],
                    edges=[Edge(**e) for e in edges_data]
                ),
                stats=StatsInfo(
                    totals={
                        "ok": ok_count, 
                        "error": error_count, 
                        "total_chars": sum(len(r.get("text", "")) for r in all_runs)
                    },
                    depth_stats=trie_stats["depth_stats"]
                )
            )
            
            current_id = output.meta.run_id
            fname = f"checkpoint-{current_id}-{prompt_hash}.json" if is_checkpoint else f"run-{current_id}-{prompt_hash}.json"
            final_path = args.out or os.path.join(out_dir, fname)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(output.model_dump_json(indent=2, by_alias=True))
            return final_path

        def on_checkpoint(current_new_runs):
            combined = existing_runs + current_new_runs
            path = save_output(combined, is_checkpoint=True)
            print(f" Checkpoint saved to {path}")

        runner = Runner(
            client=client,
            model=args.model,
            prompt=args.prompt,
            n=needed_n,
            concurrency=args.concurrency,
            request_params=request_params,
            on_result=on_result,
            on_checkpoint=on_checkpoint,
            checkpoint_interval=max(1, needed_n // 5) # 20%ごとに保存
        )

        print(f"Starting collection: model={args.model}, total_goal={args.n}, existing={len(existing_runs)}, need={needed_n}")
        new_results = await runner.run()
        raw_results = existing_runs + new_results

    # 最終保存
    if needed_n > 0 or not existing_file:
        final_path = save_output(raw_results, is_checkpoint=False)
        print(f"Done. Output saved to {final_path}")
    else:
        print(f"Existing results are up-to-date: {existing_file}")

if __name__ == "__main__":
    asyncio.run(main())
