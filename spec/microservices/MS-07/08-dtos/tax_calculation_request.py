"""TaxCalculationRequest DTO. Source: components/schemas.TaxCalculationRequest (04-api-contract.yaml)."""

from typing import List, Optional

from pydantic import BaseModel

from .customer_context import CustomerContext
from .enums import TaxBasisCalculation
from .shipping_context import ShippingContext
from .store_context import StoreContext
from .tax_calculation_item import TaxCalculationItem


class TaxCalculationRequest(BaseModel):
    customer: Optional[CustomerContext] = None
    store: Optional[StoreContext] = None
    items: List[TaxCalculationItem]
    shipping: Optional[ShippingContext] = None
    language_id: Optional[int] = None
    tax_basis: Optional[TaxBasisCalculation] = None
