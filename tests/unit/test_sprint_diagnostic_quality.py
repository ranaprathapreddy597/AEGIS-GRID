"""Independent confounders and hosted grounding; no provider or hidden twin state."""

import pytest
from aegis_agents.quality import ground_hosted_opinion, grounded_diagnose
from aegis_contracts.inference import ModelOpinion
from aegis_contracts.models import AnomalyEvidence, SensorFrame


def observed(**changes):
    data = {
        "state_version": 101,
        "simulation_time_s": 100.0,
        "coolant_temperature_c": 25.0,
        "loop_pressure_kpa": 10.0,
        "cells": [
            {
                "cell_id": f"CELL-0{i}",
                "temperature_c": 38.0,
                "load_fraction": 1.0,
                "heat_input_w": 1870.0,
                "noise_bound_c": 0.1,
                "flow_kg_s": 0.01,
            }
            for i in range(1, 7)
        ],
        "measurement": {
            "sampled_version": 101,
            "sampled_time_s": 100.0,
            "age_s": 0.0,
            "packet_available": True,
            "dropped_packets": 0,
        },
    }
    data.update(changes)
    return SensorFrame.model_validate(data)


def residual(reason="physics_disagreement", observed_c=38.0, estimate=60.0):
    return AnomalyEvidence(
        cell_id="CELL-01",
        residual_c=estimate - observed_c,
        estimated_temperature_c=estimate,
        observed_temperature_c=observed_c,
        reason=reason,
    )


def test_low_common_flow_pressure_and_high_load_do_not_establish_three_causes():
    assert [h.cause for h in grounded_diagnose(observed(), [residual()])] == ["sensor_bias"]
    assert grounded_diagnose(observed(), []) == []


@pytest.mark.parametrize("reason", ["stale_measurement", "missing_packets"])
def test_transport_residuals_are_not_sensor_bias(reason):
    assert grounded_diagnose(observed(), [residual(reason)]) == []


@pytest.mark.parametrize("available,age", [(False, 0.0), (True, 3.0)])
def test_stale_or_missing_frame_abstains_even_with_other_evidence(available, age):
    frame = observed()
    quality = {**frame.measurement.model_dump(), "packet_available": available, "age_s": age}
    assert grounded_diagnose(observed(measurement=quality), [residual()]) == []


def test_branch_restriction_ranked_above_thermal_symptom():
    cells = [c.model_dump() for c in observed().cells]
    for c in cells:
        c["flow_kg_s"] = 0.3
    cells[0]["flow_kg_s"] = 0.005
    hypotheses = grounded_diagnose(observed(cells=cells), [residual("thermal_limit", 66.0, 66.0)])
    assert [h.cause for h in hypotheses] == ["restricted_flow", "true_thermal"]


def test_heat_conditioned_overload_and_observed_only_input():
    cells = [c.model_dump() for c in observed().cells]
    cells[0]["heat_input_w"] = 2500.0
    hypotheses = grounded_diagnose(observed(cells=cells), [residual("thermal_limit", 66.0, 66.0)])
    assert hypotheses[0].cause == "overload"
    assert "ground_truth" not in SensorFrame.model_fields


def test_unsupported_hosted_alternatives_filtered_and_duplicates_removed():
    opinion = ModelOpinion(
        assessment="investigate",
        hypotheses=["weak_pump", "sensor_bias", "sensor_bias", "overload"],
        evidence_ids=["residuals", "residuals"],
    )
    accepted, rejected = ground_hosted_opinion(opinion, grounded_diagnose(None, [residual()]))
    assert accepted.hypotheses == ["sensor_bias"] and rejected == 3
    assert accepted.evidence_ids == ["residuals"]


@pytest.mark.parametrize("ids", [[], ["retrieved_sources"], ["correlations"]])
def test_context_only_cannot_ground_a_hosted_cause(ids):
    opinion = ModelOpinion(assessment="investigate", hypotheses=["sensor_bias"], evidence_ids=ids)
    accepted, _ = ground_hosted_opinion(opinion, grounded_diagnose(None, [residual()]))
    assert accepted.assessment == "insufficient_evidence"
    assert accepted.hypotheses == accepted.evidence_ids == []


def test_explicit_model_abstention_preserved_and_unsupported_only_abstains():
    for opinion in [
        ModelOpinion(assessment="insufficient_evidence", hypotheses=[], evidence_ids=[]),
        ModelOpinion(assessment="investigate", hypotheses=["weak_pump"], evidence_ids=["observed"]),
    ]:
        accepted, _ = ground_hosted_opinion(opinion, grounded_diagnose(None, [residual()]))
        assert accepted.assessment == "insufficient_evidence" and not accepted.hypotheses
