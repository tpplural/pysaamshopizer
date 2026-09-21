"""Zone + provinces routes (MS-01).

Per 04-api-contract.yaml:
  GET  /zones/{code}        -> Zone (404 unknown)
  GET  /zones/{code}/name   -> {value} (echoes code if unresolved, always 200)
  POST /provinces           -> {status, items} fail-soft envelope (BR-REF-API-001)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from ..dto import (
    NameResponse,
    ProvinceEntry,
    ProvincesRequest,
    ProvincesResponse,
    ProvincesStatus,
    Zone,
)
from ..dependencies import (
    get_correlation_id,
    get_country_service,
    get_language_service,
    get_zone_service,
)
from ..errors import BadRequestError, NotFoundError
from ..service import CountryService, LanguageService, ZoneService

router = APIRouter(dependencies=[Depends(get_correlation_id)])


@router.get("/zones/{code}", response_model=Zone)
def get_zone(
    code: str,
    service: ZoneService = Depends(get_zone_service),
) -> Zone:
    # BR-REF-RES-004: resolve by globally-unique zone code; unknown -> 404.
    zone = service.get_by_code(code)
    if zone is None:
        raise NotFoundError(f"No zone for code {code}")
    return zone


@router.get("/zones/{code}/name", response_model=NameResponse)
def get_zone_name(
    code: str,
    language: str | None = Query(default=None),
    zone_service: ZoneService = Depends(get_zone_service),
    language_service: LanguageService = Depends(get_language_service),
) -> NameResponse:
    # BR-REF-API-002: echo the code when the display name cannot be resolved (never 404).
    resolved_lang = language_service.get_by_code(language) if language else None
    value = zone_service.resolve_zone_name(code, resolved_lang)
    return NameResponse(value=value)


@router.post("/provinces", response_model=ProvincesResponse)
def get_provinces(
    body: dict[str, Any] = Body(...),
    zone_service: ZoneService = Depends(get_zone_service),
    country_service: CountryService = Depends(get_country_service),
    language_service: LanguageService = Depends(get_language_service),
) -> ProvincesResponse:
    # Contract: country_code is REQUIRED in the body — absence is a 400 bad_request (not 422).
    # The body is parsed loosely so a missing required field reaches this explicit check; a present
    # body is then validated through the ProvincesRequest DTO (malformed -> 422 via pydantic).
    if not isinstance(body, dict) or body.get("country_code") in (None, ""):
        raise BadRequestError("country_code is required")
    from pydantic import ValidationError as _PydValidationError

    try:
        request = ProvincesRequest(**body)
    except _PydValidationError as exc:
        raise BadRequestError("invalid provinces request") from exc
    # BR-REF-API-001 + BR-REF-LNG-003: fail-soft {status, items}; unknown country -> Failure, [].
    status_str, zones = zone_service.get_provinces(
        country_service=country_service,
        language_service=language_service,
        country_code=request.country_code,
        lang=request.lang,
    )
    status = ProvincesStatus.Success if status_str == "Success" else ProvincesStatus.Failure
    items = [
        ProvinceEntry(name=(z.name or z.code), code=z.code, id=(z.id or 0)) for z in zones
    ]
    return ProvincesResponse(status=status, items=items)
