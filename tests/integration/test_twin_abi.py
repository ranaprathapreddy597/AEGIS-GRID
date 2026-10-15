import hashlib
import json
from pathlib import Path

import pytest
from aegis_contracts.models import SimulatorControls
from aegis_edge.twin import NativeTwin, scenario_from_file

DIRECTORY = Path("data/scenarios")


@pytest.mark.parametrize("index", range(100))
def test_all_fixtures_replay_snapshot_and_conserve(index):
    scenario = scenario_from_file(DIRECTORY, f"scenario-{index:03}")
    with NativeTwin(scenario) as twin:
        initial = twin.snapshot()
        digest = hashlib.sha256()
        for _ in range(80):
            frame = twin.step()
            digest.update(twin.raw())
            assert abs(frame.ground_truth.energy_residual_j) < 1e-5
        saved = twin.snapshot()
        expected = [twin.step().model_dump_json() for _ in range(20)]
        twin.restore(saved)
        assert [twin.step().model_dump_json() for _ in range(20)] == expected
        twin.reset()
        assert twin.snapshot() == initial
        replay = hashlib.sha256()
        for _ in range(80):
            twin.step()
            replay.update(twin.raw())
        assert replay.hexdigest() == digest.hexdigest()


def test_invalid_controls_snapshot_and_closed_handle():
    with NativeTwin(scenario_from_file(DIRECTORY, "scenario-000")) as twin:
        twin.step()
        before = twin.snapshot()
        with pytest.raises(ValueError):
            twin.step(float("nan"))
        controls = SimulatorControls(pump=0.0, loads=[0.0] * 6, valves=[0.0] * 6)
        with pytest.raises(ValueError):
            twin.controls(0, controls)
        envelope = json.loads(before)
        envelope["payload"] += " "
        with pytest.raises(ValueError):
            twin.restore(json.dumps(envelope).encode())
        assert twin.snapshot() == before
        twin.controls(1, controls)
        frame = twin.step()
        assert frame.ground_truth.pump_fraction == pytest.approx(0.79)
    with pytest.raises(ValueError):
        twin.step()
    twin.close()  # Idempotent destruction.


def test_faults_have_distinct_measured_effects():
    with NativeTwin(scenario_from_file(DIRECTORY, "scenario-060")) as delayed:
        for _ in range(70):
            frame = delayed.step()
        assert frame.measurement.age_s == pytest.approx(2.0)
        assert frame.measurement.sampled_version == 66
    with NativeTwin(scenario_from_file(DIRECTORY, "scenario-070")) as dropped:
        frames = [dropped.step() for _ in range(70)]
        assert any(not f.measurement.packet_available for f in frames)
        assert frames[-1].measurement.dropped_packets > 0
    with NativeTwin(scenario_from_file(DIRECTORY, "scenario-020")) as frozen:
        for _ in range(61):
            start = frozen.step()
        for _ in range(400):
            end = frozen.step()
        assert abs(start.cells[0].temperature_c - end.cells[0].temperature_c) <= 0.2
        assert (
            end.ground_truth.cells[0].temperature_c > start.ground_truth.cells[0].temperature_c + 5
        )


def test_scenario_path_traversal_rejected():
    with pytest.raises(ValueError):
        scenario_from_file(DIRECTORY, "../../.env")


def test_seed_changes_noise_and_initial_state_with_bounded_instrument_error():
    scenario = scenario_from_file(DIRECTORY, "scenario-000")
    with (
        NativeTwin(scenario) as first,
        NativeTwin(scenario.model_copy(update={"seed": 43})) as second,
    ):
        assert first.snapshot() != second.snapshot()
        for _ in range(200):
            frame = first.step()
            for reading, truth in zip(frame.cells, frame.ground_truth.cells, strict=True):
                assert abs(reading.temperature_c - truth.temperature_c) <= reading.noise_bound_c
