"""MS-07 (tax) Pydantic v2 DTOs. Generated from spec/microservices/MS-07/04-api-contract.yaml."""

from .address import Address
from .create_tax_class_request import CreateTaxClassRequest
from .create_tax_rate_request import CreateTaxRateRequest
from .customer_context import CustomerContext
from .enums import TaxBasisCalculation
from .pagination_info import PaginationInfo
from .shipping_context import ShippingContext
from .store_context import StoreContext
from .tax_calculation_item import TaxCalculationItem
from .tax_calculation_request import TaxCalculationRequest
from .tax_calculation_response import TaxCalculationResponse
from .tax_class import TaxClass
from .tax_class_list_response import TaxClassListResponse
from .tax_configuration import TaxConfiguration
from .tax_line import TaxLine
from .tax_rate import TaxRate
from .tax_rate_description_item import TaxRateDescriptionItem
from .tax_rate_list_response import TaxRateListResponse
from .update_tax_class_request import UpdateTaxClassRequest
from .update_tax_rate_request import UpdateTaxRateRequest

__all__ = [
    "Address",
    "CreateTaxClassRequest",
    "CreateTaxRateRequest",
    "CustomerContext",
    "TaxBasisCalculation",
    "PaginationInfo",
    "ShippingContext",
    "StoreContext",
    "TaxCalculationItem",
    "TaxCalculationRequest",
    "TaxCalculationResponse",
    "TaxClass",
    "TaxClassListResponse",
    "TaxConfiguration",
    "TaxLine",
    "TaxRate",
    "TaxRateDescriptionItem",
    "TaxRateListResponse",
    "UpdateTaxClassRequest",
    "UpdateTaxRateRequest",
]
