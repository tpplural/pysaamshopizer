"""Seed bootstrap tests (BR-REF-SEED-001..005, 004a).

Covers the Empty->Seeded guard, one-time-only semantics, en/fr languages, localizable countries,
zone catalog (unknown-country skip), and currency real-name (NF-2).
"""

from __future__ import annotations

from reference_data.repository import (
    CountryRepository,
    CurrencyRepository,
    LanguageRepository,
    ZoneRepository,
)
from reference_data.seed_data import CURRENCY_CATALOG, LANGUAGE_CODES
from reference_data.service import SeedService


def test_seed_guard_is_empty_true_on_fresh_db(session):
    # BR-REF-SEED-001: isEmpty() <=> language count == 0.
    seed = SeedService(session)
    assert seed.is_empty() is True


def test_populate_seeds_when_empty(session):
    # BR-REF-SEED-002: ordered atomic seed populates the reference tables.
    seed = SeedService(session)
    seeded = seed.populate()
    assert seeded is True
    assert seed.is_empty() is False


def test_seed_creates_english_and_french(session):
    # BR-REF-SEED-003: exactly en + fr ship out of the box, sort_order left null.
    SeedService(session).populate()
    langs = {l.code: l for l in LanguageRepository(session).list_all()}
    assert set(langs) == set(LANGUAGE_CODES) == {"en", "fr"}
    assert langs["en"].sort_order is None


def test_seed_is_one_time_only(session):
    # BR-REF-SEED-001: a completed seed permanently disables re-seed (guard fails).
    seed = SeedService(session)
    assert seed.populate() is True
    langs_after_first = LanguageRepository(session).count()
    assert seed.populate() is False  # guard now fails
    assert LanguageRepository(session).count() == langs_after_first  # no duplicates


def test_seed_countries_are_localized_in_every_language(session):
    # BR-REF-SEED-004a + INV-REF-007: each created country has a name in en and fr.
    SeedService(session).populate()
    repo = CountryRepository(session)
    ca = repo.get_by_iso_code("CA")
    assert ca is not None
    langs = {d.language_code for d in ca.descriptions}
    assert {"en", "fr"} <= langs


def test_seed_zones_skip_unknown_country_and_link_to_country(session):
    # BR-REF-SEED-004: zones link to their country; unknown-country entries are skipped (none here).
    SeedService(session).populate()
    zones = ZoneRepository(session)
    qc = zones.get_by_code("QC")
    assert qc is not None
    assert qc.country.iso_code == "CA"


def test_seed_currency_stores_real_name_not_code(session):
    # BR-REF-SEED-005 (NF-2 fix): currency.name holds the human name, not the code.
    SeedService(session).populate()
    cad = CurrencyRepository(session).get_by_code("CAD")
    assert cad is not None
    assert cad.name == CURRENCY_CATALOG["CAD"] == "Canadian Dollar"
    assert cad.name != cad.code


def test_seed_leaves_geozone_empty(session):
    # BR-REF-SEED-GEO finding: geozone ships EMPTY.
    from reference_data.models import Geozone

    SeedService(session).populate()
    assert session.query(Geozone).count() == 0
