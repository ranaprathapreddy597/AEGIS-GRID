"""Measured CPU rollout profile. No detection/diagnosis or physical safety claims."""

import gzip
import hashlib
import json
import platform
import resource
import statistics
import time
from pathlib import Path

from aegis_edge.twin import NativeTwin, fingerprint, scenario_from_file

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output = ROOT / "docs/results"
    output.mkdir(exist_ok=True, parents=True)
    results = []
    latencies = []
    began = time.perf_counter()
    # Deterministic gzip header; every tenth second for all 100 scenarios.
    with (output / "phase2-trajectories.ndjson.gz").open("wb") as file:
        with gzip.GzipFile(filename="", fileobj=file, mode="wb", mtime=0) as traces:
            for index in range(100):
                scenario = scenario_from_file(ROOT / "data/scenarios", f"scenario-{index:03}")
                digest = hashlib.sha256()
                max_truth = max_observed = max_residual = 0.0
                first_miss = None
                with NativeTwin(scenario) as twin:
                    initial = json.loads(twin.snapshot())
                    for step in range(1200):
                        start = time.perf_counter_ns()
                        frame = twin.step(1.0)
                        raw = twin.raw()
                        latencies.append((time.perf_counter_ns() - start) / 1e6)
                        digest.update(raw + b"\n")
                        truth = max(c.temperature_c for c in frame.ground_truth.cells)
                        observed = max(c.temperature_c for c in frame.cells)
                        max_truth, max_observed = max(max_truth, truth), max(max_observed, observed)
                        max_residual = max(max_residual, abs(frame.ground_truth.energy_residual_j))
                        if (
                            truth > 80
                            and observed < 80
                            and frame.measurement.packet_available
                            and first_miss is None
                        ):
                            first_miss = {
                                "simulation_time_s": frame.simulation_time_s,
                                "max_truth_c": truth,
                                "max_observed_c": observed,
                            }
                        if step % 10 == 9:
                            traces.write(raw + b"\n")
                    twin.reset()
                    replay = hashlib.sha256()
                    for _ in range(1200):
                        twin.step(1.0)
                        replay.update(twin.raw() + b"\n")
                    if replay.digest() != digest.digest():
                        raise RuntimeError("Replay mismatch")
                results.append(
                    {
                        "scenario_id": scenario.scenario_id,
                        "scenario_sha256": fingerprint(scenario),
                        "initial_snapshot": initial,
                        "trajectory_sha256": digest.hexdigest(),
                        "replay_identical": True,
                        "max_truth_c": max_truth,
                        "max_observed_c": max_observed,
                        "max_abs_energy_residual_j": max_residual,
                        "first_threshold_miss": first_miss,
                    }
                )
    sorted_latency = sorted(latencies)
    report = {
        "model_version": "coupled-factory-v3",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "container_limits": "Profile command uses 2 CPUs and 512 MiB; host has 31.29 GiB",
        "scope": (
            "Docker Linux CPU on documented Ryzen laptop; "
            "1200 seconds x 100 fixtures x 2 passes; dt=1 s; no GPU/NPU"
        ),
        "timing_scope": (
            "First-pass ctypes step + C++ serialization + Pydantic validation + "
            "second raw serialization; excludes hashing/output"
        ),
        "step_count": len(latencies),
        "total_wall_s": time.perf_counter() - began,
        "step_median_ms": statistics.median(latencies),
        "step_p95_ms": sorted_latency[int(len(latencies) * 0.95)],
        "process_peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "library_sha256": hashlib.sha256(Path("/build/libaegis_twin.so").read_bytes()).hexdigest(),
        "trajectories_sha256": hashlib.sha256(
            (output / "phase2-trajectories.ndjson.gz").read_bytes()
        ).hexdigest(),
        "results": results,
    }
    (output / "phase2-profile.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    print(
        f"Threshold misses: {sum(r['first_threshold_miss'] is not None for r in results)}/100 "
        "synthetic cases; not an anomaly detector evaluation"
    )


if __name__ == "__main__":
    main()
