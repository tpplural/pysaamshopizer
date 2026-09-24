"""StoreListResponse DTO. Source: components/schemas/StoreListResponse (04-api-contract.yaml)."""
from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .store import Store


class StoreListResponse(BaseModel):
    items: list[Store] | None = None
    pagination: PaginationInfo | None = None
