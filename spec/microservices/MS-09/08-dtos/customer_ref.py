"""Pydantic v2 model for CustomerRef. Source schema: CustomerRef (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class CustomerRef(BaseModel):
    """Source schema: CustomerRef (04-api-contract.yaml)."""

    customer_id: str | None = None
    zone: str | None = None
    country: str | None = None
    state_province: str | None = None
