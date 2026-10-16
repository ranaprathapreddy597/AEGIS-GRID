import hashlib
import json

import pytest
from aegis_api.storage import StorageUnavailable, TelemetryStore
from aegis_contracts.models import EdgeIncident, IncidentSnapshot
from pydantic import ValidationError


def test_snapshot_hash_revision_and_version_are_verified():
    payload = json.dumps({"format": "aegis-snapshot-v3", "version": 5})
    valid = {
        "state_version": 5,
        "payload_json": payload,
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
    }
    assert IncidentSnapshot.model_validate(valid).state_version == 5
    for changes in [
        {"state_version": 6},
        {"sha256": "0" * 64},
        {"payload_json": "[]", "sha256": hashlib.sha256(b"[]").hexdigest()},
    ]:
        with pytest.raises(ValidationError):
            IncidentSnapshot.model_validate({**valid, **changes})


def test_incident_rejects_injected_tenant_commands_or_invalid_ids():
    valid = {
        "event_id": "a" * 64,
        "run_id": "00000000-0000-0000-0000-000000000001",
        "state_version": 1,
        "simulation_time_s": 0.5,
        "kind": "anomaly",
        "evidence": [],
    }
    for changes in [
        {"tenant_id": "foreign"},
        {"commands": [{"pump": 0}]},
        {"event_id": {"$ne": None}},
    ]:
        with pytest.raises(ValidationError):
            EdgeIncident.model_validate({**valid, **changes})


def test_disabled_storage_is_not_a_fake_persistent_success(settings):
    store = TelemetryStore(settings)
    with pytest.raises(StorageUnavailable):
        store._reader()


def test_incident_refuses_a_valid_snapshot_for_a_different_state_version():
    payload = json.dumps({"format": "aegis-snapshot-v3", "version": 5})
    snapshot = IncidentSnapshot(
        state_version=5, payload_json=payload, sha256=hashlib.sha256(payload.encode()).hexdigest()
    )
    with pytest.raises(ValidationError):
        EdgeIncident(
            event_id="a" * 64,
            run_id="00000000-0000-0000-0000-000000000001",
            state_version=6,
            simulation_time_s=3.0,
            kind="anomaly",
            evidence=[],
            snapshot=snapshot,
        )
