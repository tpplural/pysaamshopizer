"""RelationshipGroupListResponse model from MS-04 04-api-contract.yaml components/schemas/RelationshipGroupListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .pagination_info import PaginationInfo
from .relationship_group import RelationshipGroup


class RelationshipGroupListResponse(BaseModel):
    items: list[RelationshipGroup] | None = None
    pagination: PaginationInfo | None = None
