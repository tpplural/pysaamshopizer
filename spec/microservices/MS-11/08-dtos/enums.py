"""Enums for MS-11 content-cms. Source: 04-api-contract.yaml #/components/schemas {ContentType, ContentPosition, FileContentType}."""
from enum import Enum


class ContentType(str, Enum):
    Box = "Box"
    Page = "Page"
    Section = "Section"


class ContentPosition(str, Enum):
    Left = "Left"
    Right = "Right"


class FileContentType(str, Enum):
    StaticFile = "StaticFile"
    Image = "Image"
    Logo = "Logo"
    Product = "Product"
    ProductLarge = "ProductLarge"
    Property = "Property"
    Manufacturer = "Manufacturer"
    ProductDigital = "ProductDigital"
