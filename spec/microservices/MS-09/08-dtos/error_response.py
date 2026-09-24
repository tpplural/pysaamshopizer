"""Local model of shared shape ErrorResponse (spec/shared/common-schemas.yaml#/components/schemas/ErrorResponse)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Source schema: ErrorResponse (shared common-schemas.yaml)."""

    error: str
    message: str
    status_code: int
    timestamp: datetime | None = None
