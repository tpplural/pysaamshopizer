"""Form-support (card-expiry) routes (MS-01).

Per 04-api-contract.yaml:
  GET /credit-card-years -> {items:[str]} 10 consecutive years (current .. +9), cached
  GET /months-of-year    -> {items:[str]} "01".."12", cached
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dto import StringListResponse
from ..dependencies import get_correlation_id, get_form_support_service
from ..service import FormSupportService

router = APIRouter(dependencies=[Depends(get_correlation_id)])


@router.get("/credit-card-years", response_model=StringListResponse)
def list_credit_card_years(
    service: FormSupportService = Depends(get_form_support_service),
) -> StringListResponse:
    # BR-REF-API-003: rolling 10-year expiry list, cached.
    return StringListResponse(items=service.get_credit_card_years())


@router.get("/months-of-year", response_model=StringListResponse)
def list_months_of_year(
    service: FormSupportService = Depends(get_form_support_service),
) -> StringListResponse:
    # BR-REF-API-003: months "01".."12", cached.
    return StringListResponse(items=service.get_months_of_year())
