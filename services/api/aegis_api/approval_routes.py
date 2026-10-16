"""Origin-bound owner-only HTTP surface. No browser receives raw capabilities."""

import asyncio
import secrets
from collections.abc import Callable
from typing import Annotated, Any, TypeVar
from uuid import UUID

import httpx
from aegis_contracts.authorization import (
    ApprovalChallenge,
    ApprovalSession,
    ApprovalView,
    CredentialResponse,
    ExecuteRequest,
    ExecutionEnvelope,
    MutationReceipt,
)
from aegis_contracts.config import Settings
from aegis_contracts.models import ErrorResponse
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response
from pymongo.errors import PyMongoError

from aegis_api.authorization import AuthorizationService
from aegis_api.gateway import SimulatorGateway

Result = TypeVar("Result")


def install_approval_routes(
    app: FastAPI,
    config: Settings,
    service: Callable[[], AuthorizationService],
    gateway: Callable[[], SimulatorGateway],
    limit: Any,
) -> None:
    busy = asyncio.Lock()
    router = APIRouter(responses={code: {"model": ErrorResponse} for code in (401, 403, 429, 503)})

    def origin(request: Request) -> None:
        if request.headers.get("origin") != config.approval_origin:
            raise HTTPException(403, "Canonical local approval origin required")

    def cookie(request: Request) -> str:
        value = request.cookies.get("aegis_owner", "")
        if not value:
            raise HTTPException(401, "Owner session required")
        return value

    async def invoke(function: Callable[[], Result]) -> Result:
        try:
            return await asyncio.to_thread(function)
        except PermissionError:
            raise HTTPException(401, "Owner session or proposal scope refused") from None
        except (ValueError, KeyError, TypeError, AttributeError):
            raise HTTPException(403, "Approval proof, state or safety policy refused") from None
        except (PyMongoError, httpx.HTTPError, OSError, RuntimeError):
            raise HTTPException(
                503, "Durable authorization or independent gateway unavailable"
            ) from None

    @router.post(
        "/api/v1/approval/session",
        response_model=ApprovalSession,
        dependencies=[limit, Depends(origin)],
    )
    async def login(
        response: Response, authorization: Annotated[str | None, Header()] = None
    ) -> ApprovalSession:
        if config.approver_token is None:
            raise HTTPException(503, "Owner authentication not configured")
        if not secrets.compare_digest(
            (authorization or "").encode(),
            ("Bearer " + config.approver_token.get_secret_value()).encode(),
        ):
            raise HTTPException(401, "Owner bootstrap authentication required")
        value, session = await invoke(lambda: service().login())
        # Loopback HTTP development only; no production/TLS session claim.
        response.set_cookie(
            "aegis_owner",
            value,
            httponly=True,
            samesite="strict",
            secure=False,
            max_age=900,
            path="/api/v1/approval",
        )
        return session

    @router.get("/api/v1/approval/session", response_model=ApprovalSession, dependencies=[limit])
    async def session(request: Request) -> ApprovalSession:
        value = cookie(request)
        return await invoke(lambda: service().session_view(value))

    @router.delete(
        "/api/v1/approval/session", status_code=204, dependencies=[limit, Depends(origin)]
    )
    async def logout(request: Request, response: Response) -> None:
        value = cookie(request)
        await invoke(
            lambda: service().client.aegis.auth_sessions.delete_one(
                {"_id": service().session_id(value)}
            )
        )
        response.delete_cookie(
            "aegis_owner", path="/api/v1/approval", httponly=True, samesite="strict"
        )

    @router.post(
        "/api/v1/approval/registration/options",
        response_model=ApprovalChallenge,
        dependencies=[limit, Depends(origin)],
    )
    async def registration_options(request: Request) -> ApprovalChallenge:
        value = cookie(request)
        return await invoke(lambda: service().registration_options(value))

    @router.post(
        "/api/v1/approval/registration/verify",
        response_model=ApprovalSession,
        dependencies=[limit, Depends(origin)],
    )
    async def registration_verify(request: Request, body: CredentialResponse) -> ApprovalSession:
        value = cookie(request)
        return await invoke(lambda: service().register(value, body))

    @router.post(
        "/api/v1/approval/proposals",
        response_model=ApprovalView,
        dependencies=[limit, Depends(origin)],
    )
    async def propose(request: Request) -> ApprovalView:
        value = cookie(request)
        return await invoke(lambda: service().propose(value))

    @router.get(
        "/api/v1/approval/proposals/{action_id}", response_model=ApprovalView, dependencies=[limit]
    )
    async def read_proposal(request: Request, action_id: UUID) -> ApprovalView:
        value = cookie(request)
        return await invoke(lambda: service().view(value, str(action_id)))

    @router.post(
        "/api/v1/approval/maintenance-proposals",
        response_model=ApprovalView,
        dependencies=[limit, Depends(origin)],
    )
    async def propose_maintenance(request: Request) -> ApprovalView:
        value = cookie(request)
        return await invoke(lambda: service().propose(value, record_maintenance=True))

    @router.post(
        "/api/v1/approval/proposals/{action_id}/options",
        response_model=ApprovalChallenge,
        dependencies=[limit, Depends(origin)],
    )
    async def approval_options(request: Request, action_id: UUID) -> ApprovalChallenge:
        value = cookie(request)
        return await invoke(lambda: service().authentication_options(value, str(action_id)))

    @router.post(
        "/api/v1/approval/proposals/{action_id}/verify",
        response_model=ApprovalView,
        dependencies=[limit, Depends(origin)],
    )
    async def approval_verify(
        request: Request, action_id: UUID, body: CredentialResponse
    ) -> ApprovalView:
        value = cookie(request)
        return await invoke(lambda: service().approve(value, str(action_id), body))

    @router.post(
        "/api/v1/approval/proposals/{action_id}/execute",
        response_model=ApprovalView,
        dependencies=[limit, Depends(origin)],
    )
    async def execute(request: Request, action_id: UUID, body: ExecuteRequest) -> ApprovalView:
        value = cookie(request)
        if busy.locked():
            raise HTTPException(429, "Authorization worker busy")
        async with busy:
            return await invoke(lambda: service().execute(value, str(action_id), body.plan_sha256))

    @router.post("/internal/v1/sandbox/execute", response_model=MutationReceipt)
    async def protected_gateway(
        body: ExecutionEnvelope, authorization: Annotated[str | None, Header()] = None
    ) -> MutationReceipt:
        if config.gateway_token is None or not secrets.compare_digest(
            (authorization or "").encode(),
            ("Bearer " + config.gateway_token.get_secret_value()).encode(),
        ):
            raise HTTPException(401, "Independent gateway credential required")
        return await invoke(lambda: gateway().execute(body))

    app.include_router(router)
