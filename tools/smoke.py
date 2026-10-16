"""Actual HTTP/SSE checks against the running local Docker stack."""

import json
import os

import httpx
from aegis_contracts.models import PlantTelemetry
from dev import read_env


def main() -> None:
    token = read_env()["AEGIS_VIEWER_TOKEN"]
    port = os.environ.get("AEGIS_WEB_PORT", read_env().get("AEGIS_WEB_PORT", "8080"))
    with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=15, trust_env=False) as client:
        client.get("/healthz").raise_for_status()
        if client.get("/api/v1/telemetry/latest").status_code != 401:
            raise SystemExit("Unauthorized read accepted")
        headers = {"Authorization": f"Bearer {token}"}
        first = PlantTelemetry.model_validate_json(
            client.get("/api/v1/telemetry/latest", headers=headers).content
        )
        frames = []
        with client.stream("GET", "/api/v1/telemetry/stream", headers=headers) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: ") and "state_version" in line:
                    frames.append(PlantTelemetry.model_validate_json(line[6:]))
                if len(frames) == 3:
                    break
        if len(frames) != 3 or frames[-1].state_version <= frames[0].state_version:
            raise SystemExit("SSE did not deliver increasing frames")
        if frames[-1].cells[0].temperature_c == frames[0].cells[0].temperature_c:
            raise SystemExit("Simulator temperature did not change")
        for route in ("/api/v1/execute", "/api/v1/simulation/reset", "/api/v1/approval/complete"):
            if client.post(route, headers=headers).status_code not in (404, 405):
                raise SystemExit("Unexpected mutation route")
        print(
            json.dumps(
                {
                    "result": "PASS",
                    "source": first.source,
                    "sse_frames": len(frames),
                    "temperature_changed": True,
                    "unauthorized_reads": "denied",
                    "mutations": "general writes unavailable; passkey sandbox checked separately",
                }
            )
        )


if __name__ == "__main__":
    main()
