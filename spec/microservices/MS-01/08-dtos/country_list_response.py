"""Response DTO. Source schema: components/schemas.CountryListResponse."""

from __future__ import annotations

from pydantic import BaseModel

from .country import Country


class CountryListResponse(BaseModel):
    items: list[Country]
