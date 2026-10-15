from pathlib import Path

import pytest
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file

LIBRARY = Path("/build/libaegis_twin.so")


@pytest.mark.parametrize("index", [0, 1, 2, 3, 4])
def test_real_twin_healthy_has_no_alarm(index):
    scenario = scenario_from_file(Path("data/scenarios"), f"scenario-{index:03}")
    supervisor = SupervisedTwin(scenario, LIBRARY)
    try:
        for _ in range(1200):
            frame, status = supervisor.step(1.0)
            assert status is not None and not status.latched
            assert status.memory_entries <= 256
        assert frame.ground_truth.feeder_power_w > 9000
    finally:
        supervisor.close()


def test_real_spoof_fault_detected_and_local_stop_latches_without_any_cloud():
    scenario = scenario_from_file(Path("data/scenarios"), "scenario-090")
    supervisor = SupervisedTwin(scenario, LIBRARY)
    first_detection = None
    maximum_truth = 0
    try:
        for _ in range(1200):
            frame, status = supervisor.step(1.0)
            maximum_truth = max(
                maximum_truth, max(c.temperature_c for c in frame.ground_truth.cells)
            )
            assert status is not None
            if status.latched and first_detection is None:
                first_detection = frame
                assert status.applied_policy == "local_emergency_stop"
                assert any(e.reason == "physics_disagreement" for e in status.evidence)
        assert first_detection is not None
        assert first_detection.simulation_time_s < 488
        assert first_detection.cells[0].temperature_c < 40
        assert maximum_truth < 70
        assert all(c.load_fraction < 1e-6 for c in frame.cells)
        assert status.latched  # No automatic restart after apparent sensor recovery.
    finally:
        supervisor.close()


def test_explicit_observe_only_mode_preserves_phase_two_unmitigated_challenge():
    scenario = scenario_from_file(Path("data/scenarios"), "scenario-090")
    supervisor = SupervisedTwin(scenario, LIBRARY, observe_only=True)
    try:
        for _ in range(600):
            frame, status = supervisor.step(1.0)
        assert status is not None and status.latched
        assert status.applied_policy == "observe_only"
        assert frame.ground_truth.cells[0].temperature_c > 80
        assert max(c.temperature_c for c in frame.cells) < 80
    finally:
        supervisor.close()
