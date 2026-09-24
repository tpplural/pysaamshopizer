"""ContentListResponse DTO. Source: 04-api-contract.yaml #/components/schemas/ContentListResponse."""
from pydantic import BaseModel

from .content import Content
from .pagination_info import PaginationInfo


class ContentListResponse(BaseModel):
    items: list[Content] | None = None
    pagination: PaginationInfo | None = None
