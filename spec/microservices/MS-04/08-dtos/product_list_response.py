"""ProductListResponse model from MS-04 04-api-contract.yaml components/schemas/ProductListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .product import Product


class ProductListResponse(BaseModel):
    items: list[Product] | None = None
    pagination: PaginationInfo | None = None
