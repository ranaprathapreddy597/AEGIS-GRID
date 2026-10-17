"""Investigation proposals are observations, never execution authorization."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.inference import ModelOpinion, PlanningOpinion
from aegis_contracts.manuals import ManualDecision
from aegis_contracts.models import Contract, FiniteFloat, SimulatorControls
from aegis_contracts.optimization import RecoveryAssessment


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


class SourceCitation(Contract):
    reference_id: str
    namespace: Literal["aegis-synthetic-v1-6e4d75051cbcaf1e", "real-world-v1"]
    title: str
    source: str
    revision: str
    source_sha256: str
    license: str
    attribution: str
    synthetic: bool
    applicability: Literal["synthetic_simulator_evidence", "external_context_only"]
    tenant_id: Literal["local"] = "local"
    plant_id: Literal["isolated-simulator"] = "isolated-simulator"


class ModelAttribution(Contract):
    role: Literal["diagnosis", "planning"]
    requested_model: str
    served_model: str
    attempted_models: list[str]
    latency_ms: Annotated[FiniteFloat, Field(ge=0)]
    prompt_tokens: Annotated[int, Field(ge=0)]
    completion_tokens: Annotated[int, Field(ge=0)]
    hardware_verified: Literal[False] = False


class ModelAttempt(Contract):
    role: Literal["diagnosis", "planning"]
    model: Literal["DeepSeek-V4-Flash", "GLM-5.3-Flash", "Qwen3.8-Flash-Next"]
    stage: Annotated[str, Field(max_length=40)]
    http_status: Annotated[int, Field(ge=100, le=599)] | None = None
    rejection_class: Annotated[str, Field(max_length=60)] = ""
    schema_errors: Annotated[list[str], Field(max_length=10)] = []


RecoveryBlocker = Literal[
    "incident_gateway_scope_unavailable",
    "unresolved_manual_evidence",
    "missing_or_abstaining_diagnosis",
    "missing_or_ungrounded_planning",
    "native_candidate_not_verified",
]


class RecoveryEligibility(Contract):
    investigation_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    incident_id: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    status: Literal["BLOCKED"] = "BLOCKED"
    eligible: Literal[False] = False
    blockers: list[RecoveryBlocker]
    manual_corpus_sha256: str
    manual_decision: ManualDecision
    meaningful_hosted_diagnosis: bool
    grounded_hosted_planning: bool
    native_candidate_checked: bool
    challenge_issued: Literal[False] = False
    capability_issued: Literal[False] = False
    execution_scope: Literal["incident_recovery_unavailable"] = "incident_recovery_unavailable"


class Investigation(Contract):
    investigation_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    incident_id: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    phase: Literal[7] = 7
    status: Literal["running", "paused_no_action", "failed_closed"] = "running"
    backend: Literal["offline_template", "remote_vllm", "amd_token_factory"] = "offline_template"
    hosted_diagnosis: ModelOpinion | None = None
    hosted_planning: PlanningOpinion | None = None
    configured_mode: Literal["offline", "amd_hosted"] = "offline"
    source_citations: Annotated[list[SourceCitation], Field(max_length=15)] = []
    model_attributions: Annotated[list[ModelAttribution], Field(max_length=2)] = []
    model_attempts: Annotated[list[ModelAttempt], Field(max_length=6)] = []
    amd_request_attempts: Annotated[int, Field(ge=0, le=6)] = 0
    amd_catalog_requests: Annotated[int, Field(ge=0, le=6)] = 0
    pinecone_query_attempts: Annotated[int, Field(ge=0, le=100)] = 0
    retrieved_source_ids: Annotated[list[str], Field(max_length=15)] = []
    retrieval_backend: Literal["local_faiss", "pinecone_semantic"] = "local_faiss"
    provider_failures: Annotated[list[str], Field(max_length=10)] = []
    hypotheses: list[DiagnosticHypothesis] = []
    candidates: Annotated[list[CandidatePlan], Field(max_length=3)] = []
    recovery_assessment: RecoveryAssessment | None = None
    traces: Annotated[list[GraphTrace], Field(max_length=80)] = []
    iteration: Annotated[int, Field(ge=0, le=3)] = 0
    max_iterations: Annotated[int, Field(ge=1, le=3)] = 3
    model_token_budget: Annotated[int, Field(ge=128, le=16384)] = 1024
    model_tokens_used: Annotated[int, Field(ge=0, le=16384)] = 0
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
    live_gates: Literal[
        "MI300X/Evolus/Pinecone BLOCKED",
        "MI300X/Evolus BLOCKED; Pinecone synthetic retrieval verified",
        "MI300X/Evolus BLOCKED; Pinecone real-world references verified",
        "MI300X/Evolus BLOCKED; Pinecone dual references verified",
    ] = "MI300X/Evolus/Pinecone BLOCKED"
