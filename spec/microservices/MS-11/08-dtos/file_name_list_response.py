"""FileNameListResponse DTO. Source: 04-api-contract.yaml #/components/schemas/FileNameListResponse."""
from pydantic import BaseModel

from .enums import FileContentType


class FileNameListResponse(BaseModel):
    items: list[str] | None = None
    file_type: FileContentType | None = None
