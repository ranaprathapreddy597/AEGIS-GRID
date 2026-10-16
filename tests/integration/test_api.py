import httpx
from aegis_api.app import create_app
from fastapi.testclient import TestClient


def test_investigation_boundaries_do_not_fake_unconfigured_persistence(settings):
    with TestClient(create_app(settings)) as client:
        path = "/api/v1/incidents/" + "a" * 64 + "/investigate"
        assert client.post(path).status_code == 401
        headers = {
            "Authorization": f"Bearer {settings.viewer_token.get_secret_value()}",
            "Idempotency-Key": "00000000-0000-0000-0000-000000000007",
        }
        assert client.post(path, headers=headers).status_code == 503
        assert (
            client.post(path, headers={**headers, "Idempotency-Key": "invalid"}).status_code == 422
        )
        assert client.post(
            "/api/v1/investigations/resume", headers=headers, json={"approved": True}
        ).status_code in {404, 405}


def test_inference_projection_is_authenticated_and_never_claims_device_measurement(settings):
    with TestClient(create_app(settings)) as client:
        headers = {"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"}
        assert client.get("/api/v1/inference/memory").status_code == 401
        status = client.get("/api/v1/inference/status", headers=headers).json()
        assert status["state"] == "blocked" and not status["hardware_verified"]
        budget = client.get("/api/v1/inference/memory", headers=headers).json()
        assert not budget["projected_fits"] and not budget["hardware_measured"]
        assert budget["kv_gib"] == 48
        assert (
            client.get(
                "/api/v1/inference/memory?context_tokens=262145", headers=headers
            ).status_code
            == 422
        )


def test_manual_api_citations_refusal_auth_and_exact_source(settings):
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/manuals/evidence").status_code == 401
        headers = {"Authorization": f"Bearer {settings.viewer_token.get_secret_value()}"}
        response = client.get("/api/v1/manuals/evidence", headers=headers)
        assert response.status_code == 200
        evidence = response.json()
        assert evidence["pages"] == 1000 and evidence["decision"]["status"] == "no_action"
        assert evidence["hits"] and not evidence["evolus_live"] and not evidence["pinecone_live"]
        assert client.get("/api/v1/manuals/SIM-MANUAL/source").status_code == 401
        pdf = client.get("/api/v1/manuals/SIM-BULLETIN/source", headers=headers)
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
        assert "attachment" in pdf.headers["content-disposition"]
        assert client.get("/api/v1/manuals/unknown/source", headers=headers).status_code == 404
        assert (
            client.get("/api/v1/manuals/evidence?query=" + "x" * 501, headers=headers).status_code
            == 422
        )


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
