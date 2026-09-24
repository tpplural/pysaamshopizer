"""Model of MS-05 04-api-contract.yaml components/schemas/GroupListResponse."""

from pydantic import BaseModel


class GroupListResponse(BaseModel):
    items: list[int] | None = None
