"""Local model of shared shape PaginationInfo (spec/shared/common-schemas.yaml#/components/schemas/PaginationInfo)."""

from __future__ import annotations

from pydantic import BaseModel


class PaginationInfo(BaseModel):
    """Source schema: PaginationInfo (shared common-schemas.yaml)."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
