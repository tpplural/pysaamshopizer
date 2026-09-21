"""FastAPI dependency wiring for reference-data (MS-01).

Builds request-scoped service instances over a DB session + the shared cache. reference-data is
GLOBAL/tenant-neutral: there is NO x-store-id / x-tenant-id dependency (documented ADR-006
exception). Only x-correlation-id (optional) is read, for tracing.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .cache import ReferenceCache
from .config import get_settings
from .database import get_session
from .service import (
    CountryService,
    CurrencyService,
    FormSupportService,
    LanguageService,
    ZoneService,
)

_settings = get_settings()
# One process-wide cache client (fail-soft; degrades to no-op in test/when Redis is down).
_cache = ReferenceCache(
    url=_settings.redis_url,
    ttl_seconds=_settings.cache_ttl_seconds,
    enabled=not _settings.test_mode,
)


def get_cache() -> ReferenceCache:
    return _cache


def get_correlation_id(x_correlation_id: str | None = Header(default=None)) -> str | None:
    # Optional tracing id only — reference data is global, not tenant-scoped.
    return x_correlation_id


def db_session() -> Iterator[Session]:
    yield from get_session()


def get_country_service(session: Session = Depends(db_session)) -> CountryService:
    return CountryService(session, _cache)


def get_currency_service(session: Session = Depends(db_session)) -> CurrencyService:
    return CurrencyService(session, _cache)


def get_language_service(session: Session = Depends(db_session)) -> LanguageService:
    return LanguageService(session, _cache)


def get_zone_service(session: Session = Depends(db_session)) -> ZoneService:
    return ZoneService(session, _cache)


def get_form_support_service() -> FormSupportService:
    return FormSupportService(_cache)
