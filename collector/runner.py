import asyncio
import logging
from typing import List, Optional, Any, Callable
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

logger = logging.getLogger(__name__)

class Runner:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        n: int,
        concurrency: int,
        request_params: dict,
        on_result: Optional[Callable[[str, dict], Any]] = None,
        on_checkpoint: Optional[Callable[[List[dict]], Any]] = None,
        checkpoint_interval: int = 100
    ):
        self.client = client
        self.model = model
        self.prompt = prompt
        self.n = n
        self.concurrency = concurrency
        self.request_params = request_params
        self.on_result = on_result
        self.on_checkpoint = on_checkpoint
        self.checkpoint_interval = checkpoint_interval
        self._semaphore = asyncio.Semaphore(concurrency)
        self._results = []
        self._errors = []

    async def _call_api(self, run_id: int):
        async with self._semaphore:
            try:
                # OpenAI SDK自体がリトライ機能を持っているが、429対策として追加のリトライが必要になる可能性がある
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": self.prompt}],
                    **self.request_params
                )
                
                text = response.choices[0].message.content or ""
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                } if response.usage else None
                
                logprobs = None
                if response.choices[0].logprobs and response.choices[0].logprobs.content:
                    logprobs = []
                    for lp in response.choices[0].logprobs.content:
                        top_lp = []
                        if lp.top_logprobs:
                            for tlp in lp.top_logprobs:
                                top_lp.append({
                                    "token": tlp.token,
                                    "logprob": tlp.logprob,
                                    "bytes": list(tlp.bytes) if tlp.bytes else None
                                })
                        
                        logprobs.append({
                            "token": lp.token,
                            "logprob": lp.logprob,
                            "bytes": list(lp.bytes) if lp.bytes else None,
                            "top_logprobs": top_lp
                        })
                
                result = {
                    "id": run_id,
                    "text": text,
                    "status": "ok",
                    "usage": usage,
                    "logprobs": logprobs
                }
                
                if self.on_result:
                    self.on_result(text, result)
                
                return result
            except Exception as e:
                logger.error(f"Error in run {run_id}: {e}")
                error_info = {
                    "id": run_id,
                    "status": "error",
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e)
                    }
                }
                return error_info

    async def run(self):
        tasks = [self._call_api(i) for i in range(self.n)]
        
        results = []
        for i, task in enumerate(tqdm(asyncio.as_completed(tasks), total=self.n, desc="Collecting")):
            res = await task
            results.append(res)
            
            # チェックポイントの実行
            if self.on_checkpoint and (i + 1) % self.checkpoint_interval == 0:
                self.on_checkpoint(results)
            
        self._results = sorted(results, key=lambda x: x["id"])
        return self._results
