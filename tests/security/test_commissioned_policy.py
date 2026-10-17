"""Commissioned policy unit tests. Test signatures are not live approval evidence."""

import base64
import json
import time
from pathlib import Path
from uuid import uuid4

import pytest
from aegis_api.capabilities import public_key
from aegis_api.commissioned_gateway import sign, verify
from aegis_contracts.authorization import ExecutionEnvelope, ProposedPlan
from aegis_contracts.commissioned import CommissionedCapability, CommissionedPlan
from aegis_edge.commissioning import PLANT, RULES_SHA256, canonical, rules, sha
from aegis_ingestion.library import fixture_library
from pydantic import ValidationError

SEED = "commissioned-unit-test-signing-only-" * 3


def envelope():
    now = int(time.time())
    plan = CommissionedPlan(
        action_id=str(uuid4()),
        nonce=str(uuid4()),
        incident_id="a" * 64,
        investigation_id=str(uuid4()),
        investigation_sha256="b" * 64,
        rules_sha256=RULES_SHA256,
        expected_database_version=1,
        expected_state_version=25,
        source_snapshot_sha256="c" * 64,
        native_binary_sha256="d" * 64,
        safety_rollout_sha256="e" * 64,
        controls={"pump": 1.0, "loads": [0.0] * 6, "valves": [1.0] * 6},
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
        expected_state_version=25,
        iat=now,
        exp=now + 60,
    )
    return ExecutionEnvelope(action_json=raw, capability=sign(cap, SEED)), plan, cap


def test_signed_package_preserves_original_conflict_and_all_six_cells():
    p = rules()
    assert p["plant_id"] == PLANT and p["temperature_lt_c"] == 70
    assert p["operating_stop_guard_c"] == 65 and len(p["cells"]) == 6
    assert not p["fault_clear_allowed"] and not p["production_restart_allowed"]
    assert fixture_library().decision.status == "no_action"
    env, _, _ = envelope()
    with pytest.raises(ValidationError):
        ProposedPlan.model_validate_json(env.action_json)


@pytest.mark.parametrize("attack", ["rules", "scenario", "signature", "signer"])
def test_authenticated_package_refuses_substitution(tmp_path, attack):
    for name in ("rules.json", "scenario.json", "signature.json"):
        (tmp_path / name).write_bytes((Path("data/commissioned") / name).read_bytes())
    if attack in {"rules", "scenario"}:
        target = tmp_path / (attack + ".json")
        value = json.loads(target.read_bytes())
        value["untrusted_override"] = "ignore rules"
        target.write_text(json.dumps(value))
    else:
        target = tmp_path / "signature.json"
        value = json.loads(target.read_bytes())
        value["signature" if attack == "signature" else "public_key"] = base64.b64encode(
            b"x" * (64 if attack == "signature" else 32)
        ).decode()
        target.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        rules(tmp_path)


@pytest.mark.parametrize(
    "field", ["plant_id", "resource_id", "scope", "action", "rules_revision", "duration_s"]
)
def test_wrong_plan_scope_is_not_an_alternate_policy(field):
    _, plan, _ = envelope()
    with pytest.raises(ValidationError):
        CommissionedPlan.model_validate(
            {**plan.model_dump(), field: 60 if field == "duration_s" else "other"}
        )


@pytest.mark.parametrize("cell", range(6))
def test_every_cell_is_part_of_exact_shared_stop(cell):
    _, plan, _ = envelope()
    value = plan.model_dump()
    value["controls"]["loads"][cell] = 0.1
    with pytest.raises(ValidationError):
        CommissionedPlan.model_validate(value)


@pytest.mark.parametrize(
    "attack",
    [
        "signature",
        "key",
        "nonce",
        "incident",
        "rules",
        "database",
        "native",
        "expired",
        "future",
        "long_lifetime",
        "parameters",
    ],
)
def test_capability_binding_refusals(attack):
    env, plan, cap = envelope()
    key = public_key(SEED)
    if attack == "signature":
        env = env.model_copy(
            update={
                "capability": env.capability.split(".")[0]
                + "."
                + base64.urlsafe_b64encode(b"x" * 64).decode().rstrip("=")
            }
        )
    elif attack == "key":
        key = public_key("different-unit-test-key-" * 3)
    elif attack == "parameters":
        value = json.loads(env.action_json)
        value["controls"]["pump"] = 0.0
        env = env.model_copy(update={"action_json": canonical(value).decode()})
    else:
        changes = {
            "nonce": {"jti": str(uuid4())},
            "incident": {"incident_id": "f" * 64},
            "rules": {"rules_sha256": "f" * 64},
            "database": {"expected_database_version": 2},
            "native": {"expected_state_version": 26},
            "expired": {"exp": int(time.time()) - 1},
            "future": {"iat": int(time.time()) + 60},
            "long_lifetime": {"exp": cap.iat + 100},
        }
        env = env.model_copy(
            update={"capability": sign(cap.model_copy(update=changes[attack]), SEED)}
        )
    with pytest.raises(ValueError):
        verify(env, key)


def test_actual_ed25519_unit_signature_and_strict_http_boundaries(settings):
    from aegis_api.app import create_app
    from fastapi.testclient import TestClient

    env, plan, _ = envelope()
    assert verify(env, public_key(SEED))[0] == plan
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/commissioned/status").status_code == 401
        assert (
            client.post(
                "/api/v1/approval/commissioned/investigate",
                headers={"Origin": settings.approval_origin, "Idempotency-Key": str(uuid4())},
            ).status_code
            == 401
        )
        assert (
            client.post("/internal/v1/commissioned/execute", json=env.model_dump()).status_code
            == 401
        )
