"""Language routes (MS-01).

Per 04-api-contract.yaml:
  GET /languages            -> {items:[Language]}
  GET /languages/resolve    -> Language (200) or 204 when no configured language matches the locale
  GET /languages/{code}     -> Language (404 unknown)

NOTE: /languages/resolve is declared BEFORE /languages/{code} so the literal path is not captured
by the {code} path parameter.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from ..dto import Language, LanguageListResponse
from ..dependencies import get_correlation_id, get_language_service
from ..errors import BadRequestError, NotFoundError
from ..service import LanguageService

router = APIRouter(dependencies=[Depends(get_correlation_id)])


@router.get("/languages", response_model=LanguageListResponse)
def list_languages(
    service: LanguageService = Depends(get_language_service),
) -> LanguageListResponse:
    # BR-REF-LST-003: all configured languages (target orders by sort_order then code — NF-4).
    return LanguageListResponse(items=service.list_languages())


@router.get("/languages/resolve", response_model=Language)
def resolve_language(
    locale: str | None = Query(
        default=None, description="A locale or language tag, e.g. en_US, fr-CA"
    ),
    service: LanguageService = Depends(get_language_service),
) -> Response | Language:
    # Contract: locale is REQUIRED — missing/blank -> 400 bad_request (not 422).
    if locale is None or not locale.strip():
        raise BadRequestError("locale is required")
    # BR-REF-LNG-001 + BR-REF-LNG-002: map the locale's language part to a configured language;
    # no match -> 204 No Content (caller applies its own default per BR-REF-LNG-003).
    language = service.to_language(locale)
    if language is None:
        return Response(status_code=204)
    return language


@router.get("/languages/{code}", response_model=Language)
def get_language(
    code: str,
    service: LanguageService = Depends(get_language_service),
) -> Language:
    # BR-REF-RES-002: resolve by language code; unknown -> 404.
    language = service.get_by_code(code)
    if language is None:
        raise NotFoundError(f"No language for code {code}")
    return language
