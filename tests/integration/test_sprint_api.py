"""New analysis paths have no plant write scope and never fabricate missing observations."""

from aegis_api.app import create_app
from aegis_contracts.models import SensorFrame
from fastapi.testclient import TestClient


def test_recorded_evidence_is_authenticated_and_discloses_baselines(settings):
    with TestClient(create_app(settings)) as client:
        path = "/api/v1/analysis/sprint-evidence"
        assert client.get(path).status_code == 401
        response = client.get(
            path, headers={"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["execution_authority"] is False
        assert len(body["experiments"]) == 6
        assert len(body["attacks"]) == 6
        assert all(item["artifact_sha256"] for item in body["experiments"])
        assert body["experiments"][-1]["state"] == "PASS"
        assert all(item["state"] == "PARTIAL" for item in body["experiments"][:-1])


def test_forecast_api_requires_auth_and_only_observed_fields(settings, telemetry):
    observed = SensorFrame.model_validate(
        {name: telemetry[name] for name in SensorFrame.model_fields}
    ).model_dump()
    with TestClient(create_app(settings)) as client:
        endpoint = "/api/v1/analysis/forecast"
        assert client.post(endpoint, json={"history": [observed]}).status_code == 401
        headers = {"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"}
        response = client.post(endpoint, headers=headers, json={"history": [observed]})
        assert response.status_code == 200
        assert response.json()["status"] == "abstained"
        assert response.json()["execution_authority"] is False
        assert client.post(endpoint, headers=headers, json={"history": []}).status_code == 422
        assert (
            client.post(endpoint, headers=headers, json={"history": [telemetry]}).status_code == 422
        )
        assert (
            client.post(
                endpoint, headers=headers, json={"history": [observed, observed]}
            ).status_code
            == 422
        )
