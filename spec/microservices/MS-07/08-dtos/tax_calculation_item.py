"""TaxCalculationItem DTO. Source: components/schemas.TaxCalculationItem (04-api-contract.yaml)."""

from typing import Optional

from pydantic import BaseModel, Field


class TaxCalculationItem(BaseModel):
    unit_price: float
    quantity: int = Field(ge=1)
    tax_class_code: Optional[str] = None
