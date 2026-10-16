"""Full-resident BF16 weights and dense GQA KV from pinned upstream metadata."""

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from aegis_contracts.inference import MemoryBudget

GIB = 1024**3


def metadata() -> tuple[dict[str, Any], dict[str, Any]]:
    folder = Path(__file__).parent
    raw = (folder / "model-config.json").read_bytes()
    info = json.loads((folder / "model-metadata.json").read_text("utf-8"))
    config = json.loads(raw)
    if hashlib.sha256(raw).hexdigest() != info["config_sha256"]:
        raise ValueError("Model config integrity mismatch")
    if (
        info["parameter_dtypes"] != {"BF16": info["parameter_count"]}
        or config.get("use_sliding_window")
        or config.get("rope_scaling") is not None
        or config.get("model_type") != "qwen3_moe"
    ):
        raise ValueError("Unbudgeted model architecture/dtype/attention")
    return info, config


def calculate(
    context_tokens: int = 262144,
    concurrent_sequences: int = 2,
    kv_dtype: Literal["bf16", "fp8"] = "bf16",
    capacity_bytes: int = 192_000_000_000,
    *,
    runtime_gib: float = 12.0,
    activations_gib: float = 4.0,
    fragmentation_gib: float = 8.0,
    other_gib: float = 4.0,
) -> MemoryBudget:
    info, config = metadata()
    if (
        type(context_tokens) is not int
        or not 1 <= context_tokens <= config["max_position_embeddings"]
        or type(concurrent_sequences) is not int
        or not 1 <= concurrent_sequences <= 64
        or kv_dtype not in {"bf16", "fp8"}
        or type(capacity_bytes) is not int
        or capacity_bytes <= 0
    ):
        raise ValueError("Invalid budget configuration")
    import math

    if any(
        not math.isfinite(v) or v < 0
        for v in (runtime_gib, activations_gib, fragmentation_gib, other_gib)
    ):
        raise ValueError("Runtime assumptions must be finite and nonnegative")
    weight = info["parameter_count"] * 2 / GIB
    kv = (
        2
        * config["num_hidden_layers"]
        * config["num_key_value_heads"]
        * config["head_dim"]
        * (2 if kv_dtype == "bf16" else 1)
        * context_tokens
        * concurrent_sequences
        / GIB
    )
    total = weight + kv + runtime_gib + activations_gib + fragmentation_gib + other_gib
    capacity = capacity_bytes / GIB
    return MemoryBudget(
        model_id=info["model_id"],
        model_revision=info["revision"],
        parameters=info["parameter_count"],
        context_tokens=context_tokens,
        concurrent_sequences=concurrent_sequences,
        kv_dtype=kv_dtype,
        weight_gib=weight,
        kv_gib=kv,
        runtime_reserved_gib=runtime_gib,
        temporary_activations_gib=activations_gib,
        fragmentation_gib=fragmentation_gib,
        other_buffers_gib=other_gib,
        total_gib=total,
        capacity_gib=capacity,
        projected_headroom_gib=capacity - total,
        projected_fits=total <= capacity,
    )
