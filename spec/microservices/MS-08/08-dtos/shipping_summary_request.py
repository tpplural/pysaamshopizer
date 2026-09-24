"""ShippingSummaryRequest DTO. Source: 04-api-contract.yaml components/schemas/ShippingSummaryRequest."""
from pydantic import BaseModel

from .shipping_option import ShippingOption
from .shipping_quote import ShippingQuote


class ShippingSummaryRequest(BaseModel):
    quote: ShippingQuote
    selected_option: ShippingOption
