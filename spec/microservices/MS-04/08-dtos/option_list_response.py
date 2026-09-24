"""OptionListResponse model from MS-04 04-api-contract.yaml components/schemas/OptionListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .option import Option
from .pagination_info import PaginationInfo


class OptionListResponse(BaseModel):
    items: list[Option] | None = None
    pagination: PaginationInfo | None = None
