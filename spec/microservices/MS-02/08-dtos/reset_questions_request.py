"""ResetQuestionsRequest DTO — source: components/schemas/ResetQuestionsRequest (04-api-contract.yaml)."""

from pydantic import BaseModel


class ResetQuestionsRequest(BaseModel):
    user_name: str
