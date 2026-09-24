# reference-data (MS-01) — Domain Model

**Target DB:** PostgreSQL · **Schema:** `reference_data`
**Naming:** snake_case columns, `bigint` surrogate PKs (legacy used a table-generator sequence;
target uses identity columns). No cross-service foreign keys — consumers store `_code`/`_iso` xrefs.

> Provenance rule: every column maps to a legacy source column OR a BR-ID requirement OR is a standard
> infrastructure column. Legacy mapping shown inline. Descriptions carry `language_code` (a language
> code string) rather than a FK to LANGUAGE, matching the target ERD's cross-reference-by-code approach
> within this service; LANGUAGE remains the owned table for resolution/listing.

## Core Entities (executable DDL)

```sql
CREATE SCHEMA IF NOT EXISTS reference_data;
SET search_path TO reference_data;

-- ─────────────────────────────────────────────────────────────
-- LANGUAGE  (maps to legacy LANGUAGE)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE language (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code         VARCHAR(10)  NOT NULL,           -- Maps to LANGUAGE.CODE (BR-REF-RES-002)
    sort_order   INTEGER,                         -- Maps to LANGUAGE.SORT_ORDER (BR-REF-LST-003 / NF-4)
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),  -- Audit standard
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),  -- Audit standard
    CONSTRAINT uq_language_code UNIQUE (code)      -- INV-REF-002 (legacy had NO unique — target adds it)
);

-- ─────────────────────────────────────────────────────────────
-- CURRENCY  (maps to legacy CURRENCY)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE currency (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code           VARCHAR(3)  NOT NULL,          -- Maps to CURRENCY.CURRENCY_CODE (BR-REF-RES-003), ISO-4217
    iso_code       VARCHAR(3)  NOT NULL,          -- Maps to CURRENCY.CURRENCY_CURRENCY_CODE (platform-derived)
    name           VARCHAR(80) NOT NULL,          -- Maps to CURRENCY.CURRENCY_NAME (BR-REF-SEED-005 / NF-2: store real name)
    supported      BOOLEAN     NOT NULL DEFAULT TRUE,  -- Maps to CURRENCY.CURRENCY_SUPPORTED
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_currency_code     UNIQUE (code),      -- Legacy CURRENCY_CODE unique
    CONSTRAINT uq_currency_iso_code UNIQUE (iso_code),  -- Legacy CURRENCY_CURRENCY_CODE unique
    CONSTRAINT uq_currency_name     UNIQUE (name)       -- Legacy CURRENCY_NAME unique
);

-- ─────────────────────────────────────────────────────────────
-- GEOZONE  (maps to legacy GEOZONE) — modeled, ships EMPTY (BR-REF-SEED-GEO)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE geozone (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code         VARCHAR(40),                     -- Maps to GEOZONE.GEOZONE_CODE
    name         VARCHAR(120),                    -- Maps to GEOZONE.GEOZONE_NAME
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE geozone_description (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geozone_id    BIGINT      NOT NULL REFERENCES geozone(id) ON DELETE CASCADE,  -- Maps to GEOZONE_DESCRIPTION.GEOZONE_ID
    language_code VARCHAR(10) NOT NULL,           -- Maps to GEOZONE_DESCRIPTION.LANGUAGE_ID (as code xref)
    name          VARCHAR(120) NOT NULL,          -- Maps to Description.name
    CONSTRAINT uq_geozone_desc UNIQUE (geozone_id, language_code)  -- Legacy unique(GEOZONE_ID, LANGUAGE_ID)
);

-- ─────────────────────────────────────────────────────────────
-- COUNTRY  (maps to legacy COUNTRY)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE country (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    iso_code     VARCHAR(2)  NOT NULL,            -- Maps to COUNTRY.COUNTRY_ISOCODE (BR-REF-RES-001)
    supported    BOOLEAN     NOT NULL DEFAULT TRUE,  -- Maps to COUNTRY.COUNTRY_SUPPORTED
    geozone_id   BIGINT      REFERENCES geozone(id),  -- Maps to COUNTRY.GEOZONE_ID (nullable; always null in legacy — BR-REF-SEED-GEO)
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_country_iso_code UNIQUE (iso_code)   -- Legacy COUNTRY_ISOCODE unique, not null
);

CREATE TABLE country_description (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_id    BIGINT      NOT NULL REFERENCES country(id) ON DELETE CASCADE,  -- Maps to COUNTRY_DESCRIPTION.COUNTRY_ID
    language_code VARCHAR(10) NOT NULL,           -- Maps to COUNTRY_DESCRIPTION.LANGUAGE_ID (as code xref)
    name          VARCHAR(120) NOT NULL,          -- Maps to Description.name (BR-REF-LST-001)
    CONSTRAINT uq_country_desc UNIQUE (country_id, language_code)  -- Legacy unique(COUNTRY_ID, LANGUAGE_ID)
);

-- ─────────────────────────────────────────────────────────────
-- ZONE  (maps to legacy ZONE)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE zone (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code         VARCHAR(40) NOT NULL,            -- Maps to ZONE.ZONE_CODE (BR-REF-RES-004), globally unique
    country_id   BIGINT      NOT NULL REFERENCES country(id),  -- Maps to ZONE.COUNTRY_ID, not null (every zone has a country)
    geozone_id   BIGINT      REFERENCES geozone(id),  -- Required by target ERD (GEOZONE groups ZONE); nullable, always null in legacy
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_zone_code UNIQUE (code)          -- Legacy ZONE_CODE unique, not null
);

CREATE TABLE zone_description (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    zone_id       BIGINT      NOT NULL REFERENCES zone(id) ON DELETE CASCADE,  -- Maps to ZONE_DESCRIPTION.ZONE_ID, not null
    language_code VARCHAR(10) NOT NULL,           -- Maps to ZONE_DESCRIPTION.LANGUAGE_ID (as code xref)
    name          VARCHAR(120) NOT NULL,          -- Maps to Description.name (BR-REF-LST-002)
    CONSTRAINT uq_zone_desc UNIQUE (zone_id, language_code)  -- Legacy unique(ZONE_ID, LANGUAGE_ID)
);

-- ─────────────────────────────────────────────────────────────
-- Indexes for the hot read paths (localized, name-sorted lists — BR-REF-LST-001/002)
-- ─────────────────────────────────────────────────────────────
CREATE INDEX ix_country_desc_lang_name ON country_description (language_code, name);
CREATE INDEX ix_zone_desc_lang_name    ON zone_description (language_code, name);
CREATE INDEX ix_zone_country           ON zone (country_id);
```

## Entity State Model (Layer A)

The reference entities (Country, Currency, Language, Zone, GeoZone) are **static lookups** — they have
no per-row lifecycle or status column (`supported` is a static flag, not a state machine). No entity
state model applies to them.

The one genuine lifecycle is the **database aggregate bootstrap**, an application-level state, not a
row status. It is modeled here because "green CRUD" that re-seeds a populated database would violate it.

#### Database bootstrap lifecycle
- **States:** Empty (initial), Seeded (terminal)
- **Transitions:**

  | From | To | Trigger (BR-ID) | Guard (precondition) |
  |------|----|-----------------|----------------------|
  | Empty | Seeded | BR-REF-SEED-002 | BR-REF-SEED-001: no languages exist (`language` count = 0), atomic seed commits |

**Closed-machine notes:** Empty is the only initial state and is reachable trivially; Seeded is
terminal (no transition leaves it — the guard permanently fails once languages exist); every
non-terminal state (Empty) has an outgoing transition. A failed seed rolls back and the aggregate
remains Empty (self-loop retry on next startup, guarded identically). No operation may move Seeded back
to Empty — there is no un-seed path, and the generator must not expose one.

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-REF-001 | A country's ISO code is unique and always present | country | constraint | db |
| INV-REF-002 | A language code is unique and always present (legacy enforced this only via the seed; target enforces it in the database) | language | constraint | db |
| INV-REF-003 | A currency's code, platform code, and name are each unique | currency | constraint | db |
| INV-REF-004 | Every zone belongs to exactly one country | zone | constraint | db |
| INV-REF-005 | A zone code is unique across all countries (not per-country) | zone | constraint | db |
| INV-REF-006 | At most one description per language for a given country / zone / geo-zone | country_description, zone_description, geozone_description | constraint | db |
| INV-REF-007 | Each supported country and zone has a name in every configured language (legacy guaranteed by seed convention only; target should enforce at write time) | country_description, zone_description | cross-field | app |

**Tier rationale:** INV-REF-001..006 are integrity invariants (uniqueness / referential) and are
enforced in the database (UNIQUE / NOT NULL / FK in the DDL above) — data integrity must not depend on
the app being the sole writer. INV-REF-007 is a business completeness rule the legacy enforced only by
seed convention (BR-REF-LST-001 shows the unguarded first-description assumption it protects); it is a
write-time application check in the target, not a database constraint, so it is tier=app.

## Database Logic Objects (Layer C)

**None.** No business logic for MS-01 was placed in the database tier. All reference logic is
app-tier (cached reads + a one-time seed). The Phase 1 placement candidates (BR-REF-SEED-002 one-time
batch seed; BR-REF-SEED-004a chatty country-description writes; BR-REF-CAC-001 hot cached reads) all
default to app-tier — the seed is one-shot (no runtime latency concern) and the reads are cache-mitigated.
The only mandatory-DB enforcement is the integrity invariants above, which are expressed as
UNIQUE/NOT-NULL/FK constraints directly in the Core Entities DDL (not as triggers/functions), so this
section has no rows.

## Notes on legacy → target deltas (traceability)
- Legacy `Currency.getCode()` used a String reference comparison (`!=`) — see net-new finding NF-1.
  The target stores `code` and `iso_code` as plain columns; no reference-identity logic is carried over.
- Legacy `Currency.name` held the code, not the human name (NF-2). Target `currency.name` is NOT NULL
  and intended to hold the real display name; the seed must be corrected to populate it.
- Legacy `Zone(country,name,code)` constructor overwrote code with name (NF-3). Unused; target uses
  explicit setters/DTOs, so the defect is not reproduced.
- `geozone_id` on `zone` is added per the target ERD (GEOZONE groups ZONE). Legacy linked geo-zone only
  on COUNTRY and never populated it; both `country.geozone_id` and `zone.geozone_id` ship null.
