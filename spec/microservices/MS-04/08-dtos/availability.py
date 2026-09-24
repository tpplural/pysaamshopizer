"""Availability model from MS-04 04-api-contract.yaml components/schemas/Availability."""
from __future__ import annotations

from pydantic import BaseModel


class Availability(BaseModel):
    id: str | None = None
    region: str | None = None
    active: bool | None = None
    quantity: int | None = None
    order_min: int | None = None
    order_max: int | None = None
