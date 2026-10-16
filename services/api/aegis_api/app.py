import asyncio
import hashlib
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from aegis_contracts.config import Settings
from aegis_contracts.http import install_http_boundary
from aegis_contracts.inference import InferenceStatus, MemoryBudget
from aegis_contracts.manuals import ManualEvidence
from aegis_contracts.models import (
    Capabilities,
    Capability,
    EdgeBatch,
    EdgeBatchAck,
    EdgeStatus,
    ErrorResponse,
    Health,
    IncidentPage,
    IncidentReplay,
    PlantTelemetry,
    StorageStatus,
)
from aegis_contracts.security import RequireToken
from aegis_inference.budget import calculate, metadata
from aegis_ingestion.library import fixture_library
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi import Path as ApiPath
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from redis.exceptions import RedisError

from aegis_api.storage import EventConflict, StorageUnavailable, TelemetryStore

logger = logging.getLogger("aegis.api")


class RateLimit:
    """Bounded, single-process local rate limiter; Redis policy arrives in Phase 4."""

    def __init__(self) -> None:
        self.tokens = 60.0
        self.updated = time.monotonic()

    async def __call__(self) -> None:
        now = time.monotonic()
        self.tokens = min(60.0, self.tokens + (now - self.updated))
        self.updated = now
        if self.tokens < 1:
            raise HTTPException(429, "Local read rate exceeded", headers={"Retry-After": "1"})
        self.tokens -= 1


def create_app(
    settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None
) -> FastAPI:
    config = settings or Settings.from_env()
    active_streams = 0
    store = TelemetryStore(config)

    async def collect(client: httpx.AsyncClient) -> None:
        while True:
            try:
                await store.probe()
                response = await client.get("/v1/edge/status")
                response.raise_for_status()
                status = EdgeStatus.model_validate_json(response.content)
                for event in status.recent_events:
                    await store.append(event)
                await store.publish_pending()
            except (httpx.HTTPError, PyMongoError, RedisError, ValueError, StorageUnavailable):
                logger.warning("Monitoring collection unavailable; journal retained")
            await asyncio.sleep(1)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(
            base_url=config.edge_url,
            timeout=2,
            transport=transport,
            headers={"Authorization": f"Bearer {config.service_token.get_secret_value()}"},
            follow_redirects=False,
            trust_env=False,
        ) as client:
            app.state.edge = client
            app.state.store = store
            worker = asyncio.create_task(collect(client)) if config.storage_enabled else None
            try:
                yield
            finally:
                if worker is not None:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
                await store.close()

    app = FastAPI(
        title="AEGIS GRID API",
        responses={422: {"model": ErrorResponse}},
        version="0.2.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_http_boundary(app)
    auth = Depends(RequireToken(config.viewer_token.get_secret_value()))
    limit = Depends(RateLimit())
    errors: dict[int | str, dict[str, Any]] = {
        code: {"model": ErrorResponse} for code in (401, 429, 503)
    }

    @app.get(
        "/api/v1/inference/status",
        response_model=InferenceStatus,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def inference_status() -> InferenceStatus:
        info, config = metadata()
        return InferenceStatus(
            state="blocked",
            model_id=info["model_id"],
            native_context_tokens=config["max_position_embeddings"],
            reason="Provisioned MI300X, runtime/device logs and live path are pending",
        )

    @app.get(
        "/api/v1/inference/memory",
        response_model=MemoryBudget,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def memory_budget(
        context_tokens: Annotated[int, Query(ge=1, le=262144)] = 262144,
        sequences: Annotated[int, Query(ge=1, le=2)] = 2,
        capacity_gib: Annotated[int, Query(ge=1, le=512)] = 80,
        kv_dtype: Literal["bf16", "fp8"] = "bf16",
    ) -> MemoryBudget:
        return calculate(context_tokens, sequences, kv_dtype, capacity_gib * 1024**3)

    @app.get(
        "/api/v1/manuals/evidence",
        response_model=ManualEvidence,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def manual_evidence(
        query: Annotated[str, Query(min_length=1, max_length=500)] = "CELL-01 temperature",
    ) -> ManualEvidence:
        try:
            return await asyncio.to_thread(lambda: fixture_library().evidence(query))
        except (ValueError, OSError):
            raise HTTPException(503, "Manual evidence integrity or availability failed") from None

    @app.get(
        "/api/v1/manuals/{document_id}/source",
        response_class=FileResponse,
        dependencies=[auth, limit],
        responses={**errors, 404: {"model": ErrorResponse}},
    )
    async def manual_source(document_id: str) -> FileResponse:
        names = {"SIM-MANUAL": "synthetic-manual.pdf", "SIM-BULLETIN": "contradictory-bulletin.pdf"}
        name = names.get(document_id)
        if name is None:
            raise HTTPException(404, "Manual source not found")
        try:
            await asyncio.to_thread(fixture_library)
        except (ValueError, OSError):
            raise HTTPException(503, "Manual source integrity failed") from None
        return FileResponse(
            Path("data/manuals") / name, media_type="application/pdf", filename=name
        )

    async def ingest_auth(authorization: Annotated[str | None, Header()] = None) -> None:
        if config.ingest_token is None:
            raise HTTPException(503, "Monitoring receiver is not configured")
        RequireToken(config.ingest_token.get_secret_value())(authorization)

    @app.post(
        "/api/v1/edge/events",
        response_model=EdgeBatchAck,
        dependencies=[Depends(ingest_auth), limit],
        responses=errors,
    )
    async def ingest(
        batch: EdgeBatch, idempotency_key: Annotated[str | None, Header()] = None
    ) -> EdgeBatchAck:
        digest = hashlib.sha256(batch.model_dump_json().encode()).hexdigest()
        if idempotency_key != digest:
            raise HTTPException(400, "Canonical batch digest mismatch")
        try:
            for event in batch.events:
                await store.append(event)
            return EdgeBatchAck(accepted_event_ids=[event.event_id for event in batch.events])
        except EventConflict as exc:
            raise HTTPException(409, "Event ID conflicts with immutable journal") from exc
        except (PyMongoError, StorageUnavailable) as exc:
            raise HTTPException(
                503, "Durable journal unavailable; retry without changing events"
            ) from exc

    @app.get(
        "/api/v1/storage/status",
        response_model=StorageStatus,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def storage_status() -> StorageStatus:
        return await store.probe()

    @app.get(
        "/api/v1/incidents",
        response_model=IncidentPage,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def incidents() -> IncidentPage:
        try:
            return await store.incidents()
        except (PyMongoError, StorageUnavailable) as exc:
            raise HTTPException(503, "Incident journal unavailable") from exc

    @app.get(
        "/api/v1/incidents/{incident_id}/replay",
        response_model=IncidentReplay,
        dependencies=[auth, limit],
        responses={**errors, 404: {"model": ErrorResponse}},
    )
    async def replay(
        incident_id: Annotated[str, ApiPath(pattern=r"^[0-9a-f]{64}$")],
    ) -> IncidentReplay:
        try:
            result = await store.replay(incident_id)
        except (PyMongoError, StorageUnavailable) as exc:
            raise HTTPException(503, "Incident replay unavailable") from exc
        if result is None:
            raise HTTPException(404, "Incident not found")
        return result

    async def read_edge() -> PlantTelemetry:
        try:
            response = await app.state.edge.get("/v1/telemetry/latest")
            response.raise_for_status()
            return PlantTelemetry.model_validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as exc:
            raise HTTPException(503, "Edge telemetry unavailable") from exc

    @app.get(
        "/api/v1/edge/status",
        response_model=EdgeStatus,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def edge_status() -> EdgeStatus:
        try:
            response = await app.state.edge.get("/v1/edge/status")
            response.raise_for_status()
            return EdgeStatus.model_validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as exc:
            raise HTTPException(503, "Edge status unavailable") from exc

    @app.get("/healthz", response_model=Health)
    async def health() -> JSONResponse:
        status: Literal["ok", "degraded"]
        try:
            await read_edge()
            if config.storage_enabled and store.mongo_state != "ready":
                raise HTTPException(503, "Persistent monitoring journal unavailable")
            status, detail = "ok", "Edge telemetry reachable"
        except HTTPException:
            status, detail = "degraded", "Edge telemetry unavailable"
        body = Health(status=status, service="api", detail=detail)
        return JSONResponse(body.model_dump(), status_code=200 if status == "ok" else 503)

    @app.get(
        "/api/v1/capabilities",
        response_model=Capabilities,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def capabilities() -> Capabilities:
        return Capabilities(
            capabilities=[
                Capability(
                    name="C++ coupled factory twin",
                    status="simulated",
                    detail="Shared coolant, feeder, seeded faults and replay; synthetic parameters",
                ),
                Capability(
                    name="Telemetry transport",
                    status="verified_local",
                    detail="C++ C ABI + isolated sentinel → edge → API SSE → React",
                ),
                Capability(
                    name="MI300X inference",
                    status="blocked",
                    detail="No provisioned endpoint or hardware evidence",
                ),
                Capability(
                    name="Evolus / Pinecone",
                    status="blocked",
                    detail="Read adapters and synthetic corpus; live provider reads unverified",
                ),
                Capability(
                    name="Passkeys / operational mutations",
                    status="not_implemented",
                    detail="No mutation routes; implemented in later phases",
                ),
                Capability(
                    name="Local edge safety / FAISS",
                    status="verified_local",
                    detail="Sensor-only observer, bounded FAISS memory and synthetic local safety",
                ),
                Capability(
                    name="Redis / MongoDB persistence",
                    status="verified_local" if config.storage_enabled else "not_implemented",
                    detail="Append-only Mongo journal and bounded Redis fanout; read-only replay",
                ),
            ]
        )

    @app.get(
        "/api/v1/telemetry/latest",
        response_model=PlantTelemetry,
        dependencies=[auth, limit],
        responses=errors,
    )
    async def latest() -> PlantTelemetry:
        return await read_edge()

    @app.get(
        "/api/v1/telemetry/stream",
        dependencies=[auth, limit],
        responses={
            200: {
                "content": {"text/event-stream": {}},
                "description": "SSE telemetry and status events",
            },
            **errors,
        },
    )
    async def stream(request: Request) -> StreamingResponse:
        nonlocal active_streams
        if active_streams >= 8:
            raise HTTPException(429, "Local stream capacity reached", headers={"Retry-After": "3"})
        active_streams += 1

        async def events() -> AsyncIterator[str]:
            nonlocal active_streams
            last_identity: tuple[str, int] | None = None
            last_changed = time.monotonic()
            try:
                while not await request.is_disconnected():
                    try:
                        telemetry = await read_edge()
                        identity = telemetry.run_id, telemetry.state_version
                        if identity != last_identity:
                            last_identity = identity
                            last_changed = time.monotonic()
                            yield (
                                f"id: {telemetry.run_id}:{telemetry.state_version}\n"
                                f"event: telemetry\ndata: {telemetry.model_dump_json()}\n\n"
                            )
                        elif time.monotonic() - last_changed >= 3:
                            yield (
                                'event: status\ndata: {"status":"degraded",'
                                '"reason":"No new simulator frame"}\n\n'
                            )
                    except HTTPException:
                        yield (
                            'event: status\ndata: {"status":"degraded",'
                            '"reason":"Edge telemetry unavailable"}\n\n'
                        )
                    await asyncio.sleep(0.5)
            finally:
                active_streams -= 1

        return StreamingResponse(
            events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
        )

    return app
