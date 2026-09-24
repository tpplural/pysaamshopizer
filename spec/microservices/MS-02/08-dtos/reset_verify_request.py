"""ResetVerifyRequest DTO — source: components/schemas/ResetVerifyRequest (04-api-contract.yaml)."""

from pydantic import BaseModel, Field


class ResetVerifyRequest(BaseModel):
    answers: list[str] = Field(min_length=3, max_length=3)
