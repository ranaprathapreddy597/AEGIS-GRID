import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal

import httpx
from aegis_contracts.config import Settings
from aegis_contracts.http import install_http_boundary
from aegis_contracts.models import (
    Capabilities,
    Capability,
    EdgeStatus,
    ErrorResponse,
    Health,
    PlantTelemetry,
)
from aegis_contracts.security import RequireToken
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError


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
            yield

    app = FastAPI(
        title="AEGIS GRID API",
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
                    detail="No verified provider integration or credentials",
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
                    status="not_implemented",
                    detail="Local infrastructure only; telemetry persistence is Phase 4",
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
