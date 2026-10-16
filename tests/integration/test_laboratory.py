import gzip
import hashlib
import json
from pathlib import Path

import pytest
from aegis_agents.laboratory import analysis_incident, load_ensemble, preview
from aegis_agents.optimizer import canonical
from aegis_api.app import create_app
from aegis_contracts.laboratory import PreviewRequest
from aegis_edge.runner import SupervisedTwin
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin, scenario_from_file
from fastapi.testclient import TestClient

LIBRARY = Path("/build/libaegis_twin.so")


def test_preview_native_reproducibility_shield_and_no_shared_state():
    request = PreviewRequest(scenario_id="scenario-090", seed=42)
    first = preview(request, LIBRARY)
    second = preview(request, LIBRARY)
    assert first.baseline_final_snapshot_sha256 == second.baseline_final_snapshot_sha256
    assert first.shielded_final_snapshot_sha256 == second.shielded_final_snapshot_sha256
    assert first.baseline_peak_c > 70 > first.shielded_peak_c
    assert first.detection_s == second.detection_s
    assert not first.operational_mutation and len(first.samples) == 60
    healthy = preview(PreviewRequest(scenario_id="scenario-000", seed=42), LIBRARY)
    assert healthy.detection_s is None
    assert healthy.baseline_final_snapshot_sha256 == healthy.shielded_final_snapshot_sha256


def test_futures_artifact_counts_actual_replay_and_tamper(tmp_path):
    directory = Path("data/futures")
    report = load_ensemble(directory, LIBRARY)
    rows = json.loads(gzip.decompress((directory / "rows.json.gz").read_bytes()))
    assert report.baseline_failed == sum(bool(r["baseline"]["violation_mask"]) for r in rows)
    assert report.intervention_failed == sum(
        bool(r["intervention"]["violation_mask"]) for r in rows
    )
    scenario = scenario_from_file(Path("data/scenarios"), "scenario-090", 42)
    source = SupervisedTwin(scenario, LIBRARY)
    try:
        for _ in range(600):
            _, status = source.step()
            if status and status.latched:
                break
        state = json.loads(source.incident_snapshot.payload_json)
        row = rows[0]
        state["scenario"].update(
            seed=row["seed"],
            target=row["target"],
            severity=row["severity"],
            fault_mask=156,
            start_s=0,
        )
        for cell in state["cells"]:
            cell[0] += row["offset_c"]
        state["coolant"] += row["offset_c"]
        raw = canonical(state).decode()
        assert hashlib.sha256(raw.encode()).hexdigest() == row["snapshot_sha256"]
        with NativeTwin(scenario, LIBRARY) as twin:
            twin.restore(canonical({"payload": raw, "sha256": row["snapshot_sha256"]}))
            for name, controls in (
                ("baseline", None),
                ("intervention", SafetyShield.emergency_controls()),
            ):
                actual = twin.rollout(controls, 600, 0).model_dump()
                assert all(actual[key] == value for key, value in row[name].items())
    finally:
        source.close()
    (tmp_path / "ensemble.json").write_bytes((directory / "ensemble.json").read_bytes())
    (tmp_path / "rows.json.gz").write_bytes(gzip.compress(b"[]"))
    with pytest.raises(ValueError, match="integrity"):
        load_ensemble(tmp_path, LIBRARY)


def test_analysis_http_auth_validation_and_no_operational_control(settings):
    with TestClient(create_app(settings)) as client:
        assert client.post("/api/v1/analysis/scenario", json={}).status_code == 401
        headers = {"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"}
        assert (
            client.post(
                "/api/v1/analysis/scenario", headers=headers, json={"scenario_id": "../../env"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/analysis/scenario",
                headers=headers,
                json={"scenario_id": "scenario-090", "controls": {}},
            ).status_code
            == 422
        )
        result = client.post(
            "/api/v1/analysis/scenario",
            headers=headers,
            json={"scenario_id": "scenario-090", "seed": 42},
        )
        assert result.status_code == 200 and not result.json()["operational_mutation"]
        assert (
            client.get("/api/v1/analysis/futures", headers=headers).json()["total_rollouts"]
            == 10000
        )


def test_private_analysis_incident_has_delivered_history_and_explicit_origin():
    record = analysis_incident(PreviewRequest(scenario_id="scenario-090", seed=42), LIBRARY)
    assert record.event.origin == "isolated_analysis"
    assert record.event.snapshot and record.event.observed_history
    assert record.event.observed and record.event.evidence
    with pytest.raises(ValueError, match="No detected anomaly"):
        analysis_incident(PreviewRequest(scenario_id="scenario-000", seed=42), LIBRARY)
