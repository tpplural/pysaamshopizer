"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerListResponse."""

from pydantic import BaseModel

from .customer import Customer
from .pagination_info import PaginationInfo


class CustomerListResponse(BaseModel):
    items: list[Customer] | None = None
    pagination: PaginationInfo | None = None
