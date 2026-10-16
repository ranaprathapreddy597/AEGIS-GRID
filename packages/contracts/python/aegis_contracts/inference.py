"""Model proposals and resource estimates never constitute execution authority."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import Contract, FiniteFloat


class MemoryBudget(Contract):
    model_id: str
    model_revision: str
    parameters: int
    context_tokens: int
    concurrent_sequences: int
    kv_dtype: Literal["bf16", "fp8"]
    weight_gib: FiniteFloat
    kv_gib: FiniteFloat
    runtime_reserved_gib: FiniteFloat
    temporary_activations_gib: FiniteFloat
    fragmentation_gib: FiniteFloat
    other_buffers_gib: FiniteFloat
    total_gib: FiniteFloat
    capacity_gib: FiniteFloat
    projected_headroom_gib: FiniteFloat
    projected_fits: bool
    hardware_measured: Literal[False] = False


class ModelOpinion(Contract):
    assessment: Literal["insufficient_evidence", "investigate"]
    hypotheses: Annotated[
        list[Literal["sensor_bias", "restricted_flow", "weak_pump", "overload"]],
        Field(max_length=4),
    ]
    evidence_ids: Annotated[list[str], Field(max_length=20)]
    # No free-form commands, arbitrary tools, credentials, actions or write scope.


class PlanningOpinion(Contract):
    recommendation: Literal["minimax_candidate", "emergency_stop", "abstain"]
    evidence_ids: Annotated[
        list[Literal["candidate_evaluations", "retrieved_sources"]], Field(max_length=2)
    ]


class InferenceResult(Contract):
    backend: Literal["remote_vllm", "offline_template"]
    model_id: str
    opinion: ModelOpinion
    prompt_tokens: Annotated[int, Field(ge=0)] | None
    completion_tokens: Annotated[int, Field(ge=0)] | None
    latency_ms: Annotated[FiniteFloat, Field(ge=0)] | None
    operational_write_allowed: Literal[False] = False


class InferenceStatus(Contract):
    state: Literal["blocked", "offline_development"]
    hardware_verified: Literal[False] = False
    model_id: str
    native_context_tokens: int
    reason: str
