"""Country + country-zone routes (MS-01).

Paths/methods/status codes/query params EXACTLY per 04-api-contract.yaml:
  GET /countries                    -> {items:[Country]} (or Map keyed by iso_code when as=Map)
  GET /countries/{isoCode}          -> Country (404 unknown)
  GET /countries/{isoCode}/name     -> {value}  (echoes code if unresolved, always 200)
  GET /countries/{isoCode}/zones    -> {items:[Zone]} (fail-soft)
"""

from __future__ import annotations

from typing import Union

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from ..dto import Country, CountryListResponse, NameResponse, ZoneListResponse
from ..dependencies import (
    get_correlation_id,
    get_country_service,
    get_language_service,
    get_zone_service,
)
from ..errors import BadRequestError, NotFoundError
from ..service import CountryService, LanguageService, ZoneService

router = APIRouter(dependencies=[Depends(get_correlation_id)])


@router.get("/countries", response_model=None)
def list_countries(
    language: str | None = Query(
        default=None, description="Language code the country names are localized to"
    ),
    iso_codes: str | None = Query(
        default=None, description="Optional CSV subset of ISO codes (BR-REF-LST-005)"
    ),
    as_: str = Query(default="List", alias="as", description="List (default) or Map (BR-REF-LST-004)"),
    service: CountryService = Depends(get_country_service),
) -> Union[CountryListResponse, JSONResponse]:
    # Contract: language is REQUIRED — a missing or blank value is a 400 bad_request (not 422).
    # The param is declared optional so a missing value reaches this explicit check instead of
    # FastAPI's default 422 for absent required params.
    if language is None or not language.strip():
        raise BadRequestError("language is required")
    if as_ not in ("List", "Map"):
        raise BadRequestError(f"Unsupported 'as' value: {as_}")

    # BR-REF-LST-005: optional subset filter (CSV -> list). Empty string -> empty result.
    if iso_codes is not None:
        codes = [c for c in (part.strip() for part in iso_codes.split(",")) if c]
        countries = service.get_countries_subset(codes, language)
    else:
        # BR-REF-LST-001: localized, name-sorted list (fail-soft empty).
        countries = service.get_countries(language)

    if as_ == "Map":
        # BR-REF-LST-004: insertion-ordered map keyed by iso_code, preserving name-sort.
        ordered = {c.iso_code: c.model_dump() for c in countries}
        return JSONResponse(content=ordered)
    return CountryListResponse(items=countries)


@router.get("/countries/{iso_code}", response_model=Country)
def get_country(
    iso_code: str,
    language: str | None = Query(
        default=None, description="Optional language code to localize the country name"
    ),
    service: CountryService = Depends(get_country_service),
) -> Country:
    # BR-REF-RES-001: resolve by ISO code; unknown -> 404.
    country = service.get_by_iso_code(iso_code, language_code=language)
    if country is None:
        raise NotFoundError(f"No country for ISO code {iso_code}")
    return country


@router.get("/countries/{iso_code}/name", response_model=NameResponse)
def get_country_name(
    iso_code: str,
    language: str | None = Query(default=None),
    country_service: CountryService = Depends(get_country_service),
    language_service: LanguageService = Depends(get_language_service),
) -> NameResponse:
    # BR-REF-API-002: echo the code when the display name cannot be resolved (never 404).
    resolved_lang = language_service.get_by_code(language) if language else None
    value = country_service.resolve_country_name(iso_code, resolved_lang)
    return NameResponse(value=value)


@router.get("/countries/{iso_code}/zones", response_model=ZoneListResponse)
def list_country_zones(
    iso_code: str,
    language: str | None = Query(
        default=None, description="Language code the zone names are localized to"
    ),
    service: ZoneService = Depends(get_zone_service),
) -> ZoneListResponse:
    # Contract: language is REQUIRED — missing/blank -> 400 bad_request (not 422).
    if language is None or not language.strip():
        raise BadRequestError("language is required")
    # BR-REF-LST-002: a country's zones for a language, name-sorted (fail-soft empty).
    zones = service.get_zones_by_country(iso_code, language)
    return ZoneListResponse(items=zones)
