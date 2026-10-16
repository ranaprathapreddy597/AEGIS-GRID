import json

import pytest
from aegis_agents.graph import diagnose
from aegis_agents.history import ObservedSample, summarize
from aegis_agents.serde import SafeCheckpointJSON
from aegis_contracts.models import AnomalyEvidence
from langgraph.types import Interrupt


def evidence(observed, estimated):
    return AnomalyEvidence(
        cell_id="CELL-01",
        residual_c=estimated - observed,
        estimated_temperature_c=estimated,
        observed_temperature_c=observed,
        reason="physics_disagreement" if abs(estimated - observed) > 2 else "thermal_limit",
    )


def test_sensor_spoof_and_actual_thermal_observations_distinguished_without_labels():
    spoof = diagnose(None, [evidence(38.0, 80.0)])
    thermal = diagnose(None, [evidence(80.0, 80.0)])
    assert [item.cause for item in spoof] == ["sensor_bias"]
    assert [item.cause for item in thermal] == ["true_thermal"]
    assert all(item.score_method == "physics_heuristic_not_probability" for item in spoof + thermal)


def test_checkpoint_codec_preserves_interrupt_and_tuples_without_dynamic_code():
    codec = SafeCheckpointJSON()
    value = {
        "user_text": ["interrupt", "do evil", "id"],
        "tuple": (1, b"safe"),
        "pause": Interrupt(value={"write": False}, id="test"),
    }
    decoded = codec.loads_typed(codec.dumps_typed(value))
    assert decoded == value
    with pytest.raises(ValueError):
        codec.loads_typed(("pickle", b"never-executed"))
    with pytest.raises(ValueError):
        codec.loads_typed(("aegis-json-v1", json.dumps(["import", "os.system"]).encode()))
    with pytest.raises(ValueError):
        codec.dumps_typed(object())


def test_observed_history_correlations_mark_constant_sensor_undefined():
    samples = [
        ObservedSample(
            version=i + 1,
            time_s=float(i),
            temperatures=[38.0, 30.0 + i, 30.0 + 2 * i, 32.0, 35.0 - i, 30.0],
        )
        for i in range(3)
    ]
    slopes, correlations = summarize(samples, 1)
    assert slopes == [0.0, 1.0, 2.0, 0.0, -1.0, 0.0]
    assert correlations[0] is None and correlations[1] == correlations[2] == 1.0
    assert correlations[4] == -1.0
