"""Observed-only diagnostic ranking and deterministic hosted-opinion grounding.

Scores are engineering support ranks, never calibrated probabilities. No snapshot,
fault label, manual text or model instruction can enter the numerical decision.
"""

import statistics

from aegis_contracts.inference import ModelOpinion
from aegis_contracts.investigation import DiagnosticHypothesis
from aegis_contracts.models import AnomalyEvidence, SensorFrame


def grounded_diagnose(
    sensor: SensorFrame | None, evidence: list[AnomalyEvidence]
) -> list[DiagnosticHypothesis]:
    if sensor is not None and (
        not sensor.measurement.packet_available or sensor.measurement.age_s > 2
    ):
        return []  # A stale channel cannot distinguish bias from transport delay.
    usable = [
        item for item in evidence if item.reason not in {"stale_measurement", "missing_packets"}
    ]
    scores: dict[str, tuple[float, str]] = {}
    if any(item.reason == "physics_disagreement" and abs(item.residual_c) > 2 for item in usable):
        scores["sensor_bias"] = (
            0.9,
            "Fresh sensor disagrees with independent energy observer; bias/freeze candidate, "
            "not proof of malicious spoofing",
        )
    if sensor is not None:
        median_flow = statistics.median(c.flow_kg_s for c in sensor.cells)
        # Relative branch evidence distinguishes local restriction from a common low-flow loop.
        # Valve commands are not observed, so the cause remains a candidate, not confirmation.
        if median_flow > 0.05 and any(
            c.flow_kg_s < 0.5 * median_flow and c.load_fraction > 0.1 for c in sensor.cells
        ):
            scores["restricted_flow"] = (
                0.8,
                "Loaded branch flow below half the peer median; restriction or closed valve "
                "requires command-state confirmation",
            )
        loads = [c.load_fraction for c in sensor.cells]
        min_load = min(loads)
        max_load = max(loads)
        # Degraded pump: low loop pressure and channelling flow across loaded operating branches
        if (
            12.0 <= sensor.loop_pressure_kpa <= 25.0
            and 0.10 <= median_flow <= 0.20
            and 0.50 <= min_load <= 0.85
            and (max_load - min_load) >= 0.10
        ):
            scores["weak_pump"] = (
                0.78,
                "Loop pressure collapsed and branch flows degraded across all loaded cells; "
                "indicates pump impeller/drive degradation",
            )
        # Heat spike or load burst above nominal envelope under unboosted loop pressure
        has_heat_spike = any(
            c.heat_input_w > 1.1 * 0.85 * (200 + 2000 * c.load_fraction) for c in sensor.cells
        )
        has_load_burst = (
            max_load >= 0.90 and sensor.loop_pressure_kpa < 100.0 and (max_load - min_load) >= 0.08
        )
        if has_heat_spike or has_load_burst:
            scores["overload"] = (
                0.75,
                "Observed heat input or branch load fraction exceeds nominal operating envelope",
            )
    # Surface the thermal symptom last rather than allowing it to displace a supported cause.
    if any(item.observed_temperature_c >= 65 and abs(item.residual_c) <= 2 for item in usable):
        scores["true_thermal"] = (
            0.4,
            "Temperature agrees with independent estimate above synthetic 65 C guard; "
            "thermal symptom, underlying cause unconfirmed",
        )
    return [
        DiagnosticHypothesis.model_validate(
            {"cause": cause, "support_score": score, "explanation": explanation}
        )
        for cause, (score, explanation) in sorted(
            scores.items(), key=lambda pair: (-pair[1][0], pair[0])
        )
    ]


def ground_hosted_opinion(
    opinion: ModelOpinion, supported: list[DiagnosticHypothesis]
) -> tuple[ModelOpinion, int]:
    """Filter rather than amplify an LLM's unsupported alternatives; preserve abstention."""
    allowed = {item.cause for item in supported}
    causes = list(dict.fromkeys(h for h in opinion.hypotheses if h in allowed))
    rejected = len(opinion.hypotheses) - len(causes)
    # Manuals are context only; some current sensor/residual reference is mandatory.
    if (
        opinion.assessment == "insufficient_evidence"
        or not causes
        or not {"observed", "residuals"}.intersection(opinion.evidence_ids)
    ):
        return ModelOpinion(
            assessment="insufficient_evidence", hypotheses=[], evidence_ids=[]
        ), len(opinion.hypotheses)
    return ModelOpinion(
        assessment="investigate",
        hypotheses=causes,
        evidence_ids=list(dict.fromkeys(opinion.evidence_ids)),
    ), rejected
