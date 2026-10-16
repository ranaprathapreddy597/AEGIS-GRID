"""Frozen development benchmark; actual C++/CPU data, no hardware/provider simulation."""

import argparse
import hashlib
import json
import random
import resource
import statistics
import time
from pathlib import Path

import numpy as np
from aegis_agents.graph import diagnose
from aegis_contracts.models import SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin, scenario_from_file

LIBRARY = Path("/build/libaegis_twin.so")
ACCEPTABLE = {
    1: "sensor_bias",
    2: "sensor_bias",
    3: "restricted_flow",
    4: "weak_pump",
    5: "overload",
    6: "stale_measurement",
    7: "missing_packets",
    8: "overload",
    9: "sensor_bias",
}


def features(frame: SensorFrame) -> list[float]:
    """Strict observed-only projection; no ID, seed, truth, label, absolute time or version."""
    return (
        [c.temperature_c / 100 for c in frame.cells]
        + [c.flow_kg_s / 0.3 for c in frame.cells]
        + [c.load_fraction for c in frame.cells]
        + [c.heat_input_w / 10000 for c in frame.cells]
        + [
            frame.coolant_temperature_c / 100,
            frame.loop_pressure_kpa / 180,
            frame.measurement.age_s / 20,
        ]
    )


def metrics(rows: list[dict], name: str) -> dict:
    tp = sum(r["positive"] and r[name] is not None for r in rows)
    fp = sum(not r["positive"] and r[name] is not None for r in rows)
    fn = sum(r["positive"] and r[name] is None for r in rows)
    tn = len(rows) - tp - fp - fn
    delays = [r[name] - r["onset_s"] for r in rows if r["positive"] and r[name] is not None]
    return dict(
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        precision=tp / (tp + fp) if tp + fp else None,
        recall=tp / (tp + fn) if tp + fn else None,
        median_detection_delay_s=statistics.median(delays) if delays else None,
        p95_detection_delay_s=float(np.quantile(delays, 0.95)) if delays else None,
        early_alarms=sum(r[name] is not None and r[name] < r["onset_s"] for r in rows),
    )


def intervals(rows: list[dict], name: str) -> dict:
    rng = random.Random(120042)  # noqa: S311 - repeatable statistical resampling, not security.
    clusters = [[r for r in rows if r["family"] == family] for family in range(10)]
    values: dict[str, list[float]] = {key: [] for key in ("precision", "recall")}
    for _ in range(2000):
        sample = [r for _ in range(10) for r in clusters[rng.randrange(10)]]
        result = metrics(sample, name)
        for key in values:
            if result[key] is not None:
                values[key].append(result[key])
    return {
        key: [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))] if v else None
        for key, v in values.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    train_x, train_y, train_family = [], [], []
    training_seeds = []
    for family in range(10):
        for repeat in range(3):
            seed = 2000000 + family * 100 + repeat
            training_seeds.append(seed)
            scenario = scenario_from_file(
                Path("data/scenarios"), f"scenario-{family * 10:03}", seed
            )
            with NativeTwin(scenario, LIBRARY) as twin:
                for second in range(1, 601):
                    frame = twin.step(1.0)
                    if second % 10 or not frame.measurement.packet_available:
                        continue
                    sensor = SensorFrame.from_twin(frame)
                    train_x.append(features(sensor))
                    active = (
                        scenario.fault_mask != 0 and frame.simulation_time_s >= scenario.start_s
                    )
                    train_y.append(float(active))
                    train_family.append(family if active else 0)
    x, labels = np.asarray(train_x), np.asarray(train_y)
    mean, scale = x.mean(axis=0), np.maximum(x.std(axis=0), 1e-5)
    standardized = (x - mean) / scale
    design = np.column_stack((np.ones(len(x)), standardized))
    weights = np.zeros(design.shape[1])
    balance = np.where(labels == 1, 0.5 / labels.mean(), 0.5 / (1 - labels.mean()))
    for _ in range(600):
        probabilities = 1 / (1 + np.exp(-np.clip(design @ weights, -30, 30)))
        gradient = design.T @ ((probabilities - labels) * balance) / len(labels)
        gradient[1:] += 0.001 * weights[1:]
        weights -= 0.1 * gradient
    centroids = np.asarray(
        [standardized[np.asarray(train_family) == f].mean(axis=0) for f in range(10)]
    )
    rows, detector_ms, model_ms, full_ms = [], [], [], []
    evaluate_started = time.perf_counter()
    for index in range(100):
        scenario = scenario_from_file(Path("data/scenarios"), f"scenario-{index:03}")
        supervisor = SupervisedTwin(scenario, LIBRARY, observe_only=True)
        shielded = SupervisedTwin(scenario, LIBRARY)
        first = dict(naive_s=None, sentinel_s=None, learned_s=None)
        family = index // 10
        streak = 0
        diagnosis = None
        learned_diagnosis = None
        maximum_before = maximum_after = 0.0
        downtime = 0
        trajectory = hashlib.sha256()
        try:
            for _ in range(600):
                start = time.perf_counter_ns()
                frame, status = supervisor.step(1.0)
                full_ms.append((time.perf_counter_ns() - start) / 1e6)
                controlled, _ = shielded.step(1.0)
                trajectory.update(frame.model_dump_json().encode())
                maximum_before = max(
                    maximum_before, *(c.temperature_c for c in frame.ground_truth.cells)
                )
                maximum_after = max(
                    maximum_after, *(c.temperature_c for c in controlled.ground_truth.cells)
                )
                downtime += all(c.load_fraction < 0.01 for c in controlled.cells)
                if not frame.measurement.packet_available or status is None:
                    continue
                sensor = SensorFrame.from_twin(frame)
                detector_ms.append(status.latency_ms)
                if max(c.temperature_c for c in sensor.cells) >= 70 and first["naive_s"] is None:
                    first["naive_s"] = frame.simulation_time_s
                if status.latched and first["sentinel_s"] is None:
                    first["sentinel_s"] = frame.simulation_time_s
                    hypotheses = diagnose(sensor, status.evidence)
                    diagnosis = hypotheses[0].cause if hypotheses else None
                start = time.perf_counter_ns()
                vector = (np.asarray(features(sensor)) - mean) / scale
                probability = float(
                    1 / (1 + np.exp(-np.clip(weights[0] + vector @ weights[1:], -30, 30)))
                )
                model_ms.append((time.perf_counter_ns() - start) / 1e6)
                streak = streak + 1 if probability >= 0.5 else 0
                if streak >= 3 and first["learned_s"] is None:
                    first["learned_s"] = frame.simulation_time_s
                    learned_diagnosis = int(np.argmin(((centroids - vector) ** 2).sum(axis=1)))
            row = dict(
                scenario_id=scenario.scenario_id,
                family=family,
                seed=scenario.seed,
                positive=bool(scenario.fault_mask),
                onset_s=scenario.start_s,
                **first,
                numerical_diagnosis=diagnosis,
                expected_coarse_cause=ACCEPTABLE.get(family),
                numerical_diagnosis_correct=bool(family and diagnosis == ACCEPTABLE[family]),
                learned_family_diagnosis=learned_diagnosis,
                learned_diagnosis_correct=learned_diagnosis == family,
                baseline_peak_c=maximum_before,
                shielded_peak_c=maximum_after,
                baseline_hazard=maximum_before >= 70,
                shielded_hazard=maximum_after >= 70,
                shield_downtime_s=downtime,
                baseline_energy_kwh=frame.ground_truth.energy_j / 3600000,
                shield_energy_kwh=controlled.ground_truth.energy_j / 3600000,
                baseline_production=frame.ground_truth.production_units,
                shield_production=controlled.ground_truth.production_units,
                trajectory_sha256=trajectory.hexdigest(),
            )
            rows.append(row)
        finally:
            supervisor.close()
            shielded.close()
        if (index + 1) % 20 == 0:
            print(f"Actually evaluated {index + 1}/100 scenario pairs", flush=True)
    evaluation_s = time.perf_counter() - evaluate_started
    rng = random.Random(120099)  # noqa: S311 - nonsecurity fuzz corpus.
    blocked = 0
    for _ in range(512):
        controls = SafetyShield.emergency_controls().model_copy(
            update={"pump": rng.random(), "loads": [rng.random() for _ in range(6)]}
        )
        blocked += not SafetyShield.authorize(controls, 1, 1)
    hazardous = [r for r in rows if r["baseline_hazard"]]
    output = dict(
        scope="100 registered synthetic DEVELOPMENT fixtures; not independent held-out plants",
        protocol="docs/FINAL_VALIDATION_PLAN.md frozen before measurement",
        sentinel_revision=status.policy_revision,
        dt_s=1,
        horizon_s=600,
        native_binary_sha256=hashlib.sha256(LIBRARY.read_bytes()).hexdigest(),
        training=dict(
            seeds=training_seeds,
            trajectories=30,
            frames=len(labels),
            threshold=0.5,
            consecutive_frames=3,
            features="6 temperatures, 6 flows, 6 loads, 6 heat inputs, coolant, "
            "pressure, sensor age; no truth/labels/ID/seed/time/version",
            mean=mean.tolist(),
            scale=scale.tolist(),
            weights=weights.tolist(),
            centroids=centroids.tolist(),
        ),
        detectors={
            name: {**metrics(rows, name), "family_cluster_bootstrap_95": intervals(rows, name)}
            for name in first
        },
        diagnosis=dict(
            numerical_top1_correct=sum(r["numerical_diagnosis_correct"] for r in rows),
            fault_cases=90,
            learned_family_top1_correct_on_faults=sum(
                r["learned_diagnosis_correct"] for r in rows if r["positive"]
            ),
        ),
        recovery=dict(
            baseline_hazard_cases=len(hazardous),
            recovered_below_70=sum(not r["shielded_hazard"] for r in hazardous),
            remaining_hazards=sum(r["shielded_hazard"] for r in rows),
            mean_stop_downtime_s=statistics.mean(r["shield_downtime_s"] for r in rows),
            mean_baseline_production=statistics.mean(r["baseline_production"] for r in rows),
            mean_shield_production=statistics.mean(r["shield_production"] for r in rows),
            mean_baseline_energy_kwh=statistics.mean(r["baseline_energy_kwh"] for r in rows),
            mean_shield_energy_kwh=statistics.mean(r["shield_energy_kwh"] for r in rows),
        ),
        unsafe_controls=dict(
            attempted=512,
            refused=blocked,
            scope="finite random exact-stop shield fuzz; no network or physical I/O",
        ),
        performance=dict(
            total_wall_s=time.perf_counter() - started,
            evaluation_wall_s=evaluation_s,
            paired_native_steps=120000,
            paired_native_steps_per_wall_s=120000 / evaluation_s,
            sentinel_p50_ms=statistics.median(detector_ms),
            sentinel_p95_ms=float(np.quantile(detector_ms, 0.95)),
            learned_p95_ms=float(np.quantile(model_ms, 0.95)),
            full_baseline_step_p95_ms=float(np.quantile(full_ms, 0.95)),
            peak_process_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        ),
        limitations=[
            "Ten correlated synthetic families, one healthy family; bootstrap is descriptive only.",
            "Fault presence is not equivalent to danger; unsupported diagnoses and "
            "early alarms are retained.",
            "Detector comparison uses identical unmitigated frames; shield "
            "outcomes are separate paired native trajectories.",
            "CPU logistic/centroid baseline is real learned inference; offline "
            "language-model backend still abstains.",
            "No GPU/NPU/provider calls, model tokens, dollar savings or industrial "
            "confidence fabricated.",
        ],
        rows=rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: output[key] for key in ("detectors", "diagnosis", "recovery", "performance")}
        )
    )


if __name__ == "__main__":
    main()
