"""Enum types from MS-04 04-api-contract.yaml components/schemas (ImageSize, PriceType, OptionWidgetType)."""
from __future__ import annotations

from enum import Enum


class ImageSize(str, Enum):
    Large = "Large"
    Small = "Small"
    Original = "Original"


class PriceType(str, Enum):
    OneTime = "OneTime"
    Monthly = "Monthly"


class OptionWidgetType(str, Enum):
    Text = "Text"
    Radio = "Radio"
    Select = "Select"
    Checkbox = "Checkbox"
