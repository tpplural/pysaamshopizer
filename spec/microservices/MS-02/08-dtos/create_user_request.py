"""CreateUserRequest DTO — source: components/schemas/CreateUserRequest (04-api-contract.yaml)."""

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    user_name: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    password: str = Field(min_length=6)
    language_code: str | None = None
    group_ids: list[int]
    security_questions: list[int] = Field(min_length=3, max_length=3)
    security_answers: list[str] = Field(min_length=3, max_length=3)
