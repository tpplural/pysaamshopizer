"""UpdateStoreRequest DTO. Source: components/schemas/UpdateStoreRequest (04-api-contract.yaml)."""
from datetime import date

from pydantic import BaseModel, EmailStr, Field

from .enums import DimensionUnit, WeightUnit


class UpdateStoreRequest(BaseModel):
    name: str = Field(max_length=100)
    phone: str = Field(max_length=50)
    email: EmailStr = Field(max_length=60)
    address: str | None = Field(default=None, max_length=255)
    city: str = Field(max_length=100)
    postal_code: str = Field(max_length=15)
    country_iso: str
    zone_code: str | None = None
    state_province: str | None = Field(default=None, max_length=100)
    default_language_code: str
    currency_code: str
    language_codes: list[str] = Field(min_length=1)
    weight_unit: WeightUnit | None = None
    dimension_unit: DimensionUnit | None = None
    in_business_since: date | None = None
    use_cache: bool | None = None
    currency_format_national: bool | None = None
    domain_name: str | None = Field(default=None, max_length=80)
    continue_shopping_url: str | None = Field(default=None, max_length=150)
