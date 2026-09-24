"""Relationship model from MS-04 04-api-contract.yaml components/schemas/Relationship."""
from __future__ import annotations

from pydantic import BaseModel


class Relationship(BaseModel):
    id: str | None = None
    group_code: str | None = None
    related_product_id: str | None = None
    active: bool | None = None
