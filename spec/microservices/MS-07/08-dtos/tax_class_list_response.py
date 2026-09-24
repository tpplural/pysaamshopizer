"""TaxClassListResponse DTO. Source: components/schemas.TaxClassListResponse (04-api-contract.yaml)."""

from typing import List, Optional

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .tax_class import TaxClass


class TaxClassListResponse(BaseModel):
    items: Optional[List[TaxClass]] = None
    pagination: Optional[PaginationInfo] = None
