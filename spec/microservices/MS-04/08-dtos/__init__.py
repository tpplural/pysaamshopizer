"""Barrel exports for MS-04 catalog DTOs — generated from 04-api-contract.yaml components/schemas."""
from __future__ import annotations

from .attach_digital_file_request import AttachDigitalFileRequest
from .attribute import Attribute
from .attribute_list_response import AttributeListItem, AttributeListResponse
from .availability import Availability
from .category import Category
from .category_list_response import CategoryListResponse
from .code_availability import CodeAvailability
from .create_attribute_request import CreateAttributeRequest
from .create_availability_request import CreateAvailabilityRequest
from .create_category_request import CreateCategoryRequest
from .create_manufacturer_request import CreateManufacturerRequest
from .create_option_request import CreateOptionRequest
from .create_option_value_request import CreateOptionValueRequest
from .create_price_request import CreatePriceRequest
from .create_product_request import CreateProductRequest
from .create_relationship_group_request import CreateRelationshipGroupRequest
from .create_relationship_request import CreateRelationshipRequest
from .create_review_request import CreateReviewRequest
from .description import Description
from .description_request import DescriptionRequest
from .digital_file import DigitalFile
from .enums import ImageSize, OptionWidgetType, PriceType
from .final_price import FinalPrice
from .final_price_request import FinalPriceRequest
from .image import Image
from .image_list_response import ImageListResponse
from .image_ref import ImageRef
from .image_upload_request import ImageUploadRequest
from .image_upload_result import ImageUploadResult
from .manufacturer import Manufacturer
from .manufacturer_list_response import ManufacturerListResponse
from .move_category_request import MoveCategoryRequest
from .option import Option
from .option_list_response import OptionListResponse
from .option_type import OptionType
from .option_value import OptionValue
from .option_value_list_response import OptionValueListResponse
from .pagination_info import PaginationInfo
from .price import Price
from .price_list_response import PriceListResponse
from .product import Product
from .product_list_response import ProductListResponse
from .product_type import ProductType
from .relationship import Relationship
from .relationship_group import RelationshipGroup
from .relationship_group_list_response import RelationshipGroupListResponse
from .review import Review
from .review_list_response import ReviewListResponse
from .update_availability_request import UpdateAvailabilityRequest
from .update_image_request import UpdateImageRequest
from .update_product_request import UpdateProductRequest
from .upload_images_request import UploadImageItem, UploadImagesRequest

__all__ = [
    "AttachDigitalFileRequest",
    "Attribute",
    "AttributeListItem",
    "AttributeListResponse",
    "Availability",
    "Category",
    "CategoryListResponse",
    "CodeAvailability",
    "CreateAttributeRequest",
    "CreateAvailabilityRequest",
    "CreateCategoryRequest",
    "CreateManufacturerRequest",
    "CreateOptionRequest",
    "CreateOptionValueRequest",
    "CreatePriceRequest",
    "CreateProductRequest",
    "CreateRelationshipGroupRequest",
    "CreateRelationshipRequest",
    "CreateReviewRequest",
    "Description",
    "DescriptionRequest",
    "DigitalFile",
    "FinalPrice",
    "FinalPriceRequest",
    "Image",
    "ImageListResponse",
    "ImageRef",
    "ImageSize",
    "ImageUploadRequest",
    "ImageUploadResult",
    "Manufacturer",
    "ManufacturerListResponse",
    "MoveCategoryRequest",
    "Option",
    "OptionListResponse",
    "OptionType",
    "OptionValue",
    "OptionValueListResponse",
    "OptionWidgetType",
    "PaginationInfo",
    "Price",
    "PriceListResponse",
    "PriceType",
    "Product",
    "ProductListResponse",
    "ProductType",
    "Relationship",
    "RelationshipGroup",
    "RelationshipGroupListResponse",
    "Review",
    "ReviewListResponse",
    "UpdateAvailabilityRequest",
    "UpdateImageRequest",
    "UpdateProductRequest",
    "UploadImageItem",
    "UploadImagesRequest",
]

# Rebuild models that use forward references (from __future__ import annotations)
# so nested/cross-referenced types resolve. Category is self-capable via lineage/tree
# reads; all list-envelope and nested-object models are rebuilt to be safe.
for _model in (
    Attribute,
    AttributeListItem,
    AttributeListResponse,
    Availability,
    Category,
    CategoryListResponse,
    CreateProductRequest,
    Description,
    DescriptionRequest,
    Image,
    ImageListResponse,
    Manufacturer,
    ManufacturerListResponse,
    Option,
    OptionListResponse,
    OptionValue,
    OptionValueListResponse,
    Price,
    PriceListResponse,
    Product,
    ProductListResponse,
    Relationship,
    RelationshipGroup,
    RelationshipGroupListResponse,
    Review,
    ReviewListResponse,
    UpdateProductRequest,
    UploadImageItem,
    UploadImagesRequest,
):
    _model.model_rebuild()
