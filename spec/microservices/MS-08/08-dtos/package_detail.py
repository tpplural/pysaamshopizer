"""PackageDetail DTO. Source: 04-api-contract.yaml components/schemas/PackageDetail."""
from pydantic import BaseModel


class PackageDetail(BaseModel):
    item_name: str | None = None
    shipping_weight: float | None = None
    shipping_height: float | None = None
    shipping_length: float | None = None
    shipping_width: float | None = None
    shipping_quantity: int | None = None
