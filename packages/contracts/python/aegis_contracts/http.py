import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException
from starlette.middleware.base import RequestResponseEndpoint

from aegis_contracts.models import ErrorResponse


def install_http_boundary(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation(request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Do not reflect untrusted incoming header text into logs or responses.
        request.state.correlation_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        body = ErrorResponse(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            correlation_id=request.state.correlation_id,
        )
        return JSONResponse(body.model_dump(), status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Deliberately exclude input values (which could contain tokens).
        body = ErrorResponse(
            code="INVALID_REQUEST",
            message="Request failed schema validation",
            correlation_id=request.state.correlation_id,
        )
        return JSONResponse(body.model_dump(), status_code=422)
