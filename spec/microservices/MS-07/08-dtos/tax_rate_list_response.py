"""TaxRateListResponse DTO. Source: components/schemas.TaxRateListResponse (04-api-contract.yaml)."""

from typing import List, Optional

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .tax_rate import TaxRate


class TaxRateListResponse(BaseModel):
    items: Optional[List[TaxRate]] = None
    pagination: Optional[PaginationInfo] = None
