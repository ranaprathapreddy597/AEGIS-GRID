import copy

import numpy as np
import pytest
from aegis_contracts.models import PlantTelemetry, SensorFrame, SimulatorControls
from aegis_edge.sentinel import LocalMemory, SafetyShield, Sentinel
from pydantic import ValidationError


def sensors(telemetry):
    return SensorFrame.from_twin(PlantTelemetry.model_validate(telemetry))


def test_detector_input_excludes_truth_labels_and_scenario(telemetry):
    frame = sensors(telemetry)
    assert (
        not {"ground_truth", "injected_fault_mask", "seed", "scenario_id"}
        & SensorFrame.model_fields.keys()
    )
    modified = copy.deepcopy(telemetry)
    modified["ground_truth"]["cells"][0]["temperature_c"] = 999.0
    modified["injected_fault_mask"] = 255
    assert sensors(modified) == frame
    with pytest.raises(ValidationError):
        SensorFrame.model_validate({**frame.model_dump(), "ground_truth": {}})


def test_shield_only_allows_the_exact_conservative_local_stop():
    allowed = SafetyShield.emergency_controls()
    assert SafetyShield.authorize(allowed, 10, 10)
    assert not SafetyShield.authorize(allowed, 9, 10)
    assert not SafetyShield.authorize(allowed, True, 1)
    for controls in [
        SimulatorControls(pump=0.0, loads=[0.0] * 6, valves=[1.0] * 6),
        SimulatorControls(pump=1.0, loads=[0.1] * 6, valves=[1.0] * 6),
        SimulatorControls(pump=1.0, loads=[0.0] * 6, valves=[0.5] * 6),
    ]:
        assert not SafetyShield.authorize(controls, 10, 10)


def test_faiss_memory_is_bounded_and_returns_real_nearest_neighbor(telemetry):
    memory = LocalMemory(32)
    frame = sensors(telemetry)
    for i in range(100):
        value = np.full((1, 18), float(i), dtype=np.float32)
        memory.add(frame.model_copy(update={"state_version": i + 1}), value, False)
    assert len(memory.rows) == memory.index.ntotal == 32
    nearest = memory.lookup(np.full((1, 18), 99.0, dtype=np.float32))
    assert nearest[0].state_version == 100
    assert nearest[0].distance_squared == 0


def test_detector_rejects_duplicate_out_of_order_and_big_gaps(telemetry):
    frame = sensors(telemetry)
    for next_frame in [
        frame,
        frame.model_copy(update={"state_version": 2, "simulation_time_s": 100.0}),
    ]:
        sentinel = Sentinel()
        sentinel.update(frame)
        with pytest.raises(ValueError):
            sentinel.update(next_frame)
