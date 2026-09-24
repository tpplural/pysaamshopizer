"""ImageUploadResult model from MS-04 04-api-contract.yaml components/schemas/ImageUploadResult."""
from __future__ import annotations

from pydantic import BaseModel


class ImageUploadResult(BaseModel):
    uploaded: int | None = None
