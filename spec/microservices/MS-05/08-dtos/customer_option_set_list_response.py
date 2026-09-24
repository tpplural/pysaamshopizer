"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerOptionSetListResponse."""

from pydantic import BaseModel

from .customer_option_set import CustomerOptionSet
from .pagination_info import PaginationInfo


class CustomerOptionSetListResponse(BaseModel):
    items: list[CustomerOptionSet] | None = None
    pagination: PaginationInfo | None = None
