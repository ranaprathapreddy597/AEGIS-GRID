"""Separate commissioned replay scope. Original authorization contracts are unchanged."""

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from aegis_contracts.authorization import Identifier
from aegis_contracts.inference import ModelOpinion, PlanningOpinion
from aegis_contracts.investigation import ModelAttribution, SourceCitation
from aegis_contracts.models import Contract, FiniteFloat, SimulatorControls
from aegis_contracts.optimization import Digest, RecoveryAssessment

Plant = Literal["commissioned-simulator-01"]
Scope = Literal["commissioned_six_cell_incident"]
Revision = Literal["commissioned-stop-v1"]


class StopCertificate(Contract):
    sha256: Digest
    snapshot_sha256: Digest
    rules_sha256: Digest
    native_binary_sha256: Digest
    maximum_temperature_c: FiniteFloat
    maximum_pressure_kpa: FiniteFloat
    maximum_feeder_power_w: FiniteFloat
    duration_s: Literal[120] = 120
    cells_checked: Literal[6] = 6


class CommissionedReport(Contract):
    plant_id: Plant = "commissioned-simulator-01"
    investigation_id: Identifier
    incident_id: Digest
    rules_sha256: Digest
    rules_revision: Revision = "commissioned-stop-v1"
    report_sha256: Digest
    status: Literal["blocked", "awaiting_approval"] = "blocked"
    diagnosis: ModelOpinion | None = None
    planning: PlanningOpinion | None = None
    model_attributions: list[ModelAttribution] = []
    source_citations: list[SourceCitation] = []
    assessment: RecoveryAssessment | None = None
    certificate: StopCertificate | None = None
    unsafe_challenger_rejected: bool = False
    meaningful_diagnosis: bool = False
    grounded_planning: bool = False
    blockers: list[str] = []
    traces: list[str] = []
    candidate_round: Annotated[int, Field(ge=0, le=2)] = 0
    proposed_controls: SimulatorControls | None = None
    provider_diagnostics: list[dict[str, Any]] = []
    amd_request_attempts: int = 0
    amd_catalog_requests: int = 0
    reserved_tokens: int = 0
    pinecone_operations: list[dict[str, Any]] = []
    diagnosis_evidence: dict[str, Any] = {}
    planning_evidence: dict[str, Any] = {}
    physical_io: Literal[False] = False
    recovery_scope: Literal["frozen_native_replay_safe_stop_cooldown"] = (
        "frozen_native_replay_safe_stop_cooldown"
    )


class CommissionedPlan(Contract):
    action_id: Identifier
    tenant_id: Literal["local"] = "local"
    plant_id: Plant = "commissioned-simulator-01"
    resource_id: Plant = "commissioned-simulator-01"
    scope: Scope = "commissioned_six_cell_incident"
    action: Literal["simulator.commissioned_stop"] = "simulator.commissioned_stop"
    rules_revision: Revision = "commissioned-stop-v1"
    rules_sha256: Digest
    incident_id: Digest
    investigation_id: Identifier
    investigation_sha256: Digest
    nonce: Identifier
    expected_database_version: Annotated[int, Field(ge=1, le=10000)]
    expected_state_version: Annotated[int, Field(ge=1)]
    source_snapshot_sha256: Digest
    native_binary_sha256: Digest
    safety_rollout_sha256: Digest
    controls: SimulatorControls
    duration_s: Literal[120] = 120
    expires_at: Annotated[int, Field(ge=1)]

    @model_validator(mode="after")
    def exact_shared_stop(self) -> "CommissionedPlan":
        if self.controls != SimulatorControls(pump=1, loads=[0] * 6, valves=[1] * 6):
            raise ValueError("All six cells must receive the exact independent stop")
        return self


class CommissionedCapability(Contract):
    iss: Literal["aegis-commissioned-approver"] = "aegis-commissioned-approver"
    aud: Literal["aegis-commissioned-executor"] = "aegis-commissioned-executor"
    sub: Literal["local-owner"] = "local-owner"
    jti: Identifier
    action_id: Identifier
    plan_sha256: Digest
    plant_id: Plant = "commissioned-simulator-01"
    resource_id: Plant = "commissioned-simulator-01"
    scope: Scope = "commissioned_six_cell_incident"
    incident_id: Digest
    rules_revision: Revision = "commissioned-stop-v1"
    rules_sha256: Digest
    expected_database_version: Annotated[int, Field(ge=1)]
    expected_state_version: Annotated[int, Field(ge=1)]
    iat: Annotated[int, Field(ge=1)]
    exp: Annotated[int, Field(ge=1)]
    user_verification: Literal[True] = True


class CommissionedReceipt(Contract):
    receipt_format: Literal["commissioned-receipt-v1"] = "commissioned-receipt-v1"
    plant_id: Plant = "commissioned-simulator-01"
    incident_id: Digest
    action_id: Identifier
    nonce: Identifier
    plan_sha256: Digest
    rules_sha256: Digest
    rules_revision: Revision = "commissioned-stop-v1"
    previous_receipt_sha256: Digest
    receipt_sha256: Digest
    database_version_before: int
    database_version_after: int
    native_version_before: int
    native_version_after: int
    snapshot_sha256_before: Digest
    snapshot_sha256_after: Digest
    native_binary_sha256: Digest
    temperatures_before_c: Annotated[list[FiniteFloat], Field(min_length=6, max_length=6)]
    temperatures_after_c: Annotated[list[FiniteFloat], Field(min_length=6, max_length=6)]
    maximum_temperature_c: FiniteFloat
    duration_s: Literal[120] = 120
    fault_retained: Literal[True] = True
    physical_io: Literal[False] = False
    outcome: Literal["simulated_safe_stop_cooldown"] = "simulated_safe_stop_cooldown"
    authorization: Literal["WebAuthn_user_verified"] = "WebAuthn_user_verified"


class CommissionedView(Contract):
    action_id: Identifier
    plan_sha256: Digest
    action_json: str
    status: Literal["waiting_for_passkey", "approved", "executed"]
    receipt: CommissionedReceipt | None = None


class CommissionedStatus(Contract):
    enabled: bool = False
    plant_id: Plant = "commissioned-simulator-01"
    incident_id: Digest
    rules_sha256: Digest
    rules_revision: Revision = "commissioned-stop-v1"
    rule_package: dict[str, Any]
    database_version: int
    native_state_version: int
    snapshot_sha256: Digest
    temperatures_c: Annotated[list[FiniteFloat], Field(min_length=6, max_length=6)]
    receipts: list[CommissionedReceipt]
    mode: Literal["frozen_native_replay_simulator_only"] = "frozen_native_replay_simulator_only"
