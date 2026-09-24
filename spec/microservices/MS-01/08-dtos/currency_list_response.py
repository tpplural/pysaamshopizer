"""Response DTO. Source schema: components/schemas.CurrencyListResponse."""

from __future__ import annotations

from pydantic import BaseModel

from .currency import Currency


class CurrencyListResponse(BaseModel):
    items: list[Currency]
