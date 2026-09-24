"""Attribute model from MS-04 04-api-contract.yaml components/schemas/Attribute."""
from __future__ import annotations

from pydantic import BaseModel


class Attribute(BaseModel):
    id: str
    option_id: str | None = None
    option_value_id: str | None = None
    price: float | None = None
    additional_weight: float | None = None
    sort_order: int | None = None
    default: bool | None = None
    required: bool | None = None
    display_only: bool | None = None
    discounted: bool | None = None
    free: bool | None = None
