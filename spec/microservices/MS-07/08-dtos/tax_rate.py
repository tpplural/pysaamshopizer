"""TaxRate DTO. Source: components/schemas.TaxRate (04-api-contract.yaml)."""

from typing import List, Optional

from pydantic import BaseModel, Field, condecimal


class TaxRate(BaseModel):
    id: str
    code: str
    # Percent, precision 7 scale 4 (e.g. 5.0000); NUMERIC(7,4) per 02-domain-model.md.
    rate: condecimal(max_digits=7, decimal_places=4)
    rate_display: Optional[str] = None
    tax_priority: int = Field(default=0)
    piggyback: bool = Field(default=False)
    tax_class_id: str
    parent_id: Optional[str] = None
    country_id: int
    zone_id: Optional[int] = None
    state_province: Optional[str] = None
    descriptions: Optional[List["TaxRateDescriptionItem"]] = None


from .tax_rate_description_item import TaxRateDescriptionItem  # noqa: E402

TaxRate.model_rebuild()
