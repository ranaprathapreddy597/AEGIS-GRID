"""Actual network-isolated CPU search profile; no generated benchmark measurements."""

import argparse
import hashlib
import json
import platform
import resource
import time
from pathlib import Path

from aegis_agents.optimizer import optimize
from aegis_contracts.models import EdgeIncident, IncidentRecord, SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    library = Path("/build/libaegis_twin.so")
    supervisor = SupervisedTwin(scenario_from_file(Path("data/scenarios"), "scenario-090"), library)
    try:
        for _ in range(300):
            frame, status = supervisor.step(1.0)
            if status.latched:
                break
        if supervisor.incident_snapshot is None:
            raise RuntimeError("Actual seeded detection required")
        event = EdgeIncident(
            event_id="8" * 64,
            run_id="00000000-0000-0000-0000-000000000008",
            kind="anomaly",
            state_version=frame.state_version,
            simulation_time_s=frame.simulation_time_s,
            evidence=status.evidence,
            observed=SensorFrame.from_twin(frame),
            snapshot=supervisor.incident_snapshot,
        )
        record = IncidentRecord(
            incident_id=event.event_id,
            ingested_at="2026-10-16T00:00:00Z",
            payload_sha256=hashlib.sha256(event.model_dump_json().encode()).hexdigest(),
            event=event,
        )
        started = time.perf_counter()
        report = optimize(record, library)
        elapsed = time.perf_counter() - started
        output = {
            "mode": "actual_cpp_synthetic_physics_cpu_only",
            "python": platform.python_version(),
            "elapsed_s": elapsed,
            "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            "rollouts_per_s": report.total_rollouts / elapsed,
            "excludes": "Docker/WSL/other processes; GPU/NPU not used; single development incident",
            "incident": record.model_dump(),
            "assessment": report.model_dump(),
        }
        args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    key: value
                    for key, value in output.items()
                    if key not in {"incident", "assessment"}
                }
            )
        )
    finally:
        supervisor.close()


if __name__ == "__main__":
    main()
