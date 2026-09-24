"""UpdateUserRequest DTO — source: components/schemas/UpdateUserRequest (04-api-contract.yaml)."""

from pydantic import BaseModel


class UpdateUserRequest(BaseModel):
    user_name: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    active: bool | None = None
    language_code: str | None = None
    group_ids: list[int] | None = None
