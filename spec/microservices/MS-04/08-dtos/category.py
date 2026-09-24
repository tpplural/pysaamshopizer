"""Category model from MS-04 04-api-contract.yaml components/schemas/Category."""
from __future__ import annotations

from pydantic import BaseModel

from .description import Description


class Category(BaseModel):
    id: str
    code: str
    parent_id: str | None = None
    depth: int | None = None
    lineage: str | None = None
    sort_order: int | None = None
    visible: bool | None = None
    descendants_updated: int | None = None
    descriptions: list[Description] | None = None
