"""Finite minimax search. Native physics, rather than model opinion, decides feasibility."""

import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any

from aegis_contracts.models import IncidentRecord, SimulatorControls
from aegis_contracts.optimization import (
    Counterexample,
    PlanEvaluation,
    RecoveryAssessment,
    SimRollout,
    UncertaintyCase,
)
from aegis_edge.twin import NativeTwin, scenario_from_file

POLICY = {
    "temperature_lt_c": 70.0,
    "productive_flow_min_kg_s": 0.02,
    "pressure_max_kpa": 180.0,
    "feeder_max_w": 14500.0,
    "flow_grace_s": 10.0,
    "pump_ramp_s": 0.12,
    "load_ramp_s": 0.10,
    "valve_ramp_s": 0.20,
}
WEIGHTS = {
    "lost_production_units": 5.0,
    "downtime_s": 0.05,
    "energy_kwh": 0.25,
    "actuator_travel": 0.1,
    "thermal_risk": 10.0,
}
ASSUMPTIONS = [
    "Synthetic uncalibrated model; fixed 600-second open-loop control horizon, dt=1s/20 substeps.",
    "Full-state counterfactual referee, not observed-only prediction or inferred fault truth.",
    "Nominal plus 36 priors: six targets, severity .5/.8/1, temperature offset -2/+2C.",
    "Priors combine blockage, weak pump, demand burst and power spike, onset immediately.",
    "Finite coverage only; no statistical/industrial safety guarantee outside the enumerated set.",
    "Productive flow floor has ten seconds settling; thermal bound always applies.",
    "Costs are assumed dimensionless weights, not dollars, prices or measured business savings.",
    "Main edge emergency latch remains untouched. Contradictory manual blocks all execution.",
]


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def verify_artifact(report: RecoveryAssessment) -> None:
    value = report.model_dump()
    expected = value.pop("artifact_sha256")
    if digest(value) != expected:
        raise ValueError("Rollout artifact integrity mismatch")


def grid() -> list[tuple[str, SimulatorControls]]:
    candidates = [
        (
            f"blue-load-{int(load * 100)}-pump-{int(pump * 100)}",
            SimulatorControls(pump=pump, loads=[load] * 6, valves=[1.0] * 6),
        )
        for load, pump in product((0.0, 0.25, 0.5, 0.75, 1.0), (0.7, 1.0))
    ]
    candidates.append(
        ("planted-unsafe", SimulatorControls(pump=0.0, loads=[1.0] * 6, valves=[0.0] * 6))
    )
    return candidates


def objective(result: SimRollout) -> float:
    values = {
        "lost_production_units": max(0.0, result.horizon_s / 10 - result.production_units),
        "downtime_s": result.downtime_s,
        "energy_kwh": result.energy_kwh,
        "actuator_travel": result.actuator_travel,
        "thermal_risk": (max(0.0, result.maximum_temperature_c - 40) / 30) ** 2,
    }
    return sum(WEIGHTS[name] * value for name, value in values.items())


def uncertainty(payload: str) -> list[tuple[UncertaintyCase, bytes]]:
    source = json.loads(payload)
    variants: list[tuple[str, dict[str, Any], float]] = [("snapshot", source, 0.0)]
    for index, (target, severity, offset) in enumerate(
        product(range(6), (0.5, 0.8, 1.0), (-2.0, 2.0)), start=1
    ):
        value = json.loads(payload)
        value["scenario"].update(
            target=target,
            severity=severity,
            fault_mask=156,
            start_s=0,
            seed=(source["scenario"]["seed"] + index) % 2**32,
        )
        for cell in value["cells"]:
            cell[0] += offset
        value["coolant"] += offset
        variants.append((f"red-{index:02d}", value, offset))
    cases = []
    for name, state, offset in variants:
        raw = canonical(state).decode()
        sha = hashlib.sha256(raw.encode()).hexdigest()
        scenario = state["scenario"]
        cases.append(
            (
                UncertaintyCase(
                    case_id=name,
                    seed=scenario["seed"],
                    snapshot_sha256=sha,
                    fault_mask=scenario["fault_mask"],
                    target=scenario["target"],
                    severity=scenario["severity"],
                    temperature_offset_c=offset,
                ),
                canonical({"payload": raw, "sha256": sha}),
            )
        )
    return cases


def optimize(record: IncidentRecord, library: Path) -> RecoveryAssessment:
    snapshot = record.event.snapshot
    if snapshot is None:
        raise ValueError("No native initial state; refusing invented futures")
    source = json.loads(snapshot.payload_json)
    common: dict[str, Any] = dict(
        incident_id=record.incident_id,
        source_snapshot_sha256=snapshot.sha256,
        native_binary_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
        policy=POLICY,
        objective_weights=WEIGHTS,
        assumptions=ASSUMPTIONS,
        candidates=[],
        cases=[],
        selected_candidate_id=None,
        total_rollouts=0,
        native_substeps=0,
        baseline=None,
        intervention=None,
    )
    in_domain = (
        all(20 <= cell[0] <= 60 for cell in source["cells"])
        and 20 <= source["coolant"] <= 45
        and source["time"] <= 999000
    )
    if not in_domain:
        common.update(
            status="abstained", reason="Initial thermal state outside preregistered envelope"
        )
    else:
        cases = uncertainty(snapshot.payload_json)
        common["cases"] = [case.model_dump() for case, _ in cases]
        evaluations = []
        with NativeTwin(
            scenario_from_file(Path("data/scenarios"), "scenario-000"), library
        ) as twin:
            # Validate/restore every complete prior, not just a sensor-temperature stub.
            for name, controls in grid():
                results = []
                counterexamples: list[Counterexample] = []
                for case, envelope in cases:
                    twin.restore(envelope)
                    result = twin.rollout(controls, 600, 0)
                    results.append(result)
                    if result.violation_mask and len(counterexamples) < 3:
                        counterexamples.append(
                            Counterexample(
                                case_id=case.case_id,
                                violation_mask=result.violation_mask,
                                maximum_temperature_c=result.maximum_temperature_c,
                            )
                        )
                failed = sum(bool(item.violation_mask) for item in results)
                evaluations.append(
                    PlanEvaluation(
                        candidate_id=name,
                        controls=controls,
                        feasible=failed == 0,
                        checked_cases=len(results),
                        failed_cases=failed,
                        worst_temperature_c=max(item.maximum_temperature_c for item in results),
                        worst_objective=max(objective(item) for item in results),
                        mean_energy_kwh=sum(item.energy_kwh for item in results) / len(results),
                        minimum_production_units=min(item.production_units for item in results),
                        maximum_downtime_s=max(item.downtime_s for item in results),
                        maximum_actuator_travel=max(item.actuator_travel for item in results),
                        counterexamples=counterexamples,
                    )
                )
            # Feasibility precedes cost. An unsafe low-cost plan can never win.
            feasible = sorted(
                (item for item in evaluations if item.feasible),
                key=lambda item: (item.worst_objective, item.candidate_id),
            )
            selected = feasible[0] if feasible else None
            twin.restore(canonical({"payload": snapshot.payload_json, "sha256": snapshot.sha256}))
            common["baseline"] = twin.rollout(None).model_dump()
            if selected:
                common["selected_candidate_id"] = selected.candidate_id
                common["intervention"] = twin.rollout(selected.controls).model_dump()
            total = len(cases) * len(evaluations) + 1 + bool(selected)
            common.update(
                candidates=[item.model_dump() for item in evaluations],
                total_rollouts=total,
                native_substeps=total * 600 * 20,
                status="checked_non_executable" if selected else "abstained",
                reason="Finite robust search passed; authorization and manual gate remain closed"
                if selected
                else "No candidate satisfies every enumerated hard constraint",
            )
    # Hash the fully validated normalized representation, not unspecified JSON field order.
    report = RecoveryAssessment(artifact_sha256="0" * 64, **common)
    value = report.model_dump()
    value.pop("artifact_sha256")
    report = report.model_copy(update={"artifact_sha256": digest(value)})
    verify_artifact(report)
    return report
