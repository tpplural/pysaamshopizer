"""Local model of shared PaginationInfo. Source: spec/shared/common-schemas.yaml #/components/schemas/PaginationInfo."""
from pydantic import BaseModel


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
