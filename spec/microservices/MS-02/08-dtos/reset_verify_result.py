"""ResetVerifyResult DTO — source: components/schemas/ResetVerifyResult (04-api-contract.yaml)."""

from pydantic import BaseModel


class ResetVerifyResult(BaseModel):
    verified: bool
