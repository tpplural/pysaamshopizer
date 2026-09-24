"""Barrel exports for MS-08 shipping DTOs. Source: 04-api-contract.yaml components/schemas."""
from .add_country_request import AddCountryRequest
from .add_region_request import AddRegionRequest
from .add_weight_bracket_request import AddWeightBracketRequest
from .custom_weight_bracket import CustomWeightBracket
from .custom_weight_configuration import CustomWeightConfiguration
from .custom_weight_region import CustomWeightRegion
from .delivery import Delivery
from .enums import (
    ShippingBasisType,
    ShippingOptionPriceType,
    ShippingPackageType,
    ShippingReturnCode,
    ShippingType,
)
from .item_attribute import ItemAttribute
from .package_detail import PackageDetail
from .packages_request import PackagesRequest
from .packages_response import PackagesResponse
from .requires_shipping_request import RequiresShippingRequest
from .requires_shipping_response import RequiresShippingResponse
from .save_shipping_mode_request import SaveShippingModeRequest
from .save_shipping_options_request import SaveShippingOptionsRequest
from .save_shipping_packaging_request import SaveShippingPackagingRequest
from .save_shipping_provider_request import SaveShippingProviderRequest
from .shipping_configuration import ShippingConfiguration
from .shipping_item import ShippingItem
from .shipping_method import ShippingMethod
from .shipping_methods_response import ShippingMethodsResponse
from .shipping_option import ShippingOption
from .shipping_provider import ShippingProvider
from .shipping_quote import ShippingQuote
from .shipping_quote_request import ShippingQuoteRequest
from .shipping_summary import ShippingSummary
from .shipping_summary_request import ShippingSummaryRequest
from .supported_countries_request import SupportedCountriesRequest
from .supported_countries_response import SupportedCountriesResponse

# Resolve nested/forward references across aggregates.
ShippingItem.model_rebuild()
ShippingQuote.model_rebuild()
ShippingQuoteRequest.model_rebuild()
ShippingSummaryRequest.model_rebuild()
PackagesRequest.model_rebuild()
PackagesResponse.model_rebuild()
RequiresShippingRequest.model_rebuild()
ShippingMethodsResponse.model_rebuild()
CustomWeightRegion.model_rebuild()
CustomWeightConfiguration.model_rebuild()

__all__ = [
    "AddCountryRequest",
    "AddRegionRequest",
    "AddWeightBracketRequest",
    "CustomWeightBracket",
    "CustomWeightConfiguration",
    "CustomWeightRegion",
    "Delivery",
    "ItemAttribute",
    "PackageDetail",
    "PackagesRequest",
    "PackagesResponse",
    "RequiresShippingRequest",
    "RequiresShippingResponse",
    "SaveShippingModeRequest",
    "SaveShippingOptionsRequest",
    "SaveShippingPackagingRequest",
    "SaveShippingProviderRequest",
    "ShippingBasisType",
    "ShippingConfiguration",
    "ShippingItem",
    "ShippingMethod",
    "ShippingMethodsResponse",
    "ShippingOption",
    "ShippingOptionPriceType",
    "ShippingPackageType",
    "ShippingProvider",
    "ShippingQuote",
    "ShippingQuoteRequest",
    "ShippingReturnCode",
    "ShippingSummary",
    "ShippingSummaryRequest",
    "ShippingType",
    "SupportedCountriesRequest",
    "SupportedCountriesResponse",
]
