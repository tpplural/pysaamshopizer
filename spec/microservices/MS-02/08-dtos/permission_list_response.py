"""PermissionListResponse DTO — source: components/schemas/PermissionListResponse (04-api-contract.yaml)."""

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .permission import Permission


class PermissionListResponse(BaseModel):
    items: list[Permission] | None = None
    pagination: PaginationInfo | None = None
