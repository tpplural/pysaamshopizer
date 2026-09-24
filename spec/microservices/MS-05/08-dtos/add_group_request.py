"""Model of MS-05 04-api-contract.yaml components/schemas/AddGroupRequest."""

from pydantic import BaseModel


class AddGroupRequest(BaseModel):
    group_id: int
