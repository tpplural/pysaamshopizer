"""Enums for MS-03 merchant-store. Source: components/schemas WeightUnit, DimensionUnit (04-api-contract.yaml)."""
from enum import Enum


class WeightUnit(str, Enum):
    LB = "LB"
    KG = "KG"


class DimensionUnit(str, Enum):
    CM = "CM"
    IN = "IN"
