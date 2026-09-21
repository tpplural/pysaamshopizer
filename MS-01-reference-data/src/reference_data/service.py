"""Service layer for reference-data (MS-01) — all 26 implementable BR-IDs.

Each method is annotated ``# BR-REF-...`` directly above it. Logic is derived from
spec/microservices/MS-01/01-business-rules.md (NOT from any test suite). Field names come from
04-api-contract.yaml via the copied DTOs.

Fail-soft discipline (BR-REF-CAC-002): the list/lookup read methods NEVER raise for a data/cache
error — they log and return an empty collection (the target normalization of the legacy null).
Resolve-by-code methods return None on miss; the controller maps None to 404 (except the name
endpoints which echo the code, BR-REF-API-002).
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from .cache import ReferenceCache
from .dto import Country, Currency, Language, Zone
from .models import (
    Country as CountryModel,
    CountryDescription,
    Currency as CurrencyModel,
    Language as LanguageModel,
    Zone as ZoneModel,
    ZoneDescription,
)
from .repository import (
    CountryRepository,
    CurrencyRepository,
    LanguageRepository,
    ZoneRepository,
)
from .seed_data import (
    COUNTRY_CATALOG,
    CURRENCY_CATALOG,
    LANGUAGE_CODES,
    ZONE_CATALOG,
)

logger = logging.getLogger("reference_data.service")

DEFAULT_LANGUAGE = "en"  # BR-REF-LNG-003: Constants.DEFAULT_LANGUAGE = "en"


# ═══════════════════════════════════════════════════════════════
# LanguageService — RES-002, LST-003, LNG-001/002/003
# ═══════════════════════════════════════════════════════════════
class LanguageService:
    def __init__(self, session: Session, cache: ReferenceCache) -> None:
        self.session = session
        self.cache = cache
        self.repo = LanguageRepository(session)

    # BR-REF-RES-002: Language is resolved by its language code
    def get_by_code(self, code: str) -> Language | None:
        row = self.repo.get_by_code(code)
        return _to_language_dto(row) if row else None

    # BR-REF-LST-003: All seeded languages are listed (code-keyed), ordered by sort_order (NF-4)
    def list_languages(self) -> list[Language]:
        # BR-REF-CAC-001: cached under the single "LANGUAGES" key, read-through.
        cached = self.cache.get(ReferenceCache.LANGUAGES_KEY)
        if cached is not None:
            return [Language(**item) for item in cached]
        try:
            rows = self.repo.list_all()
            result = [_to_language_dto(r) for r in rows]
            self.cache.set(ReferenceCache.LANGUAGES_KEY, [r.model_dump() for r in result])
            return result
        except Exception as exc:  # BR-REF-CAC-002: swallow, return empty
            logger.error("list_languages failed (fail-soft): %s", exc)
            return []

    # BR-REF-LST-003 (map form): languages as an insertion-ordered code-keyed map
    def get_languages_map(self) -> dict[str, Language]:
        # LinkedHashMap<code, Language> over the ordered list (getLanguagesMap).
        return {lang.code: lang for lang in self.list_languages()}

    # BR-REF-LNG-001: A language converts to a locale using its code as the language tag
    def to_locale(self, language: Language) -> str:
        if not language.code:
            raise ValueError("Language code required to build locale")
        # new Locale(language.code) -> the bare language tag (no country/variant).
        return language.code

    # BR-REF-LNG-002: A locale maps back to a configured language, or nothing if unsupported
    def to_language(self, locale: str) -> Language | None:
        try:
            # locale.getLanguage(): take the language part before any '_'/'-' separator, lowercased.
            lang_part = locale.replace("-", "_").split("_", 1)[0].lower()
            return self.get_languages_map().get(lang_part)
        except Exception as exc:  # swallowed exception -> None (legacy toLanguage)
            logger.error("to_language(%s) failed (fail-soft): %s", locale, exc)
            return None

    # BR-REF-LNG-003: Storefront language defaults to English when none can be resolved
    def resolve_language(
        self, explicit_code: str | None = None, ambient_code: str | None = None
    ) -> Language | None:
        # Precedence: explicit supplied code -> request ambient language -> English default.
        language: Language | None = None
        if explicit_code and explicit_code.strip():
            language = self.get_by_code(explicit_code)
        if language is None and ambient_code and ambient_code.strip():
            language = self.get_by_code(ambient_code)
        if language is None:
            language = self.get_by_code(DEFAULT_LANGUAGE)
        return language


# ═══════════════════════════════════════════════════════════════
# CurrencyService — RES-003, LST-006
# ═══════════════════════════════════════════════════════════════
class CurrencyService:
    def __init__(self, session: Session, cache: ReferenceCache) -> None:
        self.session = session
        self.cache = cache
        self.repo = CurrencyRepository(session)

    # BR-REF-RES-003: Currency is resolved by its currency code (uncached — no cache wrapper here)
    def get_by_code(self, code: str) -> Currency | None:
        row = self.repo.get_by_code(code)
        return _to_currency_dto(row) if row else None

    # BR-REF-LST-006: Currencies are listed ordered by currency code (plain, uncached)
    def list_currencies(self) -> list[Currency]:
        try:
            return [_to_currency_dto(r) for r in self.repo.list_all()]
        except Exception as exc:  # BR-REF-CAC-002 fail-soft (uniform read contract)
            logger.error("list_currencies failed (fail-soft): %s", exc)
            return []


# ═══════════════════════════════════════════════════════════════
# CountryService — RES-001, LST-001/004/005, API-002 (name echo)
# ═══════════════════════════════════════════════════════════════
class CountryService:
    def __init__(self, session: Session, cache: ReferenceCache) -> None:
        self.session = session
        self.cache = cache
        self.repo = CountryRepository(session)

    # BR-REF-RES-001: Country is resolved by its ISO code
    def get_by_iso_code(self, iso_code: str, language_code: str | None = None) -> Country | None:
        row = self.repo.get_by_iso_code(iso_code)
        if row is None:
            return None
        # BR-REF-API-002: when a language is requested, populate the localized display name;
        # echo the iso_code when no description exists in that language (name echo).
        name: str | None = None
        if language_code and language_code.strip():
            try:
                name = self.repo.get_localized_name(row.id, language_code) or row.iso_code
            except Exception as exc:  # BR-REF-CAC-002 fail-soft: never raise on a read error
                logger.error("get_by_iso_code(%s) name lookup failed: %s", iso_code, exc)
                name = row.iso_code
        return _to_country_dto(row, name=name)

    # BR-REF-LST-001: Countries listed in one language, name-sorted, named by localized description
    def get_countries(self, language_code: str) -> list[Country]:
        # BR-REF-CAC-001: cached per language under COUNTRIES_<lang>, read-through.
        key = ReferenceCache.countries_key(language_code)
        cached = self.cache.get(key)
        if cached is not None:
            return [Country(**item) for item in cached]
        try:
            pairs = self.repo.list_by_language(language_code)  # (country, localized_name), name-sorted
            result = [_to_country_dto(c, name=name) for (c, name) in pairs]
            self.cache.set(key, [r.model_dump() for r in result])
            return result
        except Exception as exc:  # BR-REF-CAC-002: swallow, return empty
            logger.error("get_countries(%s) failed (fail-soft): %s", language_code, exc)
            return []

    # BR-REF-LST-004: Country map is insertion-ordered by ISO code (preserving name-sort)
    def get_countries_map(self, language_code: str) -> dict[str, Country]:
        # LinkedHashMap over the already name-sorted list; key = iso_code.
        ordered: dict[str, Country] = {}
        for c in self.get_countries(language_code):
            ordered[c.iso_code] = c
        return ordered

    # BR-REF-LST-005: Countries can be filtered to a requested subset of ISO codes
    def get_countries_subset(self, iso_codes: list[str], language_code: str) -> list[Country]:
        base = self.get_countries(language_code)
        if not base:  # empty/unresolved base list -> empty result
            return []
        wanted = set(iso_codes)
        # Preserve the localized order of the base list (only keep requested codes).
        return [c for c in base if c.iso_code in wanted]

    # BR-REF-API-002: Country name lookup echoes the code when a display name cannot be resolved
    def resolve_country_name(self, iso_code: str, language: Language | None) -> str:
        try:
            if language is None:
                return iso_code  # null language -> echo the code
            mapping = self.get_countries_map(language.code)
            entry = mapping.get(iso_code)
            if entry is not None and entry.name:
                return entry.name
        except Exception as exc:  # ServiceException -> echo the code
            logger.error("resolve_country_name(%s) failed (fail-soft): %s", iso_code, exc)
        return iso_code


# ═══════════════════════════════════════════════════════════════
# ZoneService — RES-004, LST-002, API-001 (provinces), API-002 (name echo)
# ═══════════════════════════════════════════════════════════════
class ZoneService:
    def __init__(self, session: Session, cache: ReferenceCache) -> None:
        self.session = session
        self.cache = cache
        self.repo = ZoneRepository(session)

    # BR-REF-RES-004: Zone is resolved by its globally-unique zone code
    def get_by_code(self, code: str) -> Zone | None:
        row = self.repo.get_by_code(code)
        if row is None:
            return None
        return _to_zone_dto(row, country_iso_code=row.country.iso_code, name=None)

    # BR-REF-LST-002: Zones listed by country and language, name-sorted, named by localized desc
    def get_zones_by_country(self, country_iso_code: str, language_code: str) -> list[Zone]:
        # BR-REF-CAC-001: cached per (country, language) under ZONES_<countryIso>_<lang>.
        key = ReferenceCache.zones_country_key(country_iso_code, language_code)
        cached = self.cache.get(key)
        if cached is not None:
            return [Zone(**item) for item in cached]
        try:
            rows = self.repo.list_by_language_and_country(language_code, country_iso_code)
            result = [_to_zone_dto(z, country_iso_code=iso, name=name) for (z, name, iso) in rows]
            self.cache.set(key, [r.model_dump() for r in result])
            return result
        except Exception as exc:  # BR-REF-CAC-002 fail-soft
            logger.error(
                "get_zones_by_country(%s,%s) failed (fail-soft): %s",
                country_iso_code,
                language_code,
                exc,
            )
            return []

    # BR-REF-LST-002 (language-only variant): every zone with a name in a language, keyed by code
    def get_zones_map(self, language_code: str) -> dict[str, Zone]:
        # ZONES_<lang> map form (Map<zoneCode, Zone>).
        key = ReferenceCache.zones_lang_key(language_code)
        cached = self.cache.get(key)
        if cached is not None:
            return {code: Zone(**item) for code, item in cached.items()}
        try:
            rows = self.repo.list_by_language(language_code)
            ordered: dict[str, Zone] = {}
            for (z, name, iso) in rows:
                ordered[z.code] = _to_zone_dto(z, country_iso_code=iso, name=name)
            self.cache.set(key, {code: z.model_dump() for code, z in ordered.items()})
            return ordered
        except Exception as exc:  # BR-REF-CAC-002 fail-soft
            logger.error("get_zones_map(%s) failed (fail-soft): %s", language_code, exc)
            return {}

    # BR-REF-API-001: The provinces endpoint returns a country's localized zones, fail-soft
    def get_provinces(
        self,
        country_service: "CountryService",
        language_service: "LanguageService",
        country_code: str,
        lang: str | None,
    ) -> tuple[str, list[Zone]]:
        """Returns (status, zones). status is "Success" or "Failure" (fail-soft, never raises)."""
        try:
            language = language_service.resolve_language(explicit_code=lang)  # BR-REF-LNG-003
            if language is None:
                return "Failure", []
            country = country_service.get_countries_map(language.code).get(country_code)
            if country is None:
                # Unknown country -> null country -> lookup fails -> Failure, [] (fail-soft).
                return "Failure", []
            zones = self.get_zones_by_country(country.iso_code, language.code)
            # Success even when the country simply has no zones (empty success payload).
            return "Success", zones
        except Exception as exc:  # any error -> FAILURE (never an unhandled 5xx)
            logger.error("get_provinces(%s) failed (fail-soft): %s", country_code, exc)
            return "Failure", []

    # BR-REF-API-002: Zone name lookup echoes the code when a display name cannot be resolved
    def resolve_zone_name(self, code: str, language: Language | None) -> str:
        try:
            if language is None:
                return code  # null language -> echo the code
            mapping = self.get_zones_map(language.code)
            entry = mapping.get(code)
            if entry is not None and entry.name:
                return entry.name
        except Exception as exc:  # ServiceException -> echo the code
            logger.error("resolve_zone_name(%s) failed (fail-soft): %s", code, exc)
        return code


# ═══════════════════════════════════════════════════════════════
# FormSupportService — API-003 (credit-card years / months)
# ═══════════════════════════════════════════════════════════════
class FormSupportService:
    def __init__(self, cache: ReferenceCache) -> None:
        self.cache = cache

    # BR-REF-API-003: Credit-card expiry year list — rolling 10 years (current..+9), cached
    def get_credit_card_years(self, today: date | None = None) -> list[str]:
        cached = self.cache.get(ReferenceCache.CREDIT_CARD_YEARS_KEY)
        if cached is not None:
            return list(cached)
        current = (today or date.today()).year
        years = [str(current + i) for i in range(10)]  # current year .. current+9 (10 entries)
        self.cache.set(ReferenceCache.CREDIT_CARD_YEARS_KEY, years)
        return years

    # BR-REF-API-003: Months of the year as two-digit strings "01".."12", cached
    def get_months_of_year(self) -> list[str]:
        cached = self.cache.get(ReferenceCache.MONTHS_OF_YEAR_KEY)
        if cached is not None:
            return list(cached)
        months = [f"{i:02d}" for i in range(1, 13)]  # "01".."12"
        self.cache.set(ReferenceCache.MONTHS_OF_YEAR_KEY, months)
        return months


# ═══════════════════════════════════════════════════════════════
# SeedService — SEED-001..007 (one-time atomic bootstrap)
# ═══════════════════════════════════════════════════════════════
class SeedService:
    """One-time, all-or-nothing reference-data bootstrap (Empty -> Seeded)."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.languages = LanguageRepository(session)
        self.countries = CountryRepository(session)
        self.zones = ZoneRepository(session)
        self.currencies = CurrencyRepository(session)

    # BR-REF-SEED-001: The reference data is seeded only when the database is empty
    def is_empty(self) -> bool:
        # isEmpty() <=> language count == 0. Languages are created first, so a completed seed
        # permanently disables re-seed.
        return self.languages.count() == 0

    # BR-REF-SEED-002: The full seed is one ordered, all-or-nothing transaction
    def populate(self) -> bool:
        """Run the seed if (and only if) the DB is empty. Returns True if it seeded.

        Ordered: languages -> countries -> zones -> currencies. Any exception rolls the whole
        transaction back, leaving the aggregate Empty (retry on next startup). SEED-006/007
        (default store, tax class, product type, integration modules) are MOVED OUT of MS-01.
        """
        # BR-REF-SEED-001 guard (re-checked inside the transaction boundary).
        if not self.is_empty():
            return False
        try:
            self._create_languages()  # BR-REF-SEED-003
            self._create_countries()  # BR-REF-SEED-004a
            self._create_zones()  # BR-REF-SEED-004
            self._create_currencies()  # BR-REF-SEED-005
            self._create_sub_references_and_modules()  # BR-REF-SEED-006/007 (moved out — no-op)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()  # partial seed can never satisfy the guard
            raise

    # BR-REF-SEED-003: The out-of-the-box languages are English and French
    def _create_languages(self) -> None:
        for code in LANGUAGE_CODES:  # {"en", "fr"}
            self.languages.add(LanguageModel(code=code, sort_order=None))

    # BR-REF-SEED-004a: Countries seeded from a fixed ISO list, only those the platform can localize
    def _create_countries(self) -> None:
        languages = list(self.languages.list_all())
        for iso, names_by_lang in COUNTRY_CATALOG.items():
            # A country is created only if a localized name is available (pinned catalog = deterministic).
            if not names_by_lang:
                continue  # no locale -> country SKIPPED
            country = self.countries.add(CountryModel(iso_code=iso, supported=True))
            for language in languages:
                name = names_by_lang.get(language.code)
                if name is None:
                    continue
                self.session.add(
                    CountryDescription(
                        country_id=country.id, language_code=language.code, name=name
                    )
                )

    # BR-REF-SEED-004: Zones seeded from a country/language catalog, skipping unknown countries + dups
    def _create_zones(self) -> None:
        languages = list(self.languages.list_all())
        countries_by_iso = {c.iso_code: c for c in self.session.query(CountryModel).all()}

        # loadZones: accumulate zones by code, with per-(lang, zone) de-dup and null-country skip.
        zones_by_code: dict[str, ZoneModel] = {}
        descriptions: dict[str, list[tuple[str, str]]] = {}  # zone_code -> [(lang, name)]
        seen_lang_zone: set[str] = set()

        for language in languages:
            for entry in ZONE_CATALOG.get(language.code, []):
                zone_code = entry["zone_code"]
                country_code = entry["country_code"]
                if zone_code not in zones_by_code:
                    country = countries_by_iso.get(country_code)
                    if country is None:
                        logger.warning(
                            "seed zone %s: unknown country %s — skipped", zone_code, country_code
                        )
                        continue  # null country -> warn + skip
                    zones_by_code[zone_code] = ZoneModel(code=zone_code, country_id=country.id)
                    descriptions[zone_code] = []
                dedup_key = f"{language.code}_{zone_code}"
                if dedup_key in seen_lang_zone:
                    logger.warning("seed zone %s: duplicate (%s) — skipped", zone_code, language.code)
                    continue  # duplicate (lang, zone) -> warn + skip
                seen_lang_zone.add(dedup_key)
                descriptions[zone_code].append((language.code, entry["zone_name"]))

        # createZones: a zone with no descriptions is skipped; otherwise create + attach.
        for zone_code, zone in zones_by_code.items():
            descs = descriptions.get(zone_code) or []
            if not descs:
                logger.warning("seed zone %s: no descriptions — skipped", zone_code)
                continue  # null-desc skip
            self.zones.add(zone)
            for lang_code, name in descs:
                self.session.add(
                    ZoneDescription(zone_id=zone.id, language_code=lang_code, name=name)
                )

    # BR-REF-SEED-005: Currencies seeded from a catalog; store the REAL name (NF-2 fix)
    def _create_currencies(self) -> None:
        for code, real_name in CURRENCY_CATALOG.items():
            # Pinned catalog: each code is a valid ISO-4217 alpha code. supported defaults true.
            self.currencies.add(
                CurrencyModel(code=code, iso_code=code, name=real_name, supported=True)
            )

    # BR-REF-SEED-006 + BR-REF-SEED-007: default store / tax class / product type / modules — MOVED OUT
    def _create_sub_references_and_modules(self) -> None:
        # BR-REF-SEED-006: the default store + its tax class are owned by merchant-store / tax
        #   services in the target (boundary decision R-05) — NOT seeded here.
        # BR-REF-SEED-007: the general product type (catalog) + integration modules (system-config)
        #   are owned by their target services — NOT seeded here.
        # Recorded for traceability; reference-data seeds ONLY geo/currency/language data.
        return None


# ── DTO mappers (models -> contract DTOs) ───────────────────────
def _to_language_dto(row: LanguageModel) -> Language:
    return Language(code=row.code, sort_order=row.sort_order)


def _to_currency_dto(row: CurrencyModel) -> Currency:
    return Currency(code=row.code, name=row.name, supported=row.supported)


def _to_country_dto(row: CountryModel, name: str | None) -> Country:
    return Country(iso_code=row.iso_code, supported=row.supported, name=name)


def _to_zone_dto(row: ZoneModel, country_iso_code: str, name: str | None) -> Zone:
    return Zone(code=row.code, country_iso_code=country_iso_code, id=row.id, name=name)
