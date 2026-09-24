"""Permission DTO — source: components/schemas/Permission (04-api-contract.yaml)."""

from pydantic import BaseModel


class Permission(BaseModel):
    id: int
    permission_name: str
