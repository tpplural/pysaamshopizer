"""AttachDigitalFileRequest model from MS-04 04-api-contract.yaml components/schemas/AttachDigitalFileRequest."""
from __future__ import annotations

from pydantic import BaseModel


class AttachDigitalFileRequest(BaseModel):
    file_name: str
    content: str
