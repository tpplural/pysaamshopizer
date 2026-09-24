"""CreateTaxRateRequest DTO. Source: components/schemas.CreateTaxRateRequest (04-api-contract.yaml)."""

from typing import List, Optional

from pydantic import BaseModel, Field

from .tax_rate_description_item import TaxRateDescriptionItem


class CreateTaxRateRequest(BaseModel):
    code: str
    rate_text: str
    tax_class_id: str
    country_iso_code: str
    zone_id: Optional[int] = None
    state_province: Optional[str] = None
    tax_priority: Optional[int] = None
    piggyback: bool = Field(default=False)
    parent_id: Optional[str] = None
    descriptions: List[TaxRateDescriptionItem]
