"""ResetCompleteResult DTO — source: components/schemas/ResetCompleteResult (04-api-contract.yaml)."""

from pydantic import BaseModel


class ResetCompleteResult(BaseModel):
    reset: bool
    temporary_password_emailed: bool | None = None
