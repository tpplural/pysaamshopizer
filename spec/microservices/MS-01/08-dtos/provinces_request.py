"""Request DTO. Source schema: components/schemas.ProvincesRequest."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProvincesRequest(BaseModel):
    country_code: str = Field(
        ..., description="ISO code of the country whose provinces/zones are requested"
    )
    lang: str | None = Field(
        default=None,
        description="Optional language code; falls back to ambient then English (BR-REF-LNG-003)",
    )
