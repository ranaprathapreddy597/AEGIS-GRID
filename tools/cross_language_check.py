"""Validate an actual C++ → Python → HTTP frame in generated JSON Schema/Node."""

import copy
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from aegis_contracts.models import PlantTelemetry
from dev import ROOT, read_env


def main() -> None:
    config = read_env()
    port = os.environ.get("AEGIS_WEB_PORT", config.get("AEGIS_WEB_PORT", "8080"))
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/v1/telemetry/latest",
        headers={"Authorization": f"Bearer {config['AEGIS_VIEWER_TOKEN']}"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310 - fixed loopback origin
        raw = json.load(response)
    PlantTelemetry.model_validate(raw)
    node = shutil.which("node")
    if node is None:
        raise SystemExit("Node 24 is required")
    cli = ROOT / "services/executor/dist/services/executor/src/contract-check.js"
    schema = ROOT / "packages/contracts/generated/plant-telemetry.schema.json"
    with tempfile.TemporaryDirectory(prefix="aegis-contract-", dir=ROOT / ".run") as directory:
        path = Path(directory) / "frame.json"

        def check(data: dict, expected: int) -> None:
            path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [node, str(cli), str(schema), str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            if result.returncode != expected:
                raise RuntimeError("Actual Node contract verification failed; no input data logged")

        check(raw, 0)
        bad_type = copy.deepcopy(raw)
        bad_type["cells"][0]["temperature_c"] = "38.0"
        bad_order = copy.deepcopy(raw)
        bad_order["cells"][1]["cell_id"] = "CELL-01"
        bad_extra = {**raw, "commands": [{"pump": 0}]}
        bad_flow = copy.deepcopy(raw)
        bad_flow["ground_truth"]["total_flow_kg_s"] += 0.1
        for invalid in [bad_type, bad_order, bad_extra, bad_flow]:
            check(invalid, 1)
    print(
        json.dumps(
            {
                "result": "PASS",
                "actual_frame": True,
                "boundaries": [
                    "C++",
                    "Python/Pydantic",
                    "HTTP",
                    "Node/AJV",
                    "generated TypeScript",
                ],
                "invalid_frames_rejected": 4,
                "react_actual_frame_test": "Playwright gate",
            }
        )
    )


if __name__ == "__main__":
    main()
