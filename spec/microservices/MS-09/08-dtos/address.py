"""Pydantic v2 model for Address. Source schema: Address (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class Address(BaseModel):
    """Source schema: Address (04-api-contract.yaml)."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    zone: str | None = None
    state_province: str | None = None
    phone: str | None = None
    postal_code: str | None = None
