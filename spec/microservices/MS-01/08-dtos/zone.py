"""Response DTO. Source schema: components/schemas.Zone."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Zone(BaseModel):
    code: str = Field(..., description="Globally-unique zone code (BR-REF-RES-004)")
    country_iso_code: str = Field(
        ..., description="ISO code of the country this zone belongs to (INV-REF-004)"
    )
    id: int | None = Field(
        default=None,
        description="Surrogate id (returned for the province dropdown, BR-REF-API-001)",
    )
    name: str | None = Field(default=None, description="Localized display name")
