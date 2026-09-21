"""Currency routes (MS-01).

Per 04-api-contract.yaml:
  GET /currencies        -> {items:[Currency]} code-sorted
  GET /currencies/{code} -> Currency (404 unknown)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dto import Currency, CurrencyListResponse
from ..dependencies import get_correlation_id, get_currency_service
from ..errors import NotFoundError
from ..service import CurrencyService

router = APIRouter(dependencies=[Depends(get_correlation_id)])


@router.get("/currencies", response_model=CurrencyListResponse)
def list_currencies(
    service: CurrencyService = Depends(get_currency_service),
) -> CurrencyListResponse:
    # BR-REF-LST-006: all currencies ordered by code (plain, uncached).
    return CurrencyListResponse(items=service.list_currencies())


@router.get("/currencies/{code}", response_model=Currency)
def get_currency(
    code: str,
    service: CurrencyService = Depends(get_currency_service),
) -> Currency:
    # BR-REF-RES-003: resolve by currency code (uncached); unknown -> 404.
    currency = service.get_by_code(code)
    if currency is None:
        raise NotFoundError(f"No currency for code {code}")
    return currency
