"""MenuListResponse DTO — source: components/schemas/MenuListResponse (04-api-contract.yaml)."""

from pydantic import BaseModel

from .menu_item import MenuItem


class MenuListResponse(BaseModel):
    items: list[MenuItem] | None = None
