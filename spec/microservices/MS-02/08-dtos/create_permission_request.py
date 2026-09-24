"""CreatePermissionRequest DTO — source: components/schemas/CreatePermissionRequest (04-api-contract.yaml)."""

from pydantic import BaseModel


class CreatePermissionRequest(BaseModel):
    permission_name: str
