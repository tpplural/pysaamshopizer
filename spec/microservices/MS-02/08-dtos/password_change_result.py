"""PasswordChangeResult DTO — source: components/schemas/PasswordChangeResult (04-api-contract.yaml)."""

from pydantic import BaseModel


class PasswordChangeResult(BaseModel):
    changed: bool
