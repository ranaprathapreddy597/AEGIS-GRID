"""Actually execute 10,000 C++ futures. Run in a network-none bounded CPU container."""

import argparse
import gzip
import hashlib
import json
import random
import resource
import time
from pathlib import Path

from aegis_agents.optimizer import canonical, digest
from aegis_contracts.laboratory import FutureFailure, FuturesEnsemble, HistogramBin
from aegis_edge.runner import SupervisedTwin
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin, scenario_from_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    library = Path("/build/libaegis_twin.so")
    scenario = scenario_from_file(Path("data/scenarios"), "scenario-090", 42)
    supervisor = SupervisedTwin(scenario, library)
    try:
        for _ in range(600):
            _, status = supervisor.step()
            if status and status.latched:
                break
        snapshot = supervisor.incident_snapshot
        if snapshot is None:
            raise RuntimeError("Seeded incident required")
    finally:
        supervisor.close()
    rng = random.Random(110042)  # noqa: S311  # Explicit repeatable synthetic priors, not posterior probabilities.
    bins = [
        HistogramBin(lower_c=float(n), upper_c=float(n + 10), baseline=0, intervention=0)
        for n in range(20, 120, 10)
    ]
    rows = []
    failures = []
    totals = [0.0] * 5
    failed = [0, 0]
    started = time.perf_counter()
    with NativeTwin(scenario, library) as twin:
        for index in range(5000):
            state = json.loads(snapshot.payload_json)
            seed = 1100000 + index
            target = rng.randrange(6)
            severity = rng.uniform(0.3, 1.0)
            offset = rng.uniform(-2.0, 2.0)
            state["scenario"].update(
                seed=seed, target=target, severity=severity, fault_mask=156, start_s=0
            )
            for cell in state["cells"]:
                cell[0] += offset
            state["coolant"] += offset
            raw = canonical(state).decode()
            twin.restore(
                canonical({"payload": raw, "sha256": hashlib.sha256(raw.encode()).hexdigest()})
            )
            before = twin.rollout(None, 600, 0)
            after = twin.rollout(SafetyShield.emergency_controls(), 600, 0)
            row = dict(
                case=index,
                seed=seed,
                target=target,
                severity=severity,
                offset_c=offset,
                snapshot_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                baseline={
                    k: v
                    for k, v in before.model_dump().items()
                    if k
                    in {
                        "maximum_temperature_c",
                        "violation_mask",
                        "energy_kwh",
                        "production_units",
                        "downtime_s",
                    }
                },
                intervention={
                    k: v
                    for k, v in after.model_dump().items()
                    if k
                    in {
                        "maximum_temperature_c",
                        "violation_mask",
                        "energy_kwh",
                        "production_units",
                        "downtime_s",
                    }
                },
            )
            rows.append(row)
            for side, result in enumerate((before, after)):
                position = max(0, min(9, int((result.maximum_temperature_c - 20) // 10)))
                field = "baseline" if side == 0 else "intervention"
                bins[position] = bins[position].model_copy(
                    update={field: getattr(bins[position], field) + 1}
                )
                failed[side] += bool(result.violation_mask)
            totals[0] += before.energy_kwh
            totals[1] += after.energy_kwh
            totals[2] += before.production_units
            totals[3] += after.production_units
            totals[4] += after.downtime_s
            if before.violation_mask and len(failures) < 6:
                failures.append(
                    FutureFailure(
                        case=index,
                        seed=seed,
                        target=target,
                        severity=severity,
                        baseline_peak_c=before.maximum_temperature_c,
                        intervention_peak_c=after.maximum_temperature_c,
                        baseline_violations=before.violation_mask,
                        intervention_violations=after.violation_mask,
                    )
                )
            if (index + 1) % 1000 == 0:
                print(f"Actually completed {(index + 1) * 2} native rollouts", flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    raw_rows = canonical(rows)
    (args.output / "rows.json.gz").write_bytes(gzip.compress(raw_rows, mtime=0))
    report = FuturesEnsemble(
        artifact_sha256="0" * 64,
        rows_sha256=hashlib.sha256(raw_rows).hexdigest(),
        source_snapshot_sha256=snapshot.sha256,
        native_binary_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
        baseline_failed=failed[0],
        intervention_failed=failed[1],
        histogram=bins,
        counterexamples=failures,
        baseline_mean_energy_kwh=totals[0] / 5000,
        intervention_mean_energy_kwh=totals[1] / 5000,
        baseline_mean_production=totals[2] / 5000,
        intervention_mean_production=totals[3] / 5000,
        intervention_mean_downtime_s=totals[4] / 5000,
        assumptions=[
            "Precomputed scenario-090 seed 42 incident, not the currently selected "
            "incident or live posterior.",
            "5000 seeded synthetic priors: target uniform 0..5, severity uniform .3..1, "
            "temperature offset uniform -2..2C; combined mask 156.",
            "Each prior executes baseline and exact emergency stop for 600s at 20 "
            "native substeps/s; 10000 actual CPU futures.",
            "Histogram outer bins include overflow; finite synthetic coverage is not "
            "industrial confidence.",
            "Native rollout checks thermal/flow/pressure/feeder/ramp constraints. Costs "
            "are assumed dimensionless, not dollars.",
        ],
    )
    report = report.model_copy(
        update={"artifact_sha256": digest(report.model_dump(exclude={"artifact_sha256"}))}
    )
    (args.output / "ensemble.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    profile = dict(
        elapsed_s=time.perf_counter() - started,
        peak_process_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        total_rollouts=10000,
        native_substeps=120000000,
        artifact_sha256=report.artifact_sha256,
        mode="actual_CPU_no_GPU",
        excludes="Docker/WSL memory and other processes",
    )
    (args.output / "profile.json").write_text(
        json.dumps(profile, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(profile))


if __name__ == "__main__":
    main()
