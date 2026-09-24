"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerOptionListResponse."""

from pydantic import BaseModel

from .customer_option import CustomerOption
from .pagination_info import PaginationInfo


class CustomerOptionListResponse(BaseModel):
    items: list[CustomerOption] | None = None
    pagination: PaginationInfo | None = None
