"""Actual CPU sentinel + C++ rollouts with an unreachable loopback HTTPS receiver."""

import asyncio
import hashlib
import json
import resource
import statistics
import time
from pathlib import Path

import httpx
from aegis_contracts.models import EdgeIncident
from aegis_edge.cloud import CloudOutbox
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file


async def main() -> None:
    started = time.perf_counter()
    rows = []
    timings = []
    indexes = list(range(5)) + list(range(90, 100))
    for index in indexes:
        scenario = scenario_from_file(Path("data/scenarios"), f"scenario-{index:03}")
        supervisor = SupervisedTwin(scenario, Path("/build/libaegis_twin.so"))
        outbox = CloudOutbox(
            "https://127.0.0.1:9/api/v1/edge/events", "offline-profile-fixture-" * 3
        )
        detection = None
        max_truth = 0.0
        digest = hashlib.sha256()
        attempted = False
        try:
            async with httpx.AsyncClient(
                timeout=0.2, trust_env=False, follow_redirects=False
            ) as client:
                for _ in range(1200):
                    begin = time.perf_counter_ns()
                    frame, status = supervisor.step(1.0)
                    timings.append((time.perf_counter_ns() - begin) / 1e6)
                    max_truth = max(
                        max_truth, max(c.temperature_c for c in frame.ground_truth.cells)
                    )
                    digest.update(frame.model_dump_json().encode())
                    if status is not None and status.latched and detection is None:
                        detection = frame.simulation_time_s
                        outbox.enqueue(
                            EdgeIncident(
                                event_id=hashlib.sha256(f"profile:{index}".encode()).hexdigest(),
                                run_id="00000000-0000-0000-0000-000000000001",
                                state_version=frame.state_version,
                                simulation_time_s=detection,
                                kind="local_stop",
                                evidence=status.evidence,
                            )
                        )
                        attempted = True
                        if await outbox.flush(client):
                            raise RuntimeError("Expected unreachable local HTTPS receiver")
                if index >= 90 and (detection is None or max_truth >= 70 or not attempted):
                    raise RuntimeError("Deceptive scenario safety gate failed")
                if index < 5 and detection is not None:
                    raise RuntimeError("Healthy scenario false alarm")
            rows.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "first_detection_s": detection,
                    "maximum_truth_c": max_truth,
                    "trajectory_sha256": digest.hexdigest(),
                    "final_max_load": max(c.load_fraction for c in frame.cells),
                    "cloud": outbox.state,
                    "queued_events": len(outbox.events),
                    "memory_entries": status.memory_entries if status else 0,
                }
            )
        finally:
            supervisor.close()
    ordered = sorted(timings)
    report = {
        "execution": "Linux CPU C++/ctypes + observer + FAISS + shield; network-none container",
        "scope": "15 development fixtures, 1200 simulated seconds each; dt=1 s; no held-out set",
        "cloud_test": "Refused HTTPS loopback port 9; no provider or successful TLS claim",
        "steps": len(timings),
        "wall_s": time.perf_counter() - started,
        "full_step_median_ms": statistics.median(timings),
        "full_step_p95_ms": ordered[int(len(ordered) * 0.95)],
        "process_peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "results": rows,
    }
    path = Path("docs/results/phase3-sentinel-profile.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
