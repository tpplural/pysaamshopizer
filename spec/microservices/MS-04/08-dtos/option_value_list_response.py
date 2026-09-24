"""OptionValueListResponse model from MS-04 04-api-contract.yaml components/schemas/OptionValueListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .option_value import OptionValue
from .pagination_info import PaginationInfo


class OptionValueListResponse(BaseModel):
    items: list[OptionValue] | None = None
    pagination: PaginationInfo | None = None
