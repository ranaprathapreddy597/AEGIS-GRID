"""Stream collector contract doubles, never presented as hardware measurements."""

import asyncio
import importlib.util
import json

import httpx


def test_benchmark_stream_keeps_network_and_unmeasured_engine_metrics_separate():
    spec = importlib.util.spec_from_file_location("collector", "tools/benchmark_inference.py")
    module = importlib.util.module_from_spec(spec)
    # Importing the collector needs only local dev configuration helpers.
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path("tools").resolve()))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    async def run():
        events = [
            {"choices": [{"text": "fixture"}]},
            {
                "choices": [],
                "usage": {"prompt_tokens": 8, "completion_tokens": 1, "total_tokens": 9},
            },
        ]
        data = "".join("data: " + json.dumps(event) + "\n\n" for event in events)
        data += "data: [DONE]\n\n"
        async with httpx.AsyncClient(
            base_url="https://fixture.invalid/v1/",
            transport=httpx.MockTransport(lambda request: httpx.Response(200, text=data)),
        ) as client:
            result = await module.collect(client, [1] * 8, "fixture")
        assert result["prompt_tokens"] == 8 and result["completion_tokens"] == 1
        assert result["observed_ttft_s"] is not None
        assert result["engine_prefill_tokens_s"] is result["engine_decode_tokens_s"] is None
        assert result["peak_hbm_bytes"] is None

    asyncio.run(run())
