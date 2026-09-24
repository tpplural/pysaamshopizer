"""AttributeListResponse model from MS-04 04-api-contract.yaml components/schemas/AttributeListResponse (inline items object modeled as AttributeListItem)."""
from __future__ import annotations

from pydantic import BaseModel

from .pagination_info import PaginationInfo


class AttributeListItem(BaseModel):
    attribute_id: str | None = None
    attribute: str | None = None
    value: str | None = None
    display: bool | None = None
    order: int | None = None
    price: str | None = None


class AttributeListResponse(BaseModel):
    items: list[AttributeListItem] | None = None
    pagination: PaginationInfo | None = None
