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
