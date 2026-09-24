"""LogoUploadRequest DTO. Source: components/schemas/LogoUploadRequest (04-api-contract.yaml)."""
from pydantic import BaseModel


class LogoUploadRequest(BaseModel):
    file: bytes
