"""Real native/crypto tests with labeled storage and hosted-opinion test doubles.

These do NOT establish live AMD or WebAuthn approval. Browser proof is separate.
"""

import copy
import json
import time
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from aegis_agents.optimizer import optimize
from aegis_api.capabilities import public_key
from aegis_api.commissioned_gateway import CommissionedGateway, receipt_digest, sign, verify
from aegis_contracts.authorization import ExecutionEnvelope
from aegis_contracts.commissioned import (
    CommissionedCapability,
    CommissionedPlan,
    CommissionedReport,
)
from aegis_contracts.models import IncidentRecord
from aegis_edge.commissioning import RULES_SHA256, canonical, genesis, sha, stop_certificate
from aegis_edge.sentinel import SafetyShield

LIBRARY = Path("/build/libaegis_twin.so")
SEED = "commissioned-native-test-key-only-" * 3
pytestmark = pytest.mark.skipif(not LIBRARY.exists(), reason="Native QA image required")


class ResourceDouble:
    def __init__(self, value):
        self.value = value

    def find_one(self, query):
        return copy.deepcopy(self.value)

    def update_one(self, query, update):
        if (
            query["version"] != self.value["version"]
            or query["snapshot.sha256"] != self.value["snapshot"]["sha256"]
            or self.value["receipts"]
            or query["nonces"]["$ne"] in self.value["nonces"]
        ):
            return SimpleNamespace(modified_count=0)
        self.value.update(copy.deepcopy(update["$set"]))
        self.value["version"] += 1
        for name, value in update["$push"].items():
            self.value[name].append(copy.deepcopy(value))
        return SimpleNamespace(modified_count=1)


@pytest.fixture(scope="module")
def initial():
    resource = genesis(LIBRARY)
    record = IncidentRecord.model_validate(resource["incident"])
    assessment = optimize(record, LIBRARY)
    certificate = stop_certificate(resource["snapshot"], LIBRARY)
    # Explicit local test opinions, NOT actual provider responses.
    citation = dict(
        reference_id="unit-reference",
        title="Unit fixture",
        source="unit",
        revision="1",
        source_sha256="a" * 64,
        license="unit fixture",
        attribution="test",
        synthetic=True,
        applicability="synthetic_simulator_evidence",
    )
    attrs = [
        dict(
            role=r,
            requested_model="DeepSeek-V4-Flash",
            served_model="self-dploy/DeepSeek-V4-Flash",
            attempted_models=["DeepSeek-V4-Flash"],
            latency_ms=0.0,
            prompt_tokens=0,
            completion_tokens=0,
        )
        for r in ("diagnosis", "planning")
    ]
    report = CommissionedReport(
        investigation_id=str(uuid4()),
        incident_id=record.incident_id,
        rules_sha256=RULES_SHA256,
        report_sha256="0" * 64,
        status="awaiting_approval",
        diagnosis={
            "assessment": "investigate",
            "hypotheses": ["sensor_bias"],
            "evidence_ids": ["observed", "residuals"],
        },
        planning={
            "recommendation": "emergency_stop",
            "evidence_ids": ["candidate_evaluations", "retrieved_sources"],
        },
        model_attributions=attrs,
        source_citations=[
            {**citation, "namespace": ns}
            for ns in ("real-world-v1", "aegis-synthetic-v1-6e4d75051cbcaf1e")
        ],
        assessment=assessment,
        certificate=certificate,
        unsafe_challenger_rejected=True,
        meaningful_diagnosis=True,
        grounded_planning=True,
        candidate_round=2,
        proposed_controls=SafetyShield.emergency_controls(),
        planning_evidence={"candidate_evaluations": {"emergency_stop": {"feasible": True}}},
    )
    report = report.model_copy(
        update={"report_sha256": sha(canonical(report.model_dump(exclude={"report_sha256"})))}
    )
    return resource, report


def setup(initial):
    resource, report = copy.deepcopy(initial)
    resource = ResourceDouble(resource)
    state = json.loads(resource.value["snapshot"]["payload"])
    now = int(time.time())
    plan = CommissionedPlan(
        action_id=str(uuid4()),
        nonce=str(uuid4()),
        incident_id=resource.value["incident_id"],
        investigation_id=report.investigation_id,
        investigation_sha256=report.report_sha256,
        rules_sha256=RULES_SHA256,
        expected_database_version=1,
        expected_state_version=state["version"],
        source_snapshot_sha256=resource.value["snapshot"]["sha256"],
        native_binary_sha256=report.certificate.native_binary_sha256,
        safety_rollout_sha256=report.certificate.sha256,
        controls=SafetyShield.emergency_controls(),
        expires_at=now + 600,
    )
    raw = canonical(plan.model_dump()).decode()
    cap = CommissionedCapability(
        jti=plan.nonce,
        action_id=plan.action_id,
        plan_sha256=sha(raw.encode()),
        incident_id=plan.incident_id,
        rules_sha256=RULES_SHA256,
        expected_database_version=1,
        expected_state_version=plan.expected_state_version,
        iat=now,
        exp=now + 60,
    )
    env = ExecutionEnvelope(action_json=raw, capability=sign(cap, SEED))
    approval = dict(
        status="approved", plan_sha256=cap.plan_sha256, capability=env.capability, action_json=raw
    )
    stored_report = {"report": report.model_dump()}
    gateway = CommissionedGateway.__new__(CommissionedGateway)
    gateway.library, gateway.public_key = LIBRARY, public_key(SEED)
    gateway.client = SimpleNamespace(
        aegis=SimpleNamespace(
            commissioned_resources=resource,
            commissioned_proposals=SimpleNamespace(find_one=lambda q: approval),
            commissioned_reports=SimpleNamespace(find_one=lambda q: stored_report),
        )
    )
    return gateway, env, resource, approval, stored_report


def test_partial_failure_discards_copy_then_cools_all_cells_and_refuses_replay(initial):
    gateway, env, resource, _, _ = setup(initial)
    before = copy.deepcopy(resource.value)
    with pytest.raises(ValueError, match="before atomic commit"):
        gateway.execute(env, fail_before_commit=True)
    assert resource.value == before
    receipt = gateway.execute(env)
    assert receipt.receipt_sha256 == receipt_digest(receipt)
    assert receipt.database_version_after == 2
    assert receipt.native_version_after == receipt.native_version_before + 120
    assert max(receipt.temperatures_after_c) < max(receipt.temperatures_before_c)
    assert receipt.maximum_temperature_c < 70 and receipt.fault_retained
    assert len(gateway.resource()["receipts"]) == 1
    with pytest.raises(ValueError, match="replay/repeat"):
        gateway.execute(env)
    assert len(resource.value["receipts"]) == 1


@pytest.mark.parametrize(
    "attack",
    [
        "unapproved",
        "state",
        "snapshot",
        "nonce",
        "incident",
        "rules",
        "certificate",
        "binary",
        "report",
        "abstention",
        "receipt_tamper",
    ],
)
def test_native_gateway_refuses_all_substitutions_without_commit(initial, attack):
    gateway, env, resource, approval, stored = setup(initial)
    if attack == "unapproved":
        approval["status"] = "waiting_for_passkey"
    if attack == "state":
        resource.value["version"] += 1
    if attack == "snapshot":
        resource.value["snapshot"]["sha256"] = "f" * 64
    if attack == "nonce":
        resource.value["nonces"].append(verify(env, gateway.public_key)[1].jti)
    if attack == "incident":
        resource.value["incident_id"] = "f" * 64
    if attack == "rules":
        resource.value["rules_sha256"] = "f" * 64
    if attack in {"certificate", "binary", "report"}:
        plan, cap = verify(env, gateway.public_key)
        field = {
            "certificate": "safety_rollout_sha256",
            "binary": "native_binary_sha256",
            "report": "investigation_sha256",
        }[attack]
        plan = plan.model_copy(update={field: "f" * 64})
        raw = canonical(plan.model_dump()).decode()
        cap = cap.model_copy(update={"plan_sha256": sha(raw.encode())})
        env = ExecutionEnvelope(action_json=raw, capability=sign(cap, SEED))
        approval.update(plan_sha256=cap.plan_sha256, capability=env.capability, action_json=raw)
    if attack == "abstention":
        stored["report"]["diagnosis"] = {
            "assessment": "insufficient_evidence",
            "hypotheses": [],
            "evidence_ids": [],
        }
    if attack == "receipt_tamper":
        gateway.execute(env)
        resource.value["receipts"][0]["temperatures_after_c"][0] += 1
    before = copy.deepcopy(resource.value)
    with pytest.raises(ValueError):
        gateway.execute(env)
    assert resource.value == before
