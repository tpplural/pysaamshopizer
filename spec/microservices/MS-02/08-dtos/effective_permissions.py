"""EffectivePermissions DTO — source: components/schemas/EffectivePermissions (04-api-contract.yaml)."""

from pydantic import BaseModel


class EffectivePermissions(BaseModel):
    user_id: int
    permissions: list[str]
