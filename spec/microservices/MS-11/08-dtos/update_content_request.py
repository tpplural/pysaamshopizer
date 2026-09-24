"""UpdateContentRequest DTO. Source: 04-api-contract.yaml #/components/schemas/UpdateContentRequest."""
from pydantic import BaseModel

from .content_description import ContentDescription
from .enums import ContentPosition


class UpdateContentRequest(BaseModel):
    position: ContentPosition | None = None
    visible: bool | None = None
    sort_order: int | None = None
    descriptions: list[ContentDescription]
