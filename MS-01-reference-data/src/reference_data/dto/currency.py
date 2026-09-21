"""Response DTO. Source schema: components/schemas.Currency."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Currency(BaseModel):
    code: str = Field(..., description="ISO-4217 currency code (BR-REF-RES-003)")
    name: str = Field(
        ...,
        description="Display name (target stores the real name; legacy stored the code — NF-2)",
    )
    supported: bool
