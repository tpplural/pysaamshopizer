"""AdminUserSummary DTO — source: components/schemas/AdminUserSummary (04-api-contract.yaml)."""

from pydantic import BaseModel


class AdminUserSummary(BaseModel):
    user_id: int
    name: str
    email: str | None = None
    active: bool | None = None
    store_code: str | None = None
