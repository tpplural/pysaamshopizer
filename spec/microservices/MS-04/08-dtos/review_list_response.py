"""ReviewListResponse model from MS-04 04-api-contract.yaml components/schemas/ReviewListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .review import Review


class ReviewListResponse(BaseModel):
    items: list[Review] | None = None
    pagination: PaginationInfo | None = None
