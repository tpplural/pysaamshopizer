"""Content DTO. Source: 04-api-contract.yaml #/components/schemas/Content."""
from pydantic import BaseModel, Field

from .content_description import ContentDescription
from .enums import ContentPosition, ContentType


class Content(BaseModel):
    id: str
    code: str = Field(max_length=100)
    content_type: ContentType
    position: ContentPosition | None = None
    visible: bool
    sort_order: int = 0
    descriptions: list[ContentDescription] | None = None
