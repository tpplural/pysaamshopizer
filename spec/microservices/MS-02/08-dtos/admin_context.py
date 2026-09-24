"""AdminContext DTO — source: components/schemas/AdminContext (04-api-contract.yaml)."""

from pydantic import BaseModel


class AdminContext(BaseModel):
    user_name: str | None = None
    active_store: str | None = None
    cached: bool | None = None
