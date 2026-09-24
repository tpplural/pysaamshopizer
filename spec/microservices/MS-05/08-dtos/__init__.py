"""Barrel exports for MS-05 (customer) DTOs — generated from 04-api-contract.yaml."""

from .add_group_request import AddGroupRequest
from .address import Address
from .available_option import AvailableOption
from .available_option_list_response import AvailableOptionListResponse
from .change_password_request import ChangePasswordRequest
from .create_customer_option_request import CreateCustomerOptionRequest
from .create_customer_option_set_request import CreateCustomerOptionSetRequest
from .create_customer_option_value_request import CreateCustomerOptionValueRequest
from .create_customer_request import CreateCustomerRequest
from .customer import Customer
from .customer_attribute import CustomerAttribute
from .customer_attribute_list_response import CustomerAttributeListResponse
from .customer_list_response import CustomerListResponse
from .customer_option import CustomerOption
from .customer_option_list_response import CustomerOptionListResponse
from .customer_option_set import CustomerOptionSet
from .customer_option_set_list_response import CustomerOptionSetListResponse
from .customer_option_value import CustomerOptionValue
from .customer_option_value_list_response import CustomerOptionValueListResponse
from .enums import Gender, OptionType
from .group_list_response import GroupListResponse
from .login_request import LoginRequest
from .login_response import LoginResponse
from .option_description import OptionDescription
from .pagination_info import PaginationInfo
from .register_customer_request import RegisterCustomerRequest
from .replace_attributes_request import ReplaceAttributesRequest
from .status_response import StatusResponse
from .update_customer_request import UpdateCustomerRequest

# Resolve nested model references.
Address.model_rebuild()
Customer.model_rebuild()
CreateCustomerRequest.model_rebuild()
UpdateCustomerRequest.model_rebuild()
RegisterCustomerRequest.model_rebuild()
CustomerAttribute.model_rebuild()
CustomerAttributeListResponse.model_rebuild()
ReplaceAttributesRequest.model_rebuild()
AvailableOption.model_rebuild()
AvailableOptionListResponse.model_rebuild()
OptionDescription.model_rebuild()
CustomerOption.model_rebuild()
CreateCustomerOptionRequest.model_rebuild()
CustomerOptionValue.model_rebuild()
CreateCustomerOptionValueRequest.model_rebuild()
CustomerOptionSet.model_rebuild()
CreateCustomerOptionSetRequest.model_rebuild()
CustomerListResponse.model_rebuild()
CustomerOptionListResponse.model_rebuild()
CustomerOptionValueListResponse.model_rebuild()
CustomerOptionSetListResponse.model_rebuild()

__all__ = [
    "AddGroupRequest",
    "Address",
    "AvailableOption",
    "AvailableOptionListResponse",
    "ChangePasswordRequest",
    "CreateCustomerOptionRequest",
    "CreateCustomerOptionSetRequest",
    "CreateCustomerOptionValueRequest",
    "CreateCustomerRequest",
    "Customer",
    "CustomerAttribute",
    "CustomerAttributeListResponse",
    "CustomerListResponse",
    "CustomerOption",
    "CustomerOptionListResponse",
    "CustomerOptionSet",
    "CustomerOptionSetListResponse",
    "CustomerOptionValue",
    "CustomerOptionValueListResponse",
    "Gender",
    "GroupListResponse",
    "LoginRequest",
    "LoginResponse",
    "OptionDescription",
    "OptionType",
    "PaginationInfo",
    "RegisterCustomerRequest",
    "ReplaceAttributesRequest",
    "StatusResponse",
    "UpdateCustomerRequest",
]
