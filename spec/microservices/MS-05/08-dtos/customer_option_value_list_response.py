"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerOptionValueListResponse."""

from pydantic import BaseModel

from .customer_option_value import CustomerOptionValue
from .pagination_info import PaginationInfo


class CustomerOptionValueListResponse(BaseModel):
    items: list[CustomerOptionValue] | None = None
    pagination: PaginationInfo | None = None
