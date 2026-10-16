"""Investigation proposals are observations, never execution authorization."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import Contract, FiniteFloat, SimulatorControls


class DiagnosticHypothesis(Contract):
    cause: Literal["sensor_bias", "true_thermal", "restricted_flow", "weak_pump", "overload"]
    support_score: Annotated[FiniteFloat, Field(ge=0, le=1)]
    explanation: str
    score_method: Literal["physics_heuristic_not_probability"] = "physics_heuristic_not_probability"


class GraphTrace(Contract):
    node: str
    iteration: int
    elapsed_ms: Annotated[FiniteFloat, Field(ge=0)]
    detail: str


class CandidatePlan(Contract):
    candidate_id: str
    controls: SimulatorControls
    rationale: str
    red_accepted: bool = False
    simulation_checked: bool = False
    maximum_temperature_c: FiniteFloat | None = None
    executable: Literal[False] = False


class Investigation(Contract):
    investigation_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    incident_id: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    phase: Literal[7] = 7
    status: Literal["running", "paused_no_action", "failed_closed"] = "running"
    backend: Literal["offline_template", "remote_vllm"] = "offline_template"
    hypotheses: list[DiagnosticHypothesis] = []
    candidates: Annotated[list[CandidatePlan], Field(max_length=3)] = []
    traces: Annotated[list[GraphTrace], Field(max_length=80)] = []
    iteration: Annotated[int, Field(ge=0, le=3)] = 0
    max_iterations: Annotated[int, Field(ge=1, le=3)] = 3
    model_token_budget: Annotated[int, Field(ge=128, le=2048)] = 1024
    model_tokens_used: Annotated[int, Field(ge=0, le=2048)] = 0
    cost_usd: None = None
    manual_decision: Literal["no_action", "simulator_evidence_only"] = "no_action"
    evidence_page_hashes: Annotated[list[str], Field(max_length=10)] = []
    observed_history_samples: Annotated[int, Field(ge=0, le=21)] = 0
    observed_temperature_slopes_c_s: Annotated[list[FiniteFloat], Field(max_length=6)] = []
    observed_neighbor_correlations: Annotated[list[FiniteFloat | None], Field(max_length=6)] = []
    baseline_maximum_temperature_c: FiniteFloat | None = None
    native_binary_sha256: str | None = None
    refusal: str = ""
    approval_required: Literal[True] = True
    operational_write_allowed: Literal[False] = False
    live_gates: Literal["MI300X/Evolus/Pinecone BLOCKED"] = "MI300X/Evolus/Pinecone BLOCKED"
