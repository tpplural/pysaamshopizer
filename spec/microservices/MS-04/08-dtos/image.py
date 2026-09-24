"""Image model from MS-04 04-api-contract.yaml components/schemas/Image."""
from __future__ import annotations

from pydantic import BaseModel

from .description import Description


class Image(BaseModel):
    id: str
    file_name: str | None = None
    default_image: bool | None = None
    descriptions: list[Description] | None = None
