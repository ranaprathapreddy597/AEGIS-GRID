"""Real crypto/native gateway with an explicit in-memory storage test double.

Actual Mongo atomicity and browser verification are covered separately by E2E.
"""

import copy
import hashlib
import json
import time
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from aegis_agents.optimizer import canonical
from aegis_api.capabilities import public_key, sign
from aegis_api.gateway import SimulatorGateway, certificate, genesis
from aegis_contracts.authorization import ExecutionEnvelope, ProposedPlan, VerifiedCapability
from aegis_contracts.models import SimulatorControls

LIBRARY = Path("/build/libaegis_twin.so")
SEED = "isolated-gateway-test-signing-seed-" * 3


class ResourceDouble:
    def __init__(self, resource):
        self.value = resource

    def find_one(self, query):
        return copy.deepcopy(self.value)

    def update_one(self, query, update):
        if (
            query["version"] != self.value["version"]
            or query["snapshot.sha256"] != self.value["snapshot"]["sha256"]
        ):
            return SimpleNamespace(modified_count=0)
        self.value.update(copy.deepcopy(update["$set"]))
        self.value["version"] += update["$inc"]["version"]
        for name, value in update["$push"].items():
            self.value[name].append(copy.deepcopy(value))
        return SimpleNamespace(modified_count=1)


def fixture():
    resource = ResourceDouble(genesis(LIBRARY))
    state = json.loads(resource.value["snapshot"]["payload"])
    plan = ProposedPlan(
        action_id=str(uuid4()),
        expected_database_version=1,
        expected_state_version=state["version"],
        source_snapshot_sha256=resource.value["snapshot"]["sha256"],
        native_binary_sha256=hashlib.sha256(LIBRARY.read_bytes()).hexdigest(),
        safety_rollout_sha256=certificate(resource.value["snapshot"], LIBRARY),
        before_controls=SimulatorControls(
            pump=state["pump_target"], loads=state["load_targets"], valves=state["valve_targets"]
        ),
        controls=SimulatorControls(pump=1.0, loads=[0.0] * 6, valves=[1.0] * 6),
        expires_at=int(time.time()) + 600,
    )
    text = canonical(plan.model_dump()).decode()
    cap = VerifiedCapability(
        jti=str(uuid4()),
        action_id=plan.action_id,
        plan_sha256=hashlib.sha256(text.encode()).hexdigest(),
        expected_database_version=1,
        expected_state_version=plan.expected_state_version,
        iat=int(time.time()),
        exp=int(time.time()) + 60,
    )
    envelope = ExecutionEnvelope(action_json=text, capability=sign(cap, SEED))
    approval = {
        "status": "approved",
        "plan_sha256": cap.plan_sha256,
        "capability": envelope.capability,
        "action_json": text,
    }
    gateway = SimulatorGateway.__new__(SimulatorGateway)
    gateway.library, gateway.public_key = LIBRARY, public_key(SEED)
    gateway.client = SimpleNamespace(
        aegis=SimpleNamespace(
            sandbox_resources=resource,
            auth_proposals=SimpleNamespace(find_one=lambda query: approval),
        )
    )
    return gateway, envelope, resource, approval


def test_interrupted_private_simulation_rolls_back_then_atomic_receipt_and_retry():
    gateway, envelope, resource, _ = fixture()
    before = copy.deepcopy(resource.value)
    with pytest.raises(ValueError, match="before atomic commit"):
        gateway.execute(envelope, fail_before_commit=True)
    assert resource.value == before
    receipt = gateway.execute(envelope)
    assert receipt.database_version_after == 2 and receipt.native_version_after == 90
    assert resource.value["version"] == 2 and len(resource.value["nonces"]) == 1
    state = json.loads(resource.value["snapshot"]["payload"])
    assert all(cell[1] < 0.00001 for cell in state["cells"])
    assert gateway.execute(envelope) == receipt
    assert resource.value["version"] == 2 and len(resource.value["receipts"]) == 1


@pytest.mark.parametrize(
    "attack",
    [
        "unapproved",
        "stale_database",
        "changed_snapshot",
        "nonce_reuse",
        "changed_certificate",
        "native_binary",
    ],
)
def test_protected_gateway_refuses_before_any_state_change(attack):
    gateway, envelope, resource, approval = fixture()
    if attack == "unapproved":
        approval["status"] = "waiting_for_passkey"
    if attack == "stale_database":
        resource.value["version"] += 1
    if attack == "changed_snapshot":
        resource.value["snapshot"]["sha256"] = "f" * 64
    if attack == "nonce_reuse":
        payload = json.loads(
            __import__("base64").urlsafe_b64decode(envelope.capability.split(".")[0] + "==")
        )
        resource.value["nonces"].append(payload["jti"])
    if attack in {"changed_certificate", "native_binary"}:
        plan = ProposedPlan.model_validate_json(envelope.action_json)
        field = (
            "safety_rollout_sha256" if attack == "changed_certificate" else "native_binary_sha256"
        )
        plan = plan.model_copy(update={field: "f" * 64})
        text = canonical(plan.model_dump()).decode()
        from aegis_api.capabilities import verify

        _, cap = verify(envelope, public_key(SEED))
        cap = cap.model_copy(update={"plan_sha256": hashlib.sha256(text.encode()).hexdigest()})
        envelope = ExecutionEnvelope(action_json=text, capability=sign(cap, SEED))
        approval.update(
            plan_sha256=cap.plan_sha256, capability=envelope.capability, action_json=text
        )
    before = copy.deepcopy(resource.value)
    with pytest.raises(ValueError):
        gateway.execute(envelope)
    assert resource.value == before
