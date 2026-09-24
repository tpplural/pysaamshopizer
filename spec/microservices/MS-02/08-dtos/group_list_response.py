"""GroupListResponse DTO — source: components/schemas/GroupListResponse (04-api-contract.yaml)."""

from pydantic import BaseModel

from .group import Group
from .pagination_info import PaginationInfo


class GroupListResponse(BaseModel):
    items: list[Group] | None = None
    pagination: PaginationInfo | None = None
