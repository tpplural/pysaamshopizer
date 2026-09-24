"""ShippingItem DTO. Source: 04-api-contract.yaml components/schemas/ShippingItem."""
from pydantic import BaseModel

from .item_attribute import ItemAttribute


class ShippingItem(BaseModel):
    product_id: str
    quantity: int
    final_price: float | None = None
    weight: float | None = None
    height: float | None = None
    length: float | None = None
    width: float | None = None
    virtual: bool | None = None
    shippable: bool | None = None
    attributes: list[ItemAttribute] | None = None
