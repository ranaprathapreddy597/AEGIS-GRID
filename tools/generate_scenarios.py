"""Preregister 10 synthetic fault families x 10 seeds; no benchmark outcomes as labels."""

import argparse
import json
from pathlib import Path

from aegis_contracts.models import Scenario

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = [
    ("healthy", 0),
    ("spoof", 1),
    ("freeze", 2),
    ("blockage", 4),
    ("pump_degradation", 8),
    ("demand_burst", 16),
    ("measurement_delay", 32),
    ("packet_loss", 64),
    ("power_spike", 128),
    ("deceptive_cascade", 157),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    directory = ROOT / "data/scenarios"
    directory.mkdir(exist_ok=True, parents=True)
    for family_index, (label, mask) in enumerate(FAMILIES):
        for trial in range(10):
            index = family_index * 10 + trial
            scenario = Scenario(
                scenario_id=f"scenario-{index:03}",
                seed=42 + trial * 7919,
                fault_mask=mask,
                severity=1.0 - 0.01 * trial,
                start_s=30.0,
                noise_c=0.1,
                target=trial % 6,
                delay_steps=4 + trial,
                drop_every=3 + trial % 3,
            )
            fixture = {
                "fixture_version": "3.0.0",
                "model_version": "coupled-factory-v3",
                "label": label,
                "label_source": "injected synthetic cause, not inferred diagnosis",
                "initial_state": "seeded reset; full state recorded by tools/profile_twin.py",
                "config": scenario.model_dump(),
            }
            path = directory / f"{scenario.scenario_id}.json"
            content = json.dumps(fixture, sort_keys=True, indent=2) + "\n"
            if args.check:
                if path.read_text() != content:
                    raise SystemExit(f"Scenario fixture drift: {path.name}")
            else:
                path.write_text(content, newline="\n")
    print("100 deterministic scenario fixtures checked" if args.check else "100 fixtures generated")


if __name__ == "__main__":
    main()
