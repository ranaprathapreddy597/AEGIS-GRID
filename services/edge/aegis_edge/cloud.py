"""Bounded, idempotent AEGIS cloud-event protocol; no provider-specific API assumed."""

import asyncio
import hashlib
from collections import deque
from typing import Literal

import httpx
from aegis_contracts.models import EdgeBatch, EdgeBatchAck, EdgeIncident, EdgeStatus
from aegis_contracts.security import validate_token
from pydantic import ValidationError


class CloudOutbox:
    def __init__(self, url: str | None = None, token: str | None = None) -> None:
        if url is not None and token is None:
            raise ValueError("Cloud event delivery requires a separate token")
        if token is not None:
            validate_token(token)
        self.url, self.token = url, token
        self.events: deque[EdgeIncident] = deque(maxlen=256)
        self.recent: deque[EdgeIncident] = deque(maxlen=128)
        self.dropped = 0
        self.state: Literal["disabled", "offline", "online"] = (
            "disabled" if url is None else "offline"
        )

    def enqueue(self, event: EdgeIncident) -> None:
        if any(item.event_id == event.event_id for item in self.recent):
            return
        if len(self.events) == self.events.maxlen:
            self.dropped += 1
        self.events.append(event)
        self.recent.append(event)

    def status(self) -> EdgeStatus:
        return EdgeStatus(
            cloud=self.state,
            queued_events=len(self.events),
            dropped_events=self.dropped,
            recent_events=list(self.recent),
        )

    async def flush(self, client: httpx.AsyncClient) -> bool:
        if self.url is None or not self.events:
            return True
        batch = EdgeBatch(events=list(self.events)[:32])
        digest = hashlib.sha256(batch.model_dump_json().encode()).hexdigest()
        try:
            async with client.stream(
                "POST",
                self.url,
                content=batch.model_dump_json(),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": digest,
                },
            ) as response:
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 65536:
                        raise ValueError("Cloud acknowledgement too large")
            acknowledgement = EdgeBatchAck.model_validate_json(bytes(body))
            expected = {event.event_id for event in batch.events}
            if set(acknowledgement.accepted_event_ids) != expected or len(
                acknowledgement.accepted_event_ids
            ) != len(expected):
                raise ValueError("Incomplete cloud acknowledgement")
        except (httpx.HTTPError, ValueError, ValidationError):
            self.state = "offline"
            return False
        self.events = deque(
            (event for event in self.events if event.event_id not in expected), maxlen=256
        )
        self.state = "online"
        return True

    async def run(self) -> None:
        if self.url is None:
            return
        delay = 0.5
        async with httpx.AsyncClient(timeout=2, follow_redirects=False, trust_env=False) as client:
            while True:
                success = await self.flush(client)
                delay = 0.5 if success else min(30, delay * 2)
                await asyncio.sleep(delay)
