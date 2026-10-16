import hashlib
import json
from pathlib import Path

import pytest
from aegis_agents.optimizer import grid, optimize, uncertainty, verify_artifact
from aegis_contracts.models import IncidentSnapshot, SimulatorControls
from aegis_edge.twin import NativeTwin, scenario_from_file
from test_forensic_graph import native_record

LIBRARY = Path("/build/libaegis_twin.so")


def test_native_rollout_is_non_mutating_and_matches_standard_stepping():
    scenario = scenario_from_file(Path("data/scenarios"), "scenario-090")
    controls = SimulatorControls(pump=1.0, loads=[0.0] * 6, valves=[1.0] * 6)
    with NativeTwin(scenario, LIBRARY) as twin:
        twin.step(1.0)
        before = twin.snapshot()
        result = twin.rollout(controls, 120, 10)
        assert twin.snapshot() == before
        assert twin.rollout(controls, 120, 10) == result
        initial = json.loads(twin.raw())["ground_truth"]
        twin.controls(twin.current_version(), controls)
        for _ in range(120):
            frame = twin.step(1.0)
        assert result.production_units == pytest.approx(
            frame.ground_truth.production_units - initial["production_units"], abs=1e-9
        )
        assert result.energy_kwh == pytest.approx(
            (frame.ground_truth.energy_j - initial["energy_j"]) / 3600000, abs=1e-9
        )
        assert result.samples[-1].maximum_temperature_c == max(
            cell.temperature_c for cell in frame.ground_truth.cells
        )
        assert result.violation_mask == 0 and result.maximum_ramp_excess < 1e-9
        for invalid in (0, 1201, True):
            with pytest.raises(ValueError):
                twin.rollout(None, invalid)


def test_red_search_coverage_minimax_replay_and_actual_baseline_improvement():
    record = native_record()
    report = optimize(record, LIBRARY)
    verify_artifact(report)
    assert len(grid()) == 11 and len(report.cases) == 37
    assert {case.target for case in report.cases} == set(range(6))
    assert {case.severity for case in report.cases}.issuperset({0.5, 0.8, 1.0})
    assert len({case.snapshot_sha256 for case in report.cases}) == 37
    assert all(item.checked_cases == 37 for item in report.candidates)
    assert report.total_rollouts == 409 and report.native_substeps == 4908000
    assert report.native_binary_sha256 == hashlib.sha256(LIBRARY.read_bytes()).hexdigest()
    unsafe = next(item for item in report.candidates if item.candidate_id == "planted-unsafe")
    assert not unsafe.feasible and unsafe.failed_cases > 0 and unsafe.counterexamples
    selected = next(
        item for item in report.candidates if item.candidate_id == report.selected_candidate_id
    )
    assert selected.feasible
    assert selected.worst_objective == min(
        item.worst_objective for item in report.candidates if item.feasible
    )
    assert report.intervention.violation_mask == 0
    assert report.baseline.maximum_temperature_c > 80
    assert report.intervention.maximum_temperature_c < report.baseline.maximum_temperature_c
    assert report.executable is False and report.manual_action_gate == "BLOCKED"
    assert optimize(record, LIBRARY) == report
    with pytest.raises(ValueError, match="integrity"):
        verify_artifact(report.model_copy(update={"selected_candidate_id": "planted-unsafe"}))


def test_hot_initial_state_abstains_and_prior_hashes_restore():
    record = native_record()
    snapshot = record.event.snapshot
    for case, envelope in uncertainty(snapshot.payload_json):
        with NativeTwin(
            scenario_from_file(Path("data/scenarios"), "scenario-000"), LIBRARY
        ) as twin:
            twin.restore(envelope)
            restored = json.loads(json.loads(twin.snapshot())["payload"])
            assert restored["scenario"]["seed"] == case.seed
    payload = json.loads(snapshot.payload_json)
    payload["cells"][0][0] = 80.0
    raw = json.dumps(payload)
    hot = snapshot.model_copy(
        update={"payload_json": raw, "sha256": hashlib.sha256(raw.encode()).hexdigest()}
    )
    hot = IncidentSnapshot.model_validate(hot.model_dump())
    report = optimize(
        record.model_copy(update={"event": record.event.model_copy(update={"snapshot": hot})}),
        LIBRARY,
    )
    assert report.status == "abstained" and report.total_rollouts == 0
    assert report.selected_candidate_id is None and not report.executable
    verify_artifact(report)
