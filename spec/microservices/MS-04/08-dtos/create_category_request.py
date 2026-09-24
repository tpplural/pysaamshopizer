"""CreateCategoryRequest model from MS-04 04-api-contract.yaml components/schemas/CreateCategoryRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .description_request import DescriptionRequest


class CreateCategoryRequest(BaseModel):
    code: str
    parent_id: int | None = None
    sort_order: int | None = 0
    visible: bool | None = True
    descriptions: list[DescriptionRequest] | None = None
