"""TaxLine DTO. Source: components/schemas.TaxLine (04-api-contract.yaml)."""

from pydantic import BaseModel


class TaxLine(BaseModel):
    code: str
    label: str
    rate: float
    amount: float
