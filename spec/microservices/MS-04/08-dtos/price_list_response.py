"""PriceListResponse model from MS-04 04-api-contract.yaml components/schemas/PriceListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .price import Price


class PriceListResponse(BaseModel):
    items: list[Price] | None = None
    pagination: PaginationInfo | None = None
