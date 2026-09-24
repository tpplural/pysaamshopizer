"""Local model of shared common-schemas.yaml#/components/schemas/PaginationInfo (referenced by *ListResponse)."""
from __future__ import annotations

from pydantic import BaseModel


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
