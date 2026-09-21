"""Pinned seed catalogs for reference-data (MS-01).

The legacy seed derived its createable country set from the *running JVM's* available locales,
making the seeded set platform-dependent (BR-REF-SEED-004a, net-new finding NF-5). The target
PINS the catalogs explicitly so the seed is deterministic. Each country/zone carries its localized
names for every shipped language (en, fr) so INV-REF-007 (every supported country/zone has a name
in every configured language) holds at seed time and BR-REF-LST-001/002 never hit the legacy
unguarded-first-description path.

Currency names hold the REAL display name (NF-2 fix), not the code.
"""

from __future__ import annotations

# BR-REF-SEED-003: the out-of-the-box languages are English and French.
LANGUAGE_CODES: tuple[str, ...] = ("en", "fr")

# BR-REF-SEED-004a: pinned country catalog. Each entry maps iso_code -> {language_code: name}.
# A representative, deterministic set (the legacy 246-code list minus codes with no platform
# locale). Every entry is localizable in every shipped language (INV-REF-007).
COUNTRY_CATALOG: dict[str, dict[str, str]] = {
    "AF": {"en": "Afghanistan", "fr": "Afghanistan"},
    "AL": {"en": "Albania", "fr": "Albanie"},
    "AR": {"en": "Argentina", "fr": "Argentine"},
    "AU": {"en": "Australia", "fr": "Australie"},
    "AT": {"en": "Austria", "fr": "Autriche"},
    "BE": {"en": "Belgium", "fr": "Belgique"},
    "BR": {"en": "Brazil", "fr": "Brésil"},
    "CA": {"en": "Canada", "fr": "Canada"},
    "CN": {"en": "China", "fr": "Chine"},
    "CO": {"en": "Colombia", "fr": "Colombie"},
    "DK": {"en": "Denmark", "fr": "Danemark"},
    "EG": {"en": "Egypt", "fr": "Égypte"},
    "FI": {"en": "Finland", "fr": "Finlande"},
    "FR": {"en": "France", "fr": "France"},
    "DE": {"en": "Germany", "fr": "Allemagne"},
    "GR": {"en": "Greece", "fr": "Grèce"},
    "IN": {"en": "India", "fr": "Inde"},
    "IE": {"en": "Ireland", "fr": "Irlande"},
    "IT": {"en": "Italy", "fr": "Italie"},
    "JP": {"en": "Japan", "fr": "Japon"},
    "MX": {"en": "Mexico", "fr": "Mexique"},
    "NL": {"en": "Netherlands", "fr": "Pays-Bas"},
    "NZ": {"en": "New Zealand", "fr": "Nouvelle-Zélande"},
    "NO": {"en": "Norway", "fr": "Norvège"},
    "PL": {"en": "Poland", "fr": "Pologne"},
    "PT": {"en": "Portugal", "fr": "Portugal"},
    "RU": {"en": "Russia", "fr": "Russie"},
    "SA": {"en": "Saudi Arabia", "fr": "Arabie Saoudite"},
    "SG": {"en": "Singapore", "fr": "Singapour"},
    "ZA": {"en": "South Africa", "fr": "Afrique du Sud"},
    "ES": {"en": "Spain", "fr": "Espagne"},
    "SE": {"en": "Sweden", "fr": "Suède"},
    "CH": {"en": "Switzerland", "fr": "Suisse"},
    "TR": {"en": "Turkey", "fr": "Turquie"},
    "GB": {"en": "United Kingdom", "fr": "Royaume-Uni"},
    "US": {"en": "United States", "fr": "États-Unis"},
}

# BR-REF-SEED-004: zone catalog, organized by language then entries. Each entry names a zone,
# its localized display name, and the country it belongs to. An entry whose country is not in the
# seeded country set is skipped with a warning; a duplicate (lang, zone_code) is skipped.
# zone_code is the plain province/state code (BR-REF-RES-004) and is globally unique within the
# zone table (INV-REF-005). Canadian province codes (QC, ON, ...) and US state codes (NY, TX, ...)
# are distinct sets, so no collision occurs inside the zone table.
ZONE_CATALOG: dict[str, list[dict[str, str]]] = {
    "en": [
        # United States (subset)
        {"zone_code": "AL", "zone_name": "Alabama", "country_code": "US"},
        {"zone_code": "AK", "zone_name": "Alaska", "country_code": "US"},
        {"zone_code": "AZ", "zone_name": "Arizona", "country_code": "US"},
        {"zone_code": "CA", "zone_name": "California", "country_code": "US"},
        {"zone_code": "CO", "zone_name": "Colorado", "country_code": "US"},
        {"zone_code": "FL", "zone_name": "Florida", "country_code": "US"},
        {"zone_code": "NY", "zone_name": "New York", "country_code": "US"},
        {"zone_code": "TX", "zone_name": "Texas", "country_code": "US"},
        {"zone_code": "WA", "zone_name": "Washington", "country_code": "US"},
        # Canada (provinces/territories) — plain province codes (BR-REF-RES-004)
        {"zone_code": "AB", "zone_name": "Alberta", "country_code": "CA"},
        {"zone_code": "BC", "zone_name": "British Columbia", "country_code": "CA"},
        {"zone_code": "MB", "zone_name": "Manitoba", "country_code": "CA"},
        {"zone_code": "NB", "zone_name": "New Brunswick", "country_code": "CA"},
        {"zone_code": "NL", "zone_name": "Newfoundland and Labrador", "country_code": "CA"},
        {"zone_code": "NS", "zone_name": "Nova Scotia", "country_code": "CA"},
        {"zone_code": "ON", "zone_name": "Ontario", "country_code": "CA"},
        {"zone_code": "PE", "zone_name": "Prince Edward Island", "country_code": "CA"},
        {"zone_code": "QC", "zone_name": "Quebec", "country_code": "CA"},
        {"zone_code": "SK", "zone_name": "Saskatchewan", "country_code": "CA"},
    ],
    "fr": [
        {"zone_code": "AL", "zone_name": "Alabama", "country_code": "US"},
        {"zone_code": "AK", "zone_name": "Alaska", "country_code": "US"},
        {"zone_code": "AZ", "zone_name": "Arizona", "country_code": "US"},
        {"zone_code": "CA", "zone_name": "Californie", "country_code": "US"},
        {"zone_code": "CO", "zone_name": "Colorado", "country_code": "US"},
        {"zone_code": "FL", "zone_name": "Floride", "country_code": "US"},
        {"zone_code": "NY", "zone_name": "New York", "country_code": "US"},
        {"zone_code": "TX", "zone_name": "Texas", "country_code": "US"},
        {"zone_code": "WA", "zone_name": "Washington", "country_code": "US"},
        {"zone_code": "AB", "zone_name": "Alberta", "country_code": "CA"},
        {"zone_code": "BC", "zone_name": "Colombie-Britannique", "country_code": "CA"},
        {"zone_code": "MB", "zone_name": "Manitoba", "country_code": "CA"},
        {"zone_code": "NB", "zone_name": "Nouveau-Brunswick", "country_code": "CA"},
        {"zone_code": "NL", "zone_name": "Terre-Neuve-et-Labrador", "country_code": "CA"},
        {"zone_code": "NS", "zone_name": "Nouvelle-Écosse", "country_code": "CA"},
        {"zone_code": "ON", "zone_name": "Ontario", "country_code": "CA"},
        {"zone_code": "PE", "zone_name": "Île-du-Prince-Édouard", "country_code": "CA"},
        {"zone_code": "QC", "zone_name": "Québec", "country_code": "CA"},
        {"zone_code": "SK", "zone_name": "Saskatchewan", "country_code": "CA"},
    ],
}

# BR-REF-SEED-005: currency catalog. code -> real display name (NF-2 fix — legacy stored the code
# as the name). iso_code mirrors the ISO-4217 alpha code. Codes the platform (Python stdlib) cannot
# vet are still seeded here because the catalog is pinned and explicit.
CURRENCY_CATALOG: dict[str, str] = {
    "AED": "United Arab Emirates Dirham",
    "AUD": "Australian Dollar",
    "BRL": "Brazilian Real",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "DKK": "Danish Krone",
    "EUR": "Euro",
    "GBP": "Pound Sterling",
    "INR": "Indian Rupee",
    "JPY": "Japanese Yen",
    "MXN": "Mexican Peso",
    "NOK": "Norwegian Krone",
    "NZD": "New Zealand Dollar",
    "PLN": "Polish Zloty",
    "RUB": "Russian Ruble",
    "SEK": "Swedish Krona",
    "SGD": "Singapore Dollar",
    "USD": "US Dollar",
    "ZAR": "South African Rand",
}
