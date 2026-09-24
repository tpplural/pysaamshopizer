"""TaxClass DTO. Source: components/schemas.TaxClass (04-api-contract.yaml)."""

from typing import Optional

from pydantic import BaseModel, Field


class TaxClass(BaseModel):
    id: str
    code: str = Field(max_length=10)
    title: str = Field(max_length=32)
    merchant_store_id: Optional[int] = None
