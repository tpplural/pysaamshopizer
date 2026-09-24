"""SecurityQuestions DTO — source: components/schemas/SecurityQuestions (04-api-contract.yaml)."""

from pydantic import BaseModel


class SecurityQuestions(BaseModel):
    question1: str | None = None
    question2: str | None = None
    question3: str | None = None
