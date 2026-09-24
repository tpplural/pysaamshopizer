"""AdminUserListResponse DTO — source: components/schemas/AdminUserListResponse (04-api-contract.yaml)."""

from pydantic import BaseModel

from .admin_user_summary import AdminUserSummary
from .pagination_info import PaginationInfo


class AdminUserListResponse(BaseModel):
    items: list[AdminUserSummary] | None = None
    pagination: PaginationInfo | None = None
