"""Explicit simulator-only API; owner cookies never leave the approval path."""

import asyncio
import json
import secrets
from collections.abc import Callable
from typing import Annotated, Any, TypeVar
from uuid import UUID

import httpx
from aegis_agents import commissioned
from aegis_agents.service import InvestigationService
from aegis_contracts.authorization import (
    ApprovalChallenge,
    CredentialResponse,
    ExecuteRequest,
    ExecutionEnvelope,
)
from aegis_contracts.commissioned import (
    CommissionedReceipt,
    CommissionedReport,
    CommissionedStatus,
    CommissionedView,
)
from aegis_contracts.config import Settings
from aegis_contracts.security import RequireToken
from aegis_edge.commissioning import RULES_SHA256, rules
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from pymongo.errors import PyMongoError

from aegis_api.authorization import AuthorizationService
from aegis_api.commissioned_authorization import CommissionedAuthorization
from aegis_api.commissioned_gateway import CommissionedGateway
from aegis_api.gateway import SimulatorGateway

Result = TypeVar("Result")


def install_commissioned_routes(
    app: FastAPI,
    config: Settings,
    auth: Callable[[], AuthorizationService],
    gateway: Callable[[], SimulatorGateway],
    graph: Callable[[], InvestigationService],
    limit: Any,
    investigation_busy: asyncio.Lock,
) -> None:
    router = APIRouter()
    busy = asyncio.Lock()
    viewer = Depends(RequireToken(config.viewer_token.get_secret_value()))

    def service() -> CommissionedAuthorization:
        if not config.commissioned_simulator_enabled:
            raise ValueError("Commissioned simulator explicitly disabled")
        return CommissionedAuthorization(auth(), CommissionedGateway(gateway()))

    def cookie(request: Request) -> str:
        value = request.cookies.get("aegis_owner", "")
        if not value:
            raise HTTPException(401, "Commissioned owner session required")
        return value

    def origin(request: Request) -> None:
        if request.headers.get("origin") != config.approval_origin:
            raise HTTPException(403, "Canonical approval origin required")

    async def invoke(function: Callable[[], Result]) -> Result:
        try:
            return await asyncio.to_thread(function)
        except PermissionError:
            raise HTTPException(401, "Commissioned owner scope refused") from None
        except (ValueError, KeyError, TypeError, AttributeError):
            raise HTTPException(
                403, "Commissioned evidence, approval, state or safety refused"
            ) from None
        except (PyMongoError, httpx.HTTPError, OSError, RuntimeError):
            raise HTTPException(503, "Commissioned durable service unavailable") from None

    @router.get(
        "/api/v1/commissioned/status",
        response_model=CommissionedStatus,
        dependencies=[viewer, limit],
    )
    async def status() -> CommissionedStatus:
        def read() -> CommissionedStatus:
            resource = CommissionedGateway(gateway()).resource()
            state = json.loads(resource["snapshot"]["payload"])
            return CommissionedStatus(
                enabled=config.commissioned_simulator_enabled,
                incident_id=resource["incident_id"],
                rules_sha256=RULES_SHA256,
                rule_package=rules(),
                database_version=resource["version"],
                native_state_version=state["version"],
                snapshot_sha256=resource["snapshot"]["sha256"],
                temperatures_c=[c[0] for c in state["cells"]],
                receipts=[CommissionedReceipt.model_validate(r) for r in resource["receipts"]],
            )

        return await invoke(read)

    @router.post(
        "/api/v1/approval/commissioned/investigate",
        response_model=CommissionedReport,
        dependencies=[limit, Depends(origin)],
    )
    async def investigate(
        request: Request, idempotency_key: Annotated[UUID, Header()]
    ) -> CommissionedReport:
        value = cookie(request)
        if investigation_busy.locked():
            raise HTTPException(429, "Shared investigation worker busy")
        async with investigation_busy:

            def run() -> CommissionedReport:
                auth().session(value)
                if not config.commissioned_simulator_enabled:
                    raise ValueError("Commissioned simulator explicitly disabled")
                resource = CommissionedGateway(gateway()).resource()
                existing = commissioned.read(graph(), str(idempotency_key))
                if existing:
                    return existing
                if (
                    resource["receipts"]
                    or graph().client.aegis.commissioned_reports.count_documents({}) >= 8
                ):
                    raise ValueError("Commissioned one-incident investigation quota")
                return commissioned.run(graph(), resource, str(idempotency_key))

            return await invoke(run)

    @router.get(
        "/api/v1/commissioned/investigations/{identifier}",
        response_model=CommissionedReport,
        dependencies=[viewer, limit],
    )
    async def report(identifier: UUID) -> CommissionedReport:
        return await invoke(lambda: CommissionedGateway(gateway()).report(str(identifier)))

    @router.post(
        "/api/v1/approval/commissioned/investigations/{identifier}/proposal",
        response_model=CommissionedView,
        dependencies=[limit, Depends(origin)],
    )
    async def propose(request: Request, identifier: UUID) -> CommissionedView:
        value = cookie(request)
        return await invoke(lambda: service().propose(value, str(identifier)))

    @router.get(
        "/api/v1/approval/commissioned/proposals/{identifier}",
        response_model=CommissionedView,
        dependencies=[limit],
    )
    async def read_proposal(request: Request, identifier: UUID) -> CommissionedView:
        value = cookie(request)
        return await invoke(lambda: service().view(value, str(identifier)))

    @router.post(
        "/api/v1/approval/commissioned/proposals/{identifier}/options",
        response_model=ApprovalChallenge,
        dependencies=[limit, Depends(origin)],
    )
    async def options(request: Request, identifier: UUID) -> ApprovalChallenge:
        value = cookie(request)
        return await invoke(lambda: service().options(value, str(identifier)))

    @router.post(
        "/api/v1/approval/commissioned/proposals/{identifier}/verify",
        response_model=CommissionedView,
        dependencies=[limit, Depends(origin)],
    )
    async def verify(
        request: Request, identifier: UUID, body: CredentialResponse
    ) -> CommissionedView:
        value = cookie(request)
        return await invoke(lambda: service().approve(value, str(identifier), body))

    @router.post(
        "/api/v1/approval/commissioned/proposals/{identifier}/execute",
        response_model=CommissionedView,
        dependencies=[limit, Depends(origin)],
    )
    async def execute(request: Request, identifier: UUID, body: ExecuteRequest) -> CommissionedView:
        value = cookie(request)
        if busy.locked():
            raise HTTPException(429, "Commissioned executor busy")
        async with busy:
            return await invoke(lambda: service().execute(value, str(identifier), body.plan_sha256))

    @router.post("/internal/v1/commissioned/execute", response_model=CommissionedReceipt)
    async def protected(
        body: ExecutionEnvelope, authorization: Annotated[str | None, Header()] = None
    ) -> CommissionedReceipt:
        if config.gateway_token is None or not secrets.compare_digest(
            (authorization or "").encode(),
            ("Bearer " + config.gateway_token.get_secret_value()).encode(),
        ):
            raise HTTPException(401, "Independent commissioned gateway credential required")
        if not config.commissioned_simulator_enabled:
            raise HTTPException(403, "Commissioned simulator explicitly disabled")
        return await invoke(lambda: CommissionedGateway(gateway()).execute(body))

    app.include_router(router)
