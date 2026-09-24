"""UpdateImageRequest model from MS-04 04-api-contract.yaml components/schemas/UpdateImageRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .description_request import DescriptionRequest


class UpdateImageRequest(BaseModel):
    default_image: bool | None = None
    descriptions: list[DescriptionRequest] | None = None
