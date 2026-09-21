"""Service-layer tests (resolution, list ordering, subset, map, fail-soft, locale default).

Exercises RES-001..004, LST-001/002/004/005/006, LNG-001/002/003, API-001/002/003, CAC-002.
"""

from __future__ import annotations

from datetime import date

import pytest

from reference_data.service import (
    CountryService,
    CurrencyService,
    FormSupportService,
    LanguageService,
    SeedService,
    ZoneService,
)
from tests.conftest import FailingCache


@pytest.fixture()
def seeded(session):
    SeedService(session).populate()
    return session


# ── Resolution (RES-001..004) ───────────────────────────────────
def test_resolve_country_by_iso(seeded, cache):
    svc = CountryService(seeded, cache)
    assert svc.get_by_iso_code("CA").iso_code == "CA"
    assert svc.get_by_iso_code("ZZ") is None  # unknown -> None (controller maps to 404)


def test_resolve_language_by_code(seeded, cache):
    svc = LanguageService(seeded, cache)
    assert svc.get_by_code("en").code == "en"
    assert svc.get_by_code("xx") is None


def test_resolve_currency_by_code(seeded, cache):
    svc = CurrencyService(seeded, cache)
    assert svc.get_by_code("USD").code == "USD"
    assert svc.get_by_code("ABC") is None


def test_resolve_zone_by_code(seeded, cache):
    svc = ZoneService(seeded, cache)
    z = svc.get_by_code("QC")
    assert z is not None and z.code == "QC" and z.country_iso_code == "CA"
    assert svc.get_by_code("NOPE") is None


# ── Localized name-sorted lists (LST-001/002/006) ────────────────
def test_countries_are_name_sorted(seeded, cache):
    svc = CountryService(seeded, cache)
    names = [c.name for c in svc.get_countries("en")]
    assert names == sorted(names)
    assert all(c.name for c in svc.get_countries("en"))  # every country carries a localized name


def test_countries_unknown_language_is_failsoft_empty(seeded, cache):
    # BR-REF-LST-001 / CAC-002: unknown language -> empty list (never an error).
    svc = CountryService(seeded, cache)
    assert svc.get_countries("zz") == []


def test_country_zones_name_sorted_and_scoped(seeded, cache):
    svc = ZoneService(seeded, cache)
    zones = svc.get_zones_by_country("CA", "en")
    assert all(z.country_iso_code == "CA" for z in zones)
    names = [z.name for z in zones]
    assert names == sorted(names)


def test_currencies_sorted_by_code(seeded, cache):
    svc = CurrencyService(seeded, cache)
    codes = [c.code for c in svc.list_currencies()]
    assert codes == sorted(codes)


# ── Map + subset (LST-004/005) ───────────────────────────────────
def test_countries_map_preserves_name_sort_order(seeded, cache):
    svc = CountryService(seeded, cache)
    ordered_list = [c.iso_code for c in svc.get_countries("en")]
    mp = svc.get_countries_map("en")
    assert list(mp.keys()) == ordered_list  # insertion-ordered by the name-sorted list


def test_countries_subset_filters_and_keeps_order(seeded, cache):
    svc = CountryService(seeded, cache)
    subset = svc.get_countries_subset(["US", "CA", "MX"], "en")
    isos = [c.iso_code for c in subset]
    assert set(isos) == {"US", "CA", "MX"}
    assert isos == sorted(isos, key=lambda i: {c.iso_code: c.name for c in svc.get_countries("en")}[i])


def test_subset_empty_input_is_empty(seeded, cache):
    svc = CountryService(seeded, cache)
    assert svc.get_countries_subset([], "en") == []


# ── Locale / language defaulting (LNG-001/002/003) ───────────────
def test_to_locale_uses_code(seeded, cache):
    svc = LanguageService(seeded, cache)
    assert svc.to_locale(svc.get_by_code("fr")) == "fr"


def test_to_language_maps_locale_or_none(seeded, cache):
    svc = LanguageService(seeded, cache)
    assert svc.to_language("en_US").code == "en"
    assert svc.to_language("fr-CA").code == "fr"
    assert svc.to_language("de_DE") is None  # German not configured


def test_resolve_language_defaults_to_english(seeded, cache):
    # BR-REF-LNG-003: explicit -> ambient -> English default.
    svc = LanguageService(seeded, cache)
    assert svc.resolve_language(explicit_code="fr").code == "fr"
    assert svc.resolve_language(explicit_code="zz").code == "en"  # unknown -> default en
    assert svc.resolve_language().code == "en"  # nothing supplied -> default en


# ── Provinces + name echo (API-001/002) ──────────────────────────
def test_provinces_success_and_failure(seeded, cache):
    zsvc = ZoneService(seeded, cache)
    csvc = CountryService(seeded, cache)
    lsvc = LanguageService(seeded, cache)
    status, zones = zsvc.get_provinces(csvc, lsvc, "CA", "en")
    assert status == "Success" and len(zones) > 0
    # Unknown country -> Failure, [] (fail-soft, never raises).
    status2, zones2 = zsvc.get_provinces(csvc, lsvc, "ZZ", "en")
    assert status2 == "Failure" and zones2 == []


def test_country_name_echoes_code_when_unresolved(seeded, cache):
    svc = CountryService(seeded, cache)
    en = LanguageService(seeded, cache).get_by_code("en")
    assert svc.resolve_country_name("CA", en) == "Canada"
    assert svc.resolve_country_name("ZZ", en) == "ZZ"  # echo the code
    assert svc.resolve_country_name("CA", None) == "CA"  # null language -> echo


def test_zone_name_echoes_code_when_unresolved(seeded, cache):
    svc = ZoneService(seeded, cache)
    en = LanguageService(seeded, cache).get_by_code("en")
    assert svc.resolve_zone_name("QC", en) == "Quebec"
    assert svc.resolve_zone_name("NOPE", en) == "NOPE"


# ── Form-support (API-003) ───────────────────────────────────────
def test_credit_card_years_are_rolling_ten(cache):
    svc = FormSupportService(cache)
    years = svc.get_credit_card_years(today=date(2025, 6, 1))
    assert years == [str(y) for y in range(2025, 2035)]
    assert len(years) == 10


def test_months_of_year_two_digit(cache):
    svc = FormSupportService(cache)
    assert svc.get_months_of_year() == [f"{i:02d}" for i in range(1, 13)]


# ── Fail-soft with a failing cache (CAC-002) ─────────────────────
def test_lists_failsoft_when_cache_never_hits(seeded):
    # A cache that never returns a hit must not break the read path; the store load still works.
    failing = FailingCache()
    csvc = CountryService(seeded, failing)
    assert len(csvc.get_countries("en")) > 0
    lsvc = LanguageService(seeded, failing)
    assert {l.code for l in lsvc.list_languages()} == {"en", "fr"}
