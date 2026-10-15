import asyncio
import hashlib
import logging
import sys
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime

from aegis_contracts.config import Settings
from aegis_contracts.http import install_http_boundary
from aegis_contracts.models import (
    EdgeIncident,
    EdgeStatus,
    ErrorResponse,
    Health,
    PlantTelemetry,
    SupervisorFrame,
)
from aegis_contracts.security import RequireToken
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from aegis_edge.cloud import CloudOutbox
from aegis_edge.twin import fingerprint, scenario_from_file

logger = logging.getLogger("aegis.edge")


class TwinReader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.latest: PlantTelemetry | None = None
        self.last_received = 0.0
        self.running = False
        self.process: asyncio.subprocess.Process | None = None
        self.outbox = CloudOutbox(
            settings.cloud_events_url,
            settings.cloud_token.get_secret_value() if settings.cloud_token else None,
        )

    @property
    def ready(self) -> bool:
        return (
            self.running and self.latest is not None and time.monotonic() - self.last_received < 3
        )

    async def run(self) -> None:
        library = self.settings.twin_library.resolve(strict=True)
        digest = hashlib.sha256(library.read_bytes()).hexdigest()
        run_id = str(uuid.uuid4())
        scenario = scenario_from_file(
            self.settings.scenario_dir, self.settings.scenario_id, self.settings.seed
        )
        options = [
            sys.executable,
            "-m",
            "aegis_edge.runner",
            "--scenario",
            scenario.model_dump_json(),
            "--library",
            str(library),
            "--speed",
            str(self.settings.time_scale),
            "--memory-capacity",
            str(self.settings.memory_capacity),
        ]
        if self.settings.safety_mode == "observe_only":
            options.append("--observe-only")
        self.process = await asyncio.create_subprocess_exec(
            *options,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=16384,
        )
        self.running = True
        try:
            if self.process.stdout is None:
                raise RuntimeError("Missing simulator stdout")
            previous_version = 0
            previous_dropped = 0
            reported = False
            while True:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=10 if previous_version == 0 else 3
                )
                if not line:
                    break
                envelope = SupervisorFrame.model_validate_json(line)
                raw = envelope.frame
                gap = raw.state_version - previous_version - 1
                if (
                    gap < 0
                    or gap != raw.measurement.dropped_packets - previous_dropped
                    or not raw.measurement.packet_available
                    or raw.seed != self.settings.seed
                    or raw.scenario_id != scenario.scenario_id
                ):
                    raise ValueError("Out-of-order or wrong-scenario simulator frame")
                previous_version = raw.state_version
                previous_dropped = raw.measurement.dropped_packets
                self.latest = PlantTelemetry(
                    **raw.model_dump(),
                    run_id=run_id,
                    simulator_sha256=digest,
                    scenario_sha256=fingerprint(scenario),
                    observed_at=datetime.now(UTC).isoformat(),
                    sentinel=envelope.sentinel,
                )
                if envelope.sentinel.latched and not reported:
                    kinds = ["anomaly"]
                    if envelope.sentinel.applied_policy == "local_emergency_stop":
                        kinds.append("local_stop")
                    for kind in kinds:
                        event_id = hashlib.sha256(
                            f"{run_id}:{raw.state_version}:{kind}".encode()
                        ).hexdigest()
                        self.outbox.enqueue(
                            EdgeIncident.model_validate(
                                {
                                    "event_id": event_id,
                                    "run_id": run_id,
                                    "state_version": raw.state_version,
                                    "simulation_time_s": raw.simulation_time_s,
                                    "kind": kind,
                                    "evidence": envelope.sentinel.evidence,
                                }
                            )
                        )
                    reported = True
                self.last_received = time.monotonic()
        except (TimeoutError, ValueError, ValidationError):
            logger.error("Simulator frame rejected or stalled; telemetry unavailable")
        finally:
            self.running = False
            if self.process.returncode is None:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2)
                except TimeoutError:
                    self.process.kill()
                    await self.process.wait()


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    reader = TwinReader(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(reader.run())
        cloud_task = asyncio.create_task(reader.outbox.run())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            cloud_task.cancel()
            with suppress(asyncio.CancelledError):
                await cloud_task

    app = FastAPI(
        title="AEGIS Edge",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_http_boundary(app)
    app.state.reader = reader
    auth = Depends(RequireToken(config.service_token.get_secret_value()))

    @app.get("/v1/edge/status", response_model=EdgeStatus, dependencies=[auth])
    async def edge_status() -> EdgeStatus:
        return reader.outbox.status()

    @app.get("/healthz", response_model=Health)
    async def health() -> JSONResponse:
        body = Health(
            status="ok" if reader.ready else "degraded",
            service="edge",
            detail="Simulator frames arriving" if reader.ready else "Simulator unavailable",
        )
        return JSONResponse(body.model_dump(), status_code=200 if reader.ready else 503)

    @app.get(
        "/v1/telemetry/latest",
        response_model=PlantTelemetry,
        dependencies=[auth],
        responses={401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    async def latest() -> PlantTelemetry:
        if not reader.ready or reader.latest is None:
            raise HTTPException(503, "Simulator unavailable; no current telemetry")
        return reader.latest

    return app
