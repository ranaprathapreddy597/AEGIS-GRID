"""Native fault-free control confounders, separated from fault-diagnosis holdout."""

import argparse
import hashlib
import json
from pathlib import Path

from aegis_agents.quality import grounded_diagnose
from aegis_contracts.models import SensorFrame, SimulatorControls
from aegis_edge.sentinel import PhysicsObserver
from aegis_edge.twin import NativeTwin, scenario_from_file
from evaluate_sprint_ai import legacy, metrics

CONTROLS = {
    "commanded_low_pump": SimulatorControls(pump=0.2, loads=[0.2] * 6, valves=[1.0] * 6),
    "commanded_high_load": SimulatorControls(pump=1.0, loads=[1.0] * 6, valves=[1.0] * 6),
    "commanded_closed_idle_branches": SimulatorControls(
        pump=1.0, loads=[0.0] * 6, valves=[0.0] * 6
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--library", type=Path, default=Path("/build/libaegis_twin.so"))
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Do not replace previous evidence")
    rows = []
    for name, controls in CONTROLS.items():
        for repeat in range(10):
            seed = 2734001 + repeat * 7919
            scenario = scenario_from_file(Path("data/scenarios"), "scenario-000", seed)
            observer = PhysicsObserver()
            with NativeTwin(scenario, args.library) as twin:
                initial = twin.step(1.0)
                twin.controls(initial.state_version, controls)
                for _ in range(60):
                    sensor = SensorFrame.from_twin(twin.step(1.0))
                    evidence = observer.update(sensor)
                rows.append(
                    {
                        "fixture": name,
                        "seed": seed,
                        "expected_causes": [],
                        "legacy_causes": legacy(sensor, evidence),
                        "grounded_causes": [h.cause for h in grounded_diagnose(sensor, evidence)],
                        "observed_sha256": hashlib.sha256(
                            sensor.model_dump_json().encode()
                        ).hexdigest(),
                    }
                )
    report = {
        "status": "measured_synthetic_native_confounders",
        "protocol": "fault-free native controls, 60s settling, ten seeds per command fixture",
        "authority": "private native clones; command context never supplied to diagnosis",
        "legacy": metrics(rows, "legacy_causes"),
        "grounded": metrics(rows, "grounded_causes"),
        "limitations": "Targeted post-development confounders, not independent fault holdout",
        "rows": rows,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["status", "legacy", "grounded"]}))


if __name__ == "__main__":
    main()
