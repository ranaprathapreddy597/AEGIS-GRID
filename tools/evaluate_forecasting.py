"""Frozen synthetic forecast protocol: native truth labels, observed-only predictions."""

import argparse
import hashlib
import json
import statistics
from collections import deque
from pathlib import Path

from aegis_agents.forecasting import forecast
from aegis_contracts.models import SensorFrame
from aegis_edge.twin import NativeTwin, scenario_from_file

PROTOCOL = {
    "version": "thermal-forecast-heldout-v1",
    "target": "any true cell temperature >=70 C in next 60 seconds",
    "seeds": [710001, 710002, 710003],
    "families": list(range(10)),
    "horizon_s": 60,
    "duration_s": 600,
    "evaluation_stride_s": 10,
    "training": "none; fixed trailing 30-second ordinary least squares",
    "holdout": "new seeds; existing fault families, no real-world or unseen-family claim",
}


def metrics(rows: list[dict], method: str) -> dict:
    covered = [row for row in rows if row[method] is not None]
    tp = sum(row[method] and row["positive"] for row in covered)
    fp = sum(row[method] and not row["positive"] for row in covered)
    fn = sum(not row[method] and row["positive"] for row in covered)
    tn = len(covered) - tp - fp - fn
    leads = [row["crossing_in_s"] for row in covered if row[method] and row["positive"]]
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "coverage": len(covered) / len(rows),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall_covered": tp / (tp + fn) if tp + fn else None,
        "recall_all_positives": tp / sum(row["positive"] for row in rows)
        if any(row["positive"] for row in rows)
        else None,
        "accuracy_covered": (tp + tn) / len(covered) if covered else None,
        "false_positive_rate_covered": fp / (fp + tn) if fp + tn else None,
        "median_warning_lead_time_s": statistics.median(leads) if leads else None,
    }


def evaluate(library: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Use a new output; never overwrite measured evidence")
    rows, trajectories = [], []
    for family in PROTOCOL["families"]:
        for seed in PROTOCOL["seeds"]:
            scenario = scenario_from_file(
                Path("data/scenarios"), f"scenario-{family * 10:03}", seed
            )
            frames = []
            trajectory = hashlib.sha256()
            with NativeTwin(scenario, library) as twin:
                for _ in range(PROTOCOL["duration_s"]):
                    frame = twin.step(1.0)
                    trajectory.update(frame.model_dump_json().encode())
                    frames.append(frame)
            trajectories.append({"family": family, "seed": seed, "sha256": trajectory.hexdigest()})
            history: deque[SensorFrame] = deque(maxlen=121)
            for index, frame in enumerate(frames):
                history.append(SensorFrame.from_twin(frame))
                second = index + 1
                if second % 10 or second > 540:
                    continue
                # Forecast future failures only: current hazards are existing detections.
                if max(cell.temperature_c for cell in frame.ground_truth.cells) >= 70:
                    continue
                future = frames[index + 1 : index + 61]
                crossing = next(
                    (
                        offset
                        for offset, item in enumerate(future, 1)
                        if max(cell.temperature_c for cell in item.ground_truth.cells) >= 70
                    ),
                    None,
                )
                result = forecast(list(history))
                observed = max(cell.temperature_c for cell in frame.cells)
                rows.append(
                    {
                        "family": family,
                        "seed": seed,
                        "time_s": second,
                        "positive": crossing is not None,
                        "crossing_in_s": crossing,
                        "trend": result.warning if result.status == "available" else None,
                        "persistence": observed >= 70
                        if frame.measurement.packet_available
                        else None,
                        "operating_guard": observed >= 65
                        if frame.measurement.packet_available
                        else None,
                        "forecast_status": result.status,
                    }
                )
    result = {
        "protocol": PROTOCOL,
        "protocol_sha256": hashlib.sha256(
            json.dumps(PROTOCOL, sort_keys=True).encode()
        ).hexdigest(),
        "native_binary_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
        "forecast_source_sha256": hashlib.sha256(
            Path("services/agents/aegis_agents/forecasting.py").read_bytes()
        ).hexdigest(),
        "episodes": len(trajectories),
        "windows": len(rows),
        "positive_windows": sum(row["positive"] for row in rows),
        "metrics": {
            method: metrics(rows, method) for method in ("trend", "persistence", "operating_guard")
        },
        "limitations": [
            "Overlapping episode windows are correlated; no independent-window CI claimed.",
            "Lead times summarize true-positive windows, not independent incident detection.",
            "Target is future thermal crossing, not fault identity or pre-onset fault prediction.",
            "Synthetic seeds held out; known fault families, no real-plant calibration.",
            "No parameters fitted or tuned on these results; protocol and source hashes retained.",
        ],
        "trajectories": trajectories,
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as target:
        target.write(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path("/build/libaegis_twin.so"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    measured = evaluate(args.library, args.output)
    print(json.dumps({key: measured[key] for key in ("episodes", "windows", "metrics")}, indent=2))
