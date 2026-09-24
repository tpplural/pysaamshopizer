"""TaxConfiguration DTO. Source: components/schemas.TaxConfiguration (04-api-contract.yaml)."""

from pydantic import BaseModel, Field

from .enums import TaxBasisCalculation


class TaxConfiguration(BaseModel):
    tax_basis_calculation: TaxBasisCalculation
    collect_tax_if_different_province_of_store_country: bool = Field(default=True)
    collect_tax_if_different_country_of_store_country: bool = Field(default=False)
