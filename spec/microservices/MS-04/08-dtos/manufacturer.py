"""Manufacturer model from MS-04 04-api-contract.yaml components/schemas/Manufacturer."""
from __future__ import annotations

from pydantic import BaseModel

from .description import Description


class Manufacturer(BaseModel):
    id: str
    code: str
    sort_order: int | None = None
    descriptions: list[Description] | None = None
