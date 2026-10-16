import httpx
from aegis_api.app import create_app
from fastapi.testclient import TestClient


def test_api_passes_validated_edge_frame(settings, telemetry):
    def upstream(request):
        assert (
            request.headers["Authorization"]
            == f"Bearer {settings.service_token.get_secret_value()}"
        )
        return httpx.Response(200, json=telemetry)

    with TestClient(create_app(settings, httpx.MockTransport(upstream))) as client:
        response = client.get(
            "/api/v1/telemetry/latest",
            headers={"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"},
        )
        assert response.status_code == 200
        assert response.json() == telemetry
        assert client.get("/healthz").status_code == 200


def test_edge_outage_has_no_fabricated_telemetry(settings):
    def upstream(request):
        raise httpx.ConnectError("fixture outage")

    with TestClient(create_app(settings, httpx.MockTransport(upstream))) as client:
        response = client.get(
            "/api/v1/telemetry/latest",
            headers={"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"},
        )
        assert response.status_code == 503
        assert "cells" not in response.json()
        assert client.get("/healthz").json()["status"] == "degraded"


def test_malformed_edge_frame_rejected(settings):
    with TestClient(
        create_app(
            settings,
            httpx.MockTransport(
                lambda request: httpx.Response(200, json={"temperature_c": "invented"})
            ),
        )
    ) as client:
        response = client.get(
            "/api/v1/telemetry/latest",
            headers={"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"},
        )
        assert response.status_code == 503


def test_monitoring_ingest_has_separate_auth_and_never_fakes_disabled_storage(settings):
    import hashlib

    from aegis_contracts.models import EdgeBatch, EdgeIncident
    from pydantic import SecretStr

    ingest_token = "ingest-contract-only-" * 3
    config = settings.model_copy(update={"ingest_token": SecretStr(ingest_token)})
    batch = EdgeBatch(
        events=[
            EdgeIncident(
                event_id="a" * 64,
                run_id="00000000-0000-0000-0000-000000000001",
                state_version=1,
                simulation_time_s=0.5,
                kind="anomaly",
                evidence=[],
            )
        ]
    )
    headers = {
        "Authorization": f"Bearer {ingest_token}",
        "Content-Type": "application/json",
        "Idempotency-Key": hashlib.sha256(batch.model_dump_json().encode()).hexdigest(),
    }
    with TestClient(create_app(config)) as client:
        assert (
            client.post("/api/v1/edge/events", content=batch.model_dump_json()).status_code == 401
        )
        viewer = {**headers, "Authorization": f"Bearer {config.viewer_token.get_secret_value()}"}
        assert (
            client.post(
                "/api/v1/edge/events", headers=viewer, content=batch.model_dump_json()
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/edge/events", headers=headers, content=batch.model_dump_json()
            ).status_code
            == 503
        )
        headers["Idempotency-Key"] = "modified-batch"
        assert (
            client.post(
                "/api/v1/edge/events", headers=headers, content=batch.model_dump_json()
            ).status_code
            == 400
        )
