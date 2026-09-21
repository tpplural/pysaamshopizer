"""Response DTO. Source schema: components/schemas.Country."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Country(BaseModel):
    iso_code: str = Field(..., description="ISO country code (BR-REF-RES-001)")
    supported: bool
    name: str | None = Field(
        default=None,
        description="Localized display name (set when requested with a language)",
    )
