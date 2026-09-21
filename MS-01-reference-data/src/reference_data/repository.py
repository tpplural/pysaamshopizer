"""Data-access (repository) layer for reference-data (MS-01).

Pure persistence queries — no business decisioning, no caching, no fail-soft swallowing (those
belong to the service layer). Each method mirrors a legacy DAO query shape referenced by the BRs:

  - resolve-by-code (getByField)           -> BR-REF-RES-001..004
  - localized, name-sorted lists           -> BR-REF-LST-001/002/006, LST-003
  - localized description lookup            -> BR-REF-API-002 name echo
  - counts / bulk inserts                  -> BR-REF-SEED-001..005
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .models import (
    Country,
    CountryDescription,
    Currency,
    Language,
    Zone,
    ZoneDescription,
)


class LanguageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_code(self, code: str) -> Language | None:
        # Legacy getByField(Language_.code, code) (BR-REF-RES-002).
        return self.session.scalar(select(Language).where(Language.code == code))

    def list_all(self) -> Sequence[Language]:
        # BR-REF-LST-003: legacy applied no order-by; target orders by sort_order then code (NF-4)
        # for deterministic language pickers.
        return list(
            self.session.scalars(
                select(Language).order_by(
                    Language.sort_order.is_(None), Language.sort_order.asc(), Language.code.asc()
                )
            )
        )

    def count(self) -> int:
        # BR-REF-SEED-001 guard: isEmpty() <=> language count == 0.
        return int(self.session.scalar(select(func.count()).select_from(Language)) or 0)

    def add(self, language: Language) -> Language:
        self.session.add(language)
        self.session.flush()
        return language


class CurrencyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_code(self, code: str) -> Currency | None:
        # Legacy getByField(Currency_.code, code) — uncached (BR-REF-RES-003).
        return self.session.scalar(select(Currency).where(Currency.code == code))

    def list_all(self) -> Sequence[Currency]:
        # BR-REF-LST-006: order by currency code asc.
        return list(self.session.scalars(select(Currency).order_by(Currency.code.asc())))

    def add(self, currency: Currency) -> Currency:
        self.session.add(currency)
        self.session.flush()
        return currency


class CountryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_iso_code(self, iso_code: str) -> Country | None:
        # Legacy getByField(Country_.isoCode, code) (BR-REF-RES-001).
        return self.session.scalar(select(Country).where(Country.iso_code == iso_code))

    def get_localized_name(self, country_id: int, language_code: str) -> str | None:
        # Localized display name for one country in one language (BR-REF-API-002 name echo).
        return self.session.scalar(
            select(CountryDescription.name).where(
                CountryDescription.country_id == country_id,
                CountryDescription.language_code == language_code,
            )
        )

    def list_by_language(self, language_code: str) -> Sequence[tuple[Country, str]]:
        """Countries that HAVE a name in ``language_code``, ordered by that localized name.

        Mirrors CountryDaoImpl.listByLanguage (inner-filter via the description join, order by
        d.name asc) — BR-REF-LST-001. Returns (country, localized_name) pairs so the service does
        not have to re-walk descriptions (and cannot hit the legacy unguarded .get(0)).
        """
        stmt = (
            select(Country, CountryDescription.name)
            .join(CountryDescription, CountryDescription.country_id == Country.id)
            .where(CountryDescription.language_code == language_code)
            .order_by(CountryDescription.name.asc())
        )
        return [(row[0], row[1]) for row in self.session.execute(stmt).all()]

    def add(self, country: Country) -> Country:
        self.session.add(country)
        self.session.flush()
        return country


class ZoneRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_code(self, code: str) -> Zone | None:
        # Legacy getByField(Zone_.code, code) — globally unique (BR-REF-RES-004).
        return self.session.scalar(
            select(Zone).options(selectinload(Zone.country)).where(Zone.code == code)
        )

    def list_by_language_and_country(
        self, language_code: str, country_iso_code: str
    ) -> Sequence[tuple[Zone, str, str]]:
        """A country's zones with a name in ``language_code``, ordered by that name.

        Mirrors ZoneDaoImpl.listByLanguageAndCountry (BR-REF-LST-002). Returns
        (zone, localized_name, country_iso_code) tuples.
        """
        stmt = (
            select(Zone, ZoneDescription.name, Country.iso_code)
            .join(ZoneDescription, ZoneDescription.zone_id == Zone.id)
            .join(Country, Country.id == Zone.country_id)
            .where(
                ZoneDescription.language_code == language_code,
                Country.iso_code == country_iso_code,
            )
            .order_by(ZoneDescription.name.asc())
        )
        return [(r[0], r[1], r[2]) for r in self.session.execute(stmt).all()]

    def list_by_language(self, language_code: str) -> Sequence[tuple[Zone, str, str]]:
        """Every zone with a name in ``language_code`` (no country predicate).

        Mirrors ZoneDaoImpl.listByLanguage (BR-REF-LST-002 language-only variant).
        """
        stmt = (
            select(Zone, ZoneDescription.name, Country.iso_code)
            .join(ZoneDescription, ZoneDescription.zone_id == Zone.id)
            .join(Country, Country.id == Zone.country_id)
            .where(ZoneDescription.language_code == language_code)
            .order_by(ZoneDescription.name.asc())
        )
        return [(r[0], r[1], r[2]) for r in self.session.execute(stmt).all()]

    def add(self, zone: Zone) -> Zone:
        self.session.add(zone)
        self.session.flush()
        return zone
