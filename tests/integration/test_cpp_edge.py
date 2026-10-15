import os
import subprocess
import time
from pathlib import Path

from aegis_contracts.models import PlantTelemetry, TwinMeasurement
from aegis_edge.app import create_app
from fastapi.testclient import TestClient


def test_real_cpp_deterministic_contract():
    binary = Path(os.environ.get("AEGIS_TWIN_BINARY", "/build/aegis-twin"))
    assert binary.is_file(), "Run full tests in the QA image; a real C++ binary is mandatory"
    command = [str(binary), "--seed", "42", "--steps", "10"]
    first = subprocess.check_output(command)  # noqa: S603 - fixed simulator test CLI
    second = subprocess.check_output(command)  # noqa: S603 - fixed simulator test CLI
    assert first == second
    frames = [TwinMeasurement.model_validate_json(line) for line in first.splitlines()]
    assert len(frames) == 10
    assert frames[0].cells[0].temperature_c != frames[-1].cells[0].temperature_c
    assert [frame.state_version for frame in frames] == list(range(1, 11))


def test_real_edge_streams_then_marks_dead_process_unavailable(settings):
    app = create_app(settings)
    headers = {"Authorization": f"Bearer {settings.service_token.get_secret_value()}"}
    with TestClient(app) as client:
        deadline = time.monotonic() + 5
        while client.get("/healthz").status_code != 200 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert client.get("/v1/telemetry/latest").status_code == 401
        first = PlantTelemetry.model_validate(
            client.get("/v1/telemetry/latest", headers=headers).json()
        )
        time.sleep(0.6)
        second = PlantTelemetry.model_validate(
            client.get("/v1/telemetry/latest", headers=headers).json()
        )
        assert second.run_id == first.run_id
        assert second.state_version > first.state_version
        app.state.reader.process.terminate()
        deadline = time.monotonic() + 5
        while client.get("/healthz").status_code == 200 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert client.get("/healthz").status_code == 503
        assert client.get("/v1/telemetry/latest", headers=headers).status_code == 503
