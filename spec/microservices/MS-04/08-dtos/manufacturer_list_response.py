"""ManufacturerListResponse model from MS-04 04-api-contract.yaml components/schemas/ManufacturerListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .manufacturer import Manufacturer
from .pagination_info import PaginationInfo


class ManufacturerListResponse(BaseModel):
    items: list[Manufacturer] | None = None
    pagination: PaginationInfo | None = None
