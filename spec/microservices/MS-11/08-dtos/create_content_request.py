"""CreateContentRequest DTO. Source: 04-api-contract.yaml #/components/schemas/CreateContentRequest."""
from pydantic import BaseModel, Field

from .content_description import ContentDescription
from .enums import ContentPosition, ContentType


class CreateContentRequest(BaseModel):
    code: str = Field(max_length=100)
    content_type: ContentType | None = None
    position: ContentPosition | None = None
    visible: bool = False
    sort_order: int = 0
    descriptions: list[ContentDescription]
