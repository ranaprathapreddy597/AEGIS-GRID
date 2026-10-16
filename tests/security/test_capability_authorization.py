import hashlib
import json
import time
from uuid import uuid4

import pytest
from aegis_agents.optimizer import canonical
from aegis_api.capabilities import decode, encode, private_key, public_key, sign, verify
from aegis_contracts.authorization import ExecutionEnvelope, ProposedPlan, VerifiedCapability
from aegis_contracts.models import SimulatorControls

SEED = "isolated-cryptographic-test-seed-" * 3


def proposal():
    return ProposedPlan(
        action_id=str(uuid4()),
        expected_database_version=1,
        expected_state_version=30,
        source_snapshot_sha256="a" * 64,
        native_binary_sha256="b" * 64,
        safety_rollout_sha256="c" * 64,
        before_controls=SimulatorControls(pump=0.85, loads=[0.7] * 6, valves=[1.0] * 6),
        controls=SimulatorControls(pump=1.0, loads=[0.0] * 6, valves=[1.0] * 6),
        expires_at=int(time.time()) + 600,
    )


def envelope(plan=None, cap_changes=None):
    plan = plan or proposal()
    raw = canonical(plan.model_dump()).decode()
    now = int(time.time())
    cap = VerifiedCapability(
        jti=str(uuid4()),
        action_id=plan.action_id,
        plan_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        expected_database_version=plan.expected_database_version,
        expected_state_version=plan.expected_state_version,
        iat=now,
        exp=now + 60,
    )
    value = {**cap.model_dump(), **(cap_changes or {})}
    payload = canonical(value)
    signed = encode(payload) + "." + encode(private_key(SEED).sign(payload))
    return ExecutionEnvelope(action_json=raw, capability=signed)


def test_actual_ed25519_signature_and_immutable_action_binding():
    action = envelope()
    plan, cap = verify(action, public_key(SEED))
    assert plan.action_id == cap.action_id
    assert sign(cap, SEED) == action.capability
    with pytest.raises(ValueError):
        verify(action, public_key("another-isolated-test-seed-" * 3))
    with pytest.raises(ValueError):
        verify(
            action.model_copy(
                update={"action_json": action.action_json.replace('"pump":1.0', '"pump":0.0')}
            ),
            public_key(SEED),
        )
    payload, signed = action.capability.split(".")
    signature = decode(signed)
    changed = encode(bytes([signature[0] ^ 1]) + signature[1:])
    with pytest.raises(ValueError):
        verify(
            action.model_copy(update={"capability": payload + "." + changed}),
            public_key(SEED),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"exp": 1},
        {"iat": 1},
        {"iat": int(time.time()) + 100},
        {"sub": "another-user"},
        {"aud": "unapproved-tool"},
        {"iss": "model"},
        {"user_verification": False},
        {"scope": "physical-plant"},
        {"expected_database_version": 99},
        {"expected_state_version": 999},
        {"plan_sha256": "f" * 64},
        {"resource_id": "live-edge"},
    ],
)
def test_even_signed_wrong_user_scope_expiry_and_state_are_refused(changes):
    with pytest.raises(ValueError):
        verify(envelope(cap_changes=changes), public_key(SEED))


def test_signed_unsafe_or_modified_action_cannot_override_independent_schema_policy():
    valid = envelope()
    plan, cap = verify(valid, public_key(SEED))
    raw = json.loads(valid.action_json)
    raw["controls"]["loads"] = [1.0] * 6
    text = canonical(raw).decode()
    changed = cap.model_copy(update={"plan_sha256": hashlib.sha256(text.encode()).hexdigest()})
    with pytest.raises(ValueError):
        verify(
            ExecutionEnvelope(action_json=text, capability=sign(changed, SEED)), public_key(SEED)
        )
    assert plan.controls.loads == [0.0] * 6
