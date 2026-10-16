"""One exact simulator-only authorization scope; enterprise operations stay closed."""

import json
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from aegis_contracts.models import Contract, SimulatorControls
from aegis_contracts.optimization import Digest

Identifier = Annotated[
    str, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
]


class MaintenanceChange(Contract):
    record_id: Literal["local-sandbox-maintenance"] = "local-sandbox-maintenance"
    expected_record_version: Annotated[int, Field(ge=0, le=256)]
    status_before: Literal["not_recorded", "safety_stop_verified"]
    status_after: Literal["safety_stop_verified"] = "safety_stop_verified"
    reason: Literal["Independent native emergency-stop verification"] = (
        "Independent native emergency-stop verification"
    )


class ProposedPlan(Contract):
    action_id: Identifier
    tenant_id: Literal["local"] = "local"
    resource_id: Literal["authorization-sandbox-01"] = "authorization-sandbox-01"
    action: Literal["simulator.emergency_stop", "simulator.stop_and_record_maintenance"] = (
        "simulator.emergency_stop"
    )
    maintenance: MaintenanceChange | None = None
    scope: Literal["isolated_authorization_sandbox"] = "isolated_authorization_sandbox"
    risk: Literal["simulator_only"] = "simulator_only"
    evidence_policy: Literal["authorization-test-sandbox-v1"] = "authorization-test-sandbox-v1"
    expected_database_version: Annotated[int, Field(ge=1, le=10000)]
    expected_state_version: Annotated[int, Field(ge=1, le=1000000000)]
    source_snapshot_sha256: Digest
    native_binary_sha256: Digest
    safety_rollout_sha256: Digest
    before_controls: SimulatorControls
    controls: SimulatorControls
    compensation: Literal["retain_committed_state_or_emergency_stop"] = (
        "retain_committed_state_or_emergency_stop"
    )
    expires_at: Annotated[int, Field(ge=1)]

    @model_validator(mode="after")
    def exact_stop(self) -> "ProposedPlan":
        if self.controls != SimulatorControls(pump=1.0, loads=[0.0] * 6, valves=[1.0] * 6):
            raise ValueError("Independent authorization scope only permits the exact safe stop")
        if (self.action == "simulator.stop_and_record_maintenance") != (
            self.maintenance is not None
        ):
            raise ValueError("Maintenance mutation must be explicit in the signed action")
        return self


class VerifiedCapability(Contract):
    iss: Literal["aegis-local-approver"] = "aegis-local-approver"
    aud: Literal["aegis-independent-executor"] = "aegis-independent-executor"
    sub: Literal["local-owner"] = "local-owner"
    jti: Identifier
    action_id: Identifier
    plan_sha256: Digest
    resource_id: Literal["authorization-sandbox-01"] = "authorization-sandbox-01"
    scope: Literal["isolated_authorization_sandbox"] = "isolated_authorization_sandbox"
    expected_database_version: Annotated[int, Field(ge=1, le=10000)]
    expected_state_version: Annotated[int, Field(ge=1, le=1000000000)]
    iat: Annotated[int, Field(ge=1)]
    exp: Annotated[int, Field(ge=1)]
    user_verification: Literal[True] = True


class ExecutionEnvelope(Contract):
    action_json: Annotated[str, Field(max_length=16384)]
    capability: Annotated[str, Field(max_length=8192)]


class MutationReceipt(Contract):
    receipt_format: Literal["sandbox-receipt-v1", "sandbox-receipt-v2"] = "sandbox-receipt-v1"
    maintenance_record_sha256: Digest | None = None
    tool: Literal["isolated_simulator", "local_mongo_and_simulator"] = "isolated_simulator"
    receipt_sha256: Digest
    previous_receipt_sha256: Digest
    action_id: Identifier
    nonce: Identifier
    plan_sha256: Digest
    resource_id: Literal["authorization-sandbox-01"] = "authorization-sandbox-01"
    database_version_before: int
    database_version_after: int
    native_version_before: int
    native_version_after: int
    snapshot_sha256_after: Digest
    native_binary_sha256: Digest
    outcome: Literal["applied_to_isolated_sandbox"] = "applied_to_isolated_sandbox"
    authorized_user: Literal["local-owner"] = "local-owner"
    authorization: Literal["WebAuthn_user_verified"] = "WebAuthn_user_verified"


class ApprovalView(Contract):
    action_id: Identifier
    plan_sha256: Digest
    action_json: str
    status: Literal["waiting_for_passkey", "approved", "executed"]
    receipt: MutationReceipt | None = None


def receipt_hash_fields(receipt: MutationReceipt) -> dict[str, Any]:
    """Preserve original receipt-v1 fingerprints during additive schema upgrades."""
    content = receipt.model_dump()
    content.pop("receipt_sha256")
    if receipt.receipt_format == "sandbox-receipt-v1":
        for name in ("receipt_format", "maintenance_record_sha256", "tool"):
            content.pop(name)
    return content


class ApprovalChallenge(Contract):
    ceremony_id: Identifier
    options: dict[str, Any]
    bound_plan_sha256: Digest | None = None


class CredentialResponse(Contract):
    ceremony_id: Identifier
    credential: dict[str, Any]

    @model_validator(mode="after")
    def bounded_credential(self) -> "CredentialResponse":
        if len(json.dumps(self.credential, allow_nan=False)) > 24000:
            raise ValueError("Credential response exceeds bound")
        return self


class ApprovalSession(Contract):
    user: Literal["local-owner"] = "local-owner"
    enrolled_credentials: int
    expires_at: int
    canonical_origin: str


class ExecuteRequest(Contract):
    plan_sha256: Digest
