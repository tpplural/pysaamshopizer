"""Model of MS-05 04-api-contract.yaml components/schemas/StatusResponse."""

from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: str | None = None
