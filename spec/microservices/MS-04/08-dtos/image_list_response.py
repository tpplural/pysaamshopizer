"""ImageListResponse model from MS-04 04-api-contract.yaml components/schemas/ImageListResponse."""
from __future__ import annotations

from pydantic import BaseModel

from .image_ref import ImageRef
from .pagination_info import PaginationInfo


class ImageListResponse(BaseModel):
    items: list[ImageRef] | None = None
    pagination: PaginationInfo | None = None
