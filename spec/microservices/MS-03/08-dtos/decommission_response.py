"""DecommissionResponse DTO. Source: components/schemas/DecommissionResponse (04-api-contract.yaml)."""
from pydantic import BaseModel


class DecommissionResponse(BaseModel):
    status: str
    merchant_id: int
    event: str | None = None
