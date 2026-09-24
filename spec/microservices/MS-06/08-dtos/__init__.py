"""Barrel export of MS-06 (cart) Pydantic v2 DTOs (source: MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from .add_cart_item_attribute import AddCartItemAttribute
from .add_cart_item_request import AddCartItemRequest
from .cart import Cart
from .cart_item import CartItem
from .cart_item_attribute import CartItemAttribute
from .cart_shipping_eligibility import CartShippingEligibility
from .cart_summary import CartSummary
from .create_cart_request import CreateCartRequest
from .error_response import ErrorResponse
from .merge_carts_request import MergeCartsRequest
from .order_total_line import OrderTotalLine
from .shippable_item import ShippableItem
from .update_cart_item_request import UpdateCartItemRequest
from .update_cart_items_line import UpdateCartItemsLine
from .update_cart_items_request import UpdateCartItemsRequest

# Resolve forward references in models that nest other DTOs.
Cart.model_rebuild()
CartItem.model_rebuild()
CartShippingEligibility.model_rebuild()
CartSummary.model_rebuild()
AddCartItemRequest.model_rebuild()
UpdateCartItemsRequest.model_rebuild()

__all__ = [
    "AddCartItemAttribute",
    "AddCartItemRequest",
    "Cart",
    "CartItem",
    "CartItemAttribute",
    "CartShippingEligibility",
    "CartSummary",
    "CreateCartRequest",
    "ErrorResponse",
    "MergeCartsRequest",
    "OrderTotalLine",
    "ShippableItem",
    "UpdateCartItemRequest",
    "UpdateCartItemsLine",
    "UpdateCartItemsRequest",
]
