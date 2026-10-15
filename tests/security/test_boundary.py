import httpx
import pytest
from aegis_api.app import create_app
from aegis_contracts.config import Settings
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError


def test_configuration_rejects_absent_short_tokens_and_remote_edge(settings):
    with pytest.raises(ValidationError):
        Settings(viewer_token=SecretStr(""), service_token=SecretStr("short"))
    with pytest.raises(ValidationError):
        Settings(**{**settings.model_dump(), "edge_url": "https://some-live-plant.invalid"})
    assert settings.viewer_token.get_secret_value() not in repr(settings)


@pytest.mark.parametrize("header", [None, "Bearer wrong", "Basic something", "Bearer "])
def test_auth_rejects_before_upstream(settings, header):
    def upstream(request):
        raise AssertionError("Unauthorized client reached edge")

    with TestClient(create_app(settings, httpx.MockTransport(upstream))) as client:
        response = client.get(
            "/api/v1/telemetry/latest", headers={"Authorization": header} if header else {}
        )
        assert response.status_code == 401
        assert response.json()["code"] == "HTTP_401"
        assert response.json()["correlation_id"] == response.headers["X-Correlation-ID"]


def test_public_mutation_paths_absent(settings):
    with TestClient(create_app(settings)) as client:
        for route in ("execute", "simulation/reset", "approval/complete"):
            response = client.post(
                f"/api/v1/{route}",
                headers={"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"},
            )
            assert response.status_code == 404


def test_rate_limit_is_bounded(settings):
    with TestClient(create_app(settings)) as client:
        headers = {"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"}
        statuses = [
            client.get("/api/v1/capabilities", headers=headers).status_code for _ in range(65)
        ]
        assert statuses[:60] == [200] * 60
        assert 429 in statuses[60:]
