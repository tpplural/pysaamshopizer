"""ChangePasswordRequest DTO — source: components/schemas/ChangePasswordRequest (04-api-contract.yaml)."""

from pydantic import BaseModel, Field


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
    repeat_password: str
