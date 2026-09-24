"""AdminUser DTO — source: components/schemas/AdminUser (04-api-contract.yaml)."""

from pydantic import BaseModel

from .group import Group


class AdminUser(BaseModel):
    id: int
    user_name: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    merchant_id: int | None = None
    store_code: str | None = None
    language_code: str | None = None
    active: bool
    last_access: str | None = None
    login_time: str | None = None
    groups: list[Group] | None = None
