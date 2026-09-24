"""DTO for ErrorResponse (source: shared/common-schemas.yaml#/components/schemas/ErrorResponse; used by MS-06 502 BadGateway)."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    timestamp: str | None = None
