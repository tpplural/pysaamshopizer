"""Group DTO — source: components/schemas/Group (04-api-contract.yaml)."""

from pydantic import BaseModel

from .enums import GroupType


class Group(BaseModel):
    id: int
    group_name: str
    group_type: GroupType
    description: str | None = None
