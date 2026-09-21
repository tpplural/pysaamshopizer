"""Error types + FastAPI exception handlers for reference-data (MS-01).

Produces the shared ErrorResponse shape from spec/shared/common-schemas.yaml:
    { "error": <machine class>, "message": <human msg>, "status_code": <int>, "timestamp": <iso> }
with snake_case error classes per spec/shared/infrastructure-patterns.md
(422 = unprocessable_entity is the canonical validation code, 404 = not_found, 400 = bad_request).

reference-data read paths are fail-soft (BR-REF-CAC-002) and generally do NOT raise these — they
are used by the resolve-by-code endpoints (404) and query-validation (400) only.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application error carrying an HTTP status + machine error class."""

    status_code: int = 500
    error: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    error = "not_found"


class BadRequestError(AppError):
    status_code = 400
    error = "bad_request"


def _body(error: str, message: str, status_code: int, extra: dict | None = None) -> dict:
    payload = {
        "error": error,
        "message": message,
        "status_code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.error, exc.message, exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # 422 is the canonical validation code across all services (infrastructure-patterns.md).
        errors = [
            {"field": ".".join(str(p) for p in e.get("loc", [])), "message": e.get("msg", "")}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body(
                "unprocessable_entity",
                "Request validation failed",
                422,
                {"errors": errors},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        mapping = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found"}
        error_class = mapping.get(exc.status_code, "error")
        # 204 and other empty responses are handled by the routes directly; only surface a body
        # for real error statuses.
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(error_class, str(exc.detail), exc.status_code),
        )

    @app.exception_handler(Exception)
    async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = request.headers.get("x-correlation-id")
        payload = {"error": "internal_error", "status_code": 500}
        if correlation_id:
            payload["correlation_id"] = correlation_id
        return JSONResponse(status_code=500, content=payload)
