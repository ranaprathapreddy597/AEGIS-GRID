"""Frozen seed-held-out native diagnosis evaluation; no cloud calls, tuning or training.

Run in the existing QA image with /workspace read-only mounted and PYTHONPATH set
to source services. The caller chooses a new output path; historical proof is not edited.
"""

import argparse
import hashlib
import json
import time
from pathlib import Path

from aegis_agents.quality import grounded_diagnose
from aegis_contracts.models import AnomalyEvidence, SensorFrame
from aegis_edge.sentinel import PhysicsObserver
from aegis_edge.twin import NativeTwin, scenario_from_file

# Frozen before execution. Existing scenario equations/families are development knowledge;
# only seeds, target cell and observation cutoffs are held out. No fitted parameters.
EVALUATION_SEEDS = tuple(1734001 + 7919 * i for i in range(10))
EXPECTED = {
    0: [],
    1: ["sensor_bias"],
    2: ["sensor_bias"],
    3: ["restricted_flow"],
    4: ["weak_pump"],
    5: ["overload"],
    6: [],
    7: [],
    8: ["overload"],
    9: ["sensor_bias", "restricted_flow", "weak_pump", "overload"],
}
PROTOCOL = {
    "version": "sprint-ai-seed-holdout-v2",
    "seeds": EVALUATION_SEEDS,
    "scenario_families": list(range(10)),
    "cutoff": "90 + (seed % 181) seconds, one prediction per case",
    "targets": "seed % 6; no hidden truth supplied to diagnosis",
    "expected_causes": EXPECTED,
    "training": "none; v2 removes residual precondition after v1 development seed evaluation",
    "split": "new seeds/target/cutoff; existing equation families are NOT held out",
}


def legacy(sensor: SensorFrame, evidence: list[AnomalyEvidence]) -> list[str]:
    scores = {}
    if any(abs(e.residual_c) > 2 for e in evidence):
        scores["sensor_bias"] = 0.9
    if any(e.observed_temperature_c >= 70 and abs(e.residual_c) <= 2 for e in evidence):
        scores["true_thermal"] = 0.9
    if any(c.flow_kg_s < 0.02 for c in sensor.cells):
        scores["restricted_flow"] = 0.6
    if sensor.loop_pressure_kpa < 20:
        scores["weak_pump"] = 0.5
    if any(c.load_fraction > 0.9 for c in sensor.cells):
        scores["overload"] = 0.5
    return sorted(scores, key=lambda cause: (-scores[cause], cause))


def metrics(rows: list[dict], field: str) -> dict:
    tp = fp = fn = correct = issued = correct_top = faults = abstained = 0
    for row in rows:
        predictions, expected = set(row[field]), set(row["expected_causes"])
        tp += len(predictions & expected)
        fp += len(predictions - expected)
        fn += len(expected - predictions)
        issued += bool(predictions)
        faults += bool(expected)
        abstained += not predictions
        top = row[field][0] if row[field] else None
        correct_top += top in expected
        correct += top in expected if expected else top is None
    return {
        "cases": len(rows),
        "true_positive_causes": tp,
        "false_positive_causes": fp,
        "false_negative_causes": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "accuracy": correct / len(rows),
        "top1_fault_recall": correct_top / faults if faults else None,
        "selective_top1_accuracy": correct_top / issued if issued else None,
        "abstention_coverage": abstained / len(rows),
        "prediction_coverage": issued / len(rows),
        "abstained_cases": abstained,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=Path("/build/libaegis_twin.so"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Use a new output; never overwrite measured evidence")
    started = time.perf_counter()
    rows = []
    for family in range(10):
        for seed in EVALUATION_SEEDS:
            scenario = scenario_from_file(
                Path("data/scenarios"), f"scenario-{family * 10:03}", seed
            )
            scenario = scenario.model_copy(update={"target": seed % 6})
            observer = PhysicsObserver()
            evidence: list[AnomalyEvidence] = []
            sensor = None
            trajectory = hashlib.sha256()
            cutoff = 90 + seed % 181
            with NativeTwin(scenario, args.library) as twin:
                for _ in range(cutoff):
                    frame = twin.step(1.0)
                    sensor = SensorFrame.from_twin(frame)
                    trajectory.update(sensor.model_dump_json().encode())
                    # Observer gets current channel quality too; missing/stale evidence cannot
                    # subsequently become asserted bias in grounded_diagnose.
                    evidence = observer.update(sensor)
            assert sensor is not None  # noqa: S101 - frozen cutoff always positive
            hypotheses = grounded_diagnose(sensor, evidence)
            rows.append(
                {
                    "family": family,
                    "seed": seed,
                    "target": scenario.target,
                    "cutoff_s": cutoff,
                    "expected_causes": EXPECTED[family],
                    "legacy_causes": legacy(sensor, evidence),
                    "grounded_causes": [h.cause for h in hypotheses],
                    "grounded_explanations": [h.explanation for h in hypotheses],
                    "observed_trajectory_sha256": trajectory.hexdigest(),
                    "measurement_age_s": sensor.measurement.age_s,
                    "packet_available": sensor.measurement.packet_available,
                }
            )
    report = {
        "status": "measured_synthetic_seed_holdout",
        "protocol": PROTOCOL,
        "protocol_sha256": hashlib.sha256(
            json.dumps(PROTOCOL, sort_keys=True).encode()
        ).hexdigest(),
        "native_binary_sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
        "quality_source_sha256": hashlib.sha256(
            Path("services/agents/aegis_agents/quality.py").read_bytes()
        ).hexdigest(),
        "elapsed_s": time.perf_counter() - started,
        "legacy": metrics(rows, "legacy_causes"),
        "grounded": metrics(rows, "grounded_causes"),
        "per_family": {
            str(f): metrics([r for r in rows if r["family"] == f], "grounded_causes")
            for f in range(10)
        },
        "definitions": {
            "precision_recall": "micro cause-set precision/recall; thermal symptom unsupported",
            "accuracy": "top cause in injected set; correct abstention for no modeled cause",
            "abstention_coverage": "fraction with no hypothesis, NOT an accuracy",
            "transport": "delay/drop families lack a representable cause; expected to abstain",
        },
        "limitations": [
            "Same synthetic equations and fault families used during original development",
            "Seed holdout does not establish unseen-fault or real-world generalization",
            "Weak pump and load bursts are ambiguous without command/history inputs",
            "High precision may be traded for lower recall/coverage; all false negatives retained",
            "No AMD/Pinecone/MI300X call or hosted diagnostic performance evaluated",
        ],
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["status", "legacy", "grounded", "elapsed_s"]}))


if __name__ == "__main__":
    main()
