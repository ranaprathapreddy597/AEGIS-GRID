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


def test_real_edge_accepts_accounted_packet_loss(settings):
    config = settings.model_copy(update={"scenario_id": "scenario-070", "time_scale": 20.0})
    app = create_app(config)
    headers = {"Authorization": f"Bearer {settings.service_token.get_secret_value()}"}
    with TestClient(app) as client:
        deadline = time.monotonic() + 8
        saw_loss = False
        while time.monotonic() < deadline:
            response = client.get("/v1/telemetry/latest", headers=headers)
            if response.status_code == 200:
                frame = PlantTelemetry.model_validate(response.json())
                if frame.measurement.dropped_packets >= 3:
                    saw_loss = True
                    break
            time.sleep(0.1)
        assert saw_loss
        assert client.get("/healthz").status_code == 200


def test_real_cloud_refusal_does_not_disable_simulator_safety(settings):
    from pydantic import SecretStr

    config = settings.model_copy(
        update={
            "scenario_id": "scenario-090",
            "time_scale": 20.0,
            "cloud_events_url": "https://127.0.0.1:9/api/v1/edge/events",
            "cloud_token": SecretStr("real-loopback-refusal-fixture-" * 3),
        }
    )
    app = create_app(config)
    headers = {"Authorization": f"Bearer {settings.service_token.get_secret_value()}"}
    with TestClient(app) as client:
        deadline = time.monotonic() + 30
        stopped = False
        while time.monotonic() < deadline:
            response = client.get("/v1/telemetry/latest", headers=headers)
            if response.status_code == 200:
                frame = PlantTelemetry.model_validate(response.json())
                if frame.sentinel.latched and max(c.load_fraction for c in frame.cells) < 0.001:
                    stopped = True
                    break
            time.sleep(0.1)
        assert stopped
        assert client.get("/healthz").status_code == 200
        status = client.get("/v1/edge/status", headers=headers).json()
        assert status["cloud"] == "offline"
        assert status["queued_events"] == 2
