"""TaxCalculationResponse DTO. Source: components/schemas.TaxCalculationResponse (04-api-contract.yaml)."""

from typing import List, Optional

from pydantic import BaseModel

from .tax_line import TaxLine


class TaxCalculationResponse(BaseModel):
    """The tax lines, or null when no tax applies (BR-TAX-024)."""

    tax_lines: Optional[List[TaxLine]] = None
