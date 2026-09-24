"""Enums from MS-05 04-api-contract.yaml components/schemas (Gender, OptionType)."""

from enum import Enum


class Gender(str, Enum):
    M = "M"
    F = "F"


class OptionType(str, Enum):
    Text = "Text"
    Radio = "Radio"
    Select = "Select"
    Checkbox = "Checkbox"
