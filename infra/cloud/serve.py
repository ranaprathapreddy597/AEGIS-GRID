"""Run only on an authorized provisioned GPU host, after device/image checks."""

import hashlib
import json
import os
import sys
from pathlib import Path


def command() -> list[str]:
    folder = Path(__file__).parent
    metadata = json.loads((folder / "model-metadata.json").read_text("utf-8"))
    config = json.loads((folder / "model-config.json").read_text("utf-8"))
    if (
        hashlib.sha256((folder / "model-config.json").read_bytes()).hexdigest()
        != metadata["config_sha256"]
    ):
        raise ValueError("Pinned config integrity mismatch")
    context = int(os.environ.get("AEGIS_CONTEXT_TOKENS", "8192"))
    sequences = int(os.environ.get("AEGIS_CONCURRENT_SEQUENCES", "1"))
    if not 1 <= context <= config["max_position_embeddings"] or not 1 <= sequences <= 2:
        raise ValueError("Unsupported context/concurrency")
    key = os.environ.get("VLLM_API_KEY", "")
    if len(key) < 32:
        raise ValueError("Distinct strong inference authentication required")
    # VLLM_API_KEY is read by vLLM. Never interpolate it into argv or logs.
    return [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        metadata["model_id"],
        "--revision",
        metadata["revision"],
        "--tokenizer-revision",
        metadata["revision"],
        "--served-model-name",
        metadata["model_id"],
        "--dtype",
        "bfloat16",
        "--kv-cache-dtype",
        "auto",
        "--max-model-len",
        str(context),
        "--max-num-seqs",
        str(sequences),
        "--max-num-batched-tokens",
        "8192",
        "--enable-chunked-prefill",
        "--gpu-memory-utilization",
        "0.90",
        "--generation-config",
        "vllm",
        "--disable-log-requests",
        "--host",
        "0.0.0.0",  # noqa: S104 - container port published only on host loopback
        "--port",
        "8000",
    ]


if __name__ == "__main__":
    argv = command()
    from importlib.metadata import version

    import torch

    if (
        not torch.version.hip
        or not torch.version.hip.startswith("7.0")
        or not version("vllm").startswith("0.11.2")
        or torch.cuda.device_count() != 1
        or "MI300X" not in torch.cuda.get_device_name(0)
    ):
        raise SystemExit("Observed runtime/device mismatch; review compatibility before launch")
    os.execv(argv[0], argv)  # noqa: S606 - fixed interpreter/argument builder, no shell
