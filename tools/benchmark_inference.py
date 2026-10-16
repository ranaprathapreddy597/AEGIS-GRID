"""Real streaming endpoint collector. Missing access produces no fabricated measurements."""

import asyncio
import json
import os
import time

import httpx
from aegis_inference.budget import metadata
from dev import read_env


async def collect(client: httpx.AsyncClient, token_ids: list[int], model: str) -> dict[str, object]:
    started = time.perf_counter()
    first = None
    usage = None
    text_chars = 0
    buffer = ""
    async with client.stream(
        "POST",
        "completions",
        json={
            "model": model,
            "prompt": token_ids,
            "max_tokens": 128,
            "temperature": 0,
            "stream": True,
            "stream_options": {"include_usage": True},
        },
    ) as response:
        if response.headers.get("content-encoding", "identity") != "identity":
            raise ValueError("Unexpected compressed benchmark stream")
        if response.status_code != 200:
            return {
                "prompt_tokens_requested": len(token_ids),
                "status": "REFUSED",
                "http_status": response.status_code,
            }
        async for chunk in response.aiter_text():
            buffer += chunk
            buffer = buffer.replace("\r\n", "\n")
            if len(buffer) > 65536:
                raise ValueError("Benchmark SSE event exceeds bound")
            while "\n\n" in buffer:
                event, buffer = buffer.split("\n\n", 1)
                for line in event.splitlines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    item = json.loads(line[6:])
                    if item.get("usage"):
                        usage = item["usage"]
                    for choice in item.get("choices", []):
                        if choice.get("text"):
                            first = first or time.perf_counter()
                            text_chars += len(choice["text"])
    elapsed = time.perf_counter() - started
    if (
        not isinstance(usage, dict)
        or usage.get("prompt_tokens") != len(token_ids)
        or type(usage.get("completion_tokens")) is not int
        or not 1 <= usage["completion_tokens"] <= 128
        or usage.get("total_tokens") != len(token_ids) + usage["completion_tokens"]
        or not text_chars
    ):
        raise ValueError("Benchmark token count not confirmed by server")
    return {
        "status": "MEASURED",
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "response_characters": text_chars,
        "wall_s": elapsed,
        "observed_ttft_s": first - started if first else None,
        "end_to_end_output_tokens_s": usage["completion_tokens"] / elapsed,
        "engine_prefill_tokens_s": None,
        "engine_decode_tokens_s": None,
        "peak_hbm_bytes": None,
        "note": "Network-observed timings. Engine prefill/decode/HBM require device metrics.",
    }


async def main() -> None:
    values = read_env()
    values.update(
        {
            name: os.environ[name]
            for name in ["INFERENCE_BASE_URL", "INFERENCE_API_KEY"]
            if name in os.environ
        }
    )
    if not values.get("INFERENCE_BASE_URL") or not values.get("INFERENCE_API_KEY"):
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "hardware_verified": False,
                    "reason": "MI300X endpoint/access pending",
                    "measurements": [],
                }
            )
        )
        return
    # Import the cloud provisioned tokenizer only after actual access is configured.
    from aegis_inference.client import VLLMClient
    from pydantic import SecretStr
    from transformers import AutoTokenizer

    info, _ = metadata()
    tokenizer = AutoTokenizer.from_pretrained(
        info["model_id"], revision=info["revision"], trust_remote_code=False
    )
    unit = tokenizer.encode(" Synthetic factory evidence record. ", add_special_tokens=False)
    transport = VLLMClient(values["INFERENCE_BASE_URL"], SecretStr(values["INFERENCE_API_KEY"]))
    try:
        rows = []
        for count in [8192, 32768, 131072, 204800, 262016]:
            tokens = (unit * (count // len(unit) + 1))[:count]
            rows.append(
                await asyncio.wait_for(collect(transport.client, tokens, info["model_id"]), 300)
            )
        print(
            json.dumps(
                {
                    "status": "NETWORK_MEASUREMENTS",
                    "hardware_verified": False,
                    "model_revision": info["revision"],
                    "measurements": rows,
                },
                indent=2,
            )
        )
    finally:
        await transport.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, httpx.HTTPError, ImportError, TimeoutError):
        raise SystemExit("Benchmark unavailable; no successful hardware/context claim") from None
