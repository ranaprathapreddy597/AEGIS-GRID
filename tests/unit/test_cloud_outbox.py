import asyncio

import httpx
import pytest
from aegis_contracts.config import Settings
from aegis_contracts.models import EdgeIncident
from aegis_edge.cloud import CloudOutbox
from pydantic import ValidationError


def event(index):
    return EdgeIncident(
        event_id=f"{index:064x}",
        run_id="00000000-0000-0000-0000-000000000001",
        state_version=index + 1,
        simulation_time_s=float(index),
        kind="anomaly",
        evidence=[],
    )


def test_outage_queue_is_bounded_and_reconnect_retries_idempotently():
    async def scenario():
        outbox = CloudOutbox("https://cloud.test/api/v1/edge/events", "test-cloud-only-" * 3)
        for i in range(300):
            outbox.enqueue(event(i))
        assert outbox.status().queued_events == 256
        assert outbox.status().dropped_events == 44
        assert len(outbox.status().recent_events) == 128
        keys = []

        def outage(request):
            keys.append(request.headers["Idempotency-Key"])
            raise httpx.ConnectError("Explicit cloud outage test double")

        async with httpx.AsyncClient(transport=httpx.MockTransport(outage)) as client:
            assert not await outbox.flush(client)
            assert not await outbox.flush(client)
        assert keys[0] == keys[1]
        assert outbox.status().cloud == "offline"
        assert len(outbox.events) == 256
        batch_ids = [e.event_id for e in list(outbox.events)[:32]]

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"accepted_event_ids": batch_ids})
            )
        ) as client:
            assert await outbox.flush(client)
        assert outbox.status().cloud == "online"
        assert len(outbox.events) == 224

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "response",
    [
        {"accepted_event_ids": []},
        {"accepted_event_ids": ["unknown"]},
        {"accepted_event_ids": [f"{0:064x}"], "commands": [{"pump": 0}]},
    ],
)
def test_partial_or_injected_cloud_ack_cannot_clear_queue_or_control_plant(response):
    async def scenario():
        outbox = CloudOutbox("https://cloud.test/api/v1/edge/events", "test-cloud-only-" * 3)
        outbox.enqueue(event(0))
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json=response))
        ) as client:
            assert not await outbox.flush(client)
        assert len(outbox.events) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "url",
    [
        "http://cloud.test/api/v1/edge/events",
        "https://user:pass@cloud.test/api/v1/edge/events",
        "https://cloud.test/unknown",
        "https://cloud.test/api/v1/edge/events?token=bad",
    ],
)
def test_config_requires_explicit_tls_without_url_credentials(settings, url):
    with pytest.raises(ValidationError):
        Settings.model_validate({**settings.model_dump(), "cloud_events_url": url})
