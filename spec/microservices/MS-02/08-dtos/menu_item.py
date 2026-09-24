"""MenuItem DTO (self-referential) — source: components/schemas/MenuItem (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class MenuItem(BaseModel):
    code: str
    role: str
    url: str | None = None
    icon: str | None = None
    order: int | None = None
    menus: list[MenuItem] | None = None


MenuItem.model_rebuild()
