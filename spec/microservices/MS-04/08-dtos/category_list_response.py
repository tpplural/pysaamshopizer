"""CategoryListResponse model from MS-04 04-api-contract.yaml components/schemas/CategoryListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .category import Category
from .pagination_info import PaginationInfo


class CategoryListResponse(BaseModel):
    items: list[Category] | None = None
    pagination: PaginationInfo | None = None
