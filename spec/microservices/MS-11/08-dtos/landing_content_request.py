"""LandingContentRequest DTO. Source: 04-api-contract.yaml #/components/schemas/LandingContentRequest."""
from pydantic import BaseModel

from .content_description import ContentDescription


class LandingContentRequest(BaseModel):
    visible: bool = True
    descriptions: list[ContentDescription]
