"""CreateGroupRequest DTO — source: components/schemas/CreateGroupRequest (04-api-contract.yaml)."""

from pydantic import BaseModel

from .enums import GroupType


class CreateGroupRequest(BaseModel):
    group_name: str
    group_type: GroupType
