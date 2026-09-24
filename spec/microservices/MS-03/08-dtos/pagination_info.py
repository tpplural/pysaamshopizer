"""PaginationInfo DTO. Source: components/schemas/PaginationInfo (shared/common-schemas.yaml)."""
from pydantic import BaseModel


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
