# MS-07 (tax) — Domain Model

**Version**: 1.0
**Service ID**: MS-07
**Schema**: `tax_schema`
**Target**: PostgreSQL 15+ (FastAPI service)

Owned tables: `tax_class`, `tax_rate`, `tax_rate_description`, `tax_configuration`.
External ids (NOT owned, no DDL here): `country_id` (MS-01 reference), `zone_id` (MS-01 reference),
`language_id` (MS-01 reference), `merchant_store_id` (MS-03 store), `product` tax-class association
(MS-04 catalog — the reverse association is owned by catalog; MS-07 only reads it on class delete).

> **Legacy origin note:** `tax_configuration` is modelled here as an owned first-class table. In the
> legacy system it is NOT a table — it is a JSON blob persisted inside `MERCHANT_CONFIGURATION` under the
> key `TAX_CONFIG` (one document per store). MS-07 owns the tax configuration concept; the modernized
> representation is a table (one row per store). The legacy serialization persisted ONLY the tax basis
> (see BR-TAX-003) — the two collection-scope columns below preserve that behavior via defaults (they are
> stored, but the legacy never round-tripped them; the modernized service may later choose to persist
> them — a Phase 4a BA decision).

## Core Entities

```sql
CREATE SCHEMA IF NOT EXISTS tax_schema;

-- ---------------------------------------------------------------------------
-- tax_class : a taxable classification for products (legacy TAX_CLASS)
-- ---------------------------------------------------------------------------
CREATE TABLE tax_schema.tax_class (
    id                 UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Maps to TAX_CLASS.TAX_CLASS_CODE (NotEmpty, length 10). "DEFAULT" is reserved (BR-TAX-025).
    code               VARCHAR(10)  NOT NULL,
    -- Maps to TAX_CLASS.TAX_CLASS_TITLE (NotEmpty, length 32).
    title              VARCHAR(32)  NOT NULL,
    -- Maps to TAX_CLASS.MERCHANT_ID — external store id (MS-03). Store scoping (BR-TAX-025).
    merchant_store_id  BIGINT       NOT NULL,
    -- Standard infrastructure (multi-tenancy / audit).
    tenant_id          UUID         NOT NULL,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- Unique (merchant_store_id, code) — maps to legacy UniqueConstraint (MERCHANT_ID, TAX_CLASS_CODE).
    CONSTRAINT uq_tax_class_store_code UNIQUE (merchant_store_id, code)
);
CREATE INDEX ix_tax_class_store ON tax_schema.tax_class (merchant_store_id);

-- ---------------------------------------------------------------------------
-- tax_rate : a percentage rate for a class + jurisdiction (legacy TAX_RATE)
-- ---------------------------------------------------------------------------
CREATE TABLE tax_schema.tax_rate (
    id                 UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Maps to TAX_CODE (NotEmpty). Unique per store (BR-TAX-027).
    code               VARCHAR(100)  NOT NULL,
    -- Maps to TAX_RATE.TAX_RATE (precision 7, scale 4) — percent, e.g. 5.0000 (BR-TAX-020/027).
    rate               NUMERIC(7,4)  NOT NULL,
    -- Maps to TAX_PRIORITY (default 0). Ascending order drives compound stacking (BR-TAX-017/021).
    tax_priority       INTEGER       NOT NULL DEFAULT 0,
    -- Maps to PIGGYBACK — compound (tax-on-tax) flag (BR-TAX-021).
    piggyback          BOOLEAN       NOT NULL DEFAULT FALSE,
    -- Maps to TAX_CLASS_ID (NOT NULL). Owned FK to tax_class.
    tax_class_id       UUID          NOT NULL,
    -- Maps to PARENT_ID — self-reference; only meaningful when piggyback (BR-TAX-027).
    parent_id          UUID          NULL,
    -- Maps to MERCHANT_ID (NOT NULL) — external store id (MS-03).
    merchant_store_id  BIGINT        NOT NULL,
    -- Maps to COUNTRY_ID (NOT NULL) — external reference id (MS-01).
    country_id         BIGINT        NOT NULL,
    -- Maps to ZONE_ID (nullable) — external reference id (MS-01). Structured jurisdiction.
    zone_id            BIGINT        NULL,
    -- Maps to STORE_STATE_PROV (length 100) — free-text state/province jurisdiction (BR-TAX-018).
    state_province     VARCHAR(100)  NULL,
    -- Audit (legacy AuditListener / AuditSection).
    tenant_id          UUID          NOT NULL,
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
    created_by         VARCHAR(60)   NULL,
    CONSTRAINT uq_tax_rate_store_code UNIQUE (merchant_store_id, code),
    CONSTRAINT fk_tax_rate_class  FOREIGN KEY (tax_class_id) REFERENCES tax_schema.tax_class (id),
    CONSTRAINT fk_tax_rate_parent FOREIGN KEY (parent_id)    REFERENCES tax_schema.tax_rate (id)
);
CREATE INDEX ix_tax_rate_lookup ON tax_schema.tax_rate (merchant_store_id, country_id, zone_id, tax_priority);
CREATE INDEX ix_tax_rate_state  ON tax_schema.tax_rate (merchant_store_id, country_id, state_province, tax_priority);
CREATE INDEX ix_tax_rate_class  ON tax_schema.tax_rate (tax_class_id);

-- ---------------------------------------------------------------------------
-- tax_rate_description : localized label for a tax rate (legacy TAX_RATE_DESCRIPTION)
-- ---------------------------------------------------------------------------
CREATE TABLE tax_schema.tax_rate_description (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Maps to TAX_RATE_ID — FK to tax_rate (cascade delete with parent rate).
    tax_rate_id   UUID          NOT NULL,
    -- Maps to LANGUAGE_ID — external reference id (MS-01). One description per rate per language.
    language_id   BIGINT        NOT NULL,
    -- Maps to Description.NAME — the display label used as the tax-line label (BR-TAX-020).
    name          VARCHAR(120)  NOT NULL,
    tenant_id     UUID          NOT NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_tax_rate_desc_lang UNIQUE (tax_rate_id, language_id),
    CONSTRAINT fk_tax_rate_desc_rate FOREIGN KEY (tax_rate_id)
        REFERENCES tax_schema.tax_rate (id) ON DELETE CASCADE
);
CREATE INDEX ix_tax_rate_desc_rate ON tax_schema.tax_rate_description (tax_rate_id);

-- ---------------------------------------------------------------------------
-- tax_configuration : per-store tax settings (legacy MERCHANT_CONFIGURATION JSON blob, key TAX_CONFIG)
-- One row per store. Legacy persisted ONLY tax_basis_calculation (BR-TAX-003); the two collection
-- flags are modelled with their legacy defaults.
-- ---------------------------------------------------------------------------
CREATE TABLE tax_schema.tax_configuration (
    id                                            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    -- One configuration per store (MS-03). Unique.
    merchant_store_id                             BIGINT       NOT NULL,
    -- Maps to TaxConfiguration.taxBasisCalculation. Enum: StoreAddress|ShippingAddress|BillingAddress.
    -- Default ShippingAddress (BR-TAX-002). NOTE: never actually applied at runtime (BR-TAX-007).
    tax_basis_calculation                         VARCHAR(20)  NOT NULL DEFAULT 'ShippingAddress',
    -- Maps to collectTaxIfDifferentProvinceOfStoreCountry. Legacy default true (BR-TAX-010).
    -- Legacy never persisted this flag (BR-TAX-003); default is the effective runtime value.
    collect_tax_if_different_province_of_country  BOOLEAN      NOT NULL DEFAULT TRUE,
    -- Maps to collectTaxIfDifferentCountryOfStoreCountry. Legacy default false (BR-TAX-010).
    collect_tax_if_different_country_of_country    BOOLEAN      NOT NULL DEFAULT FALSE,
    tenant_id                                     UUID         NOT NULL,
    created_at                                    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at                                    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_tax_configuration_store UNIQUE (merchant_store_id),
    CONSTRAINT ck_tax_basis CHECK (tax_basis_calculation IN ('StoreAddress','ShippingAddress','BillingAddress'))
);
```

## Entity State Model (Layer A)

`tax_class`, `tax_rate`, and `tax_rate_description` have NO lifecycle/status column — they are
configuration/reference data with plain CRUD (create/update/delete). `tax_configuration` is a
singleton-per-store settings document with no lifecycle. **No entity in this service has a state
machine**, so this section is intentionally empty (per template: omit for entities with no lifecycle).
`TaxItem` is a transient computed result (never persisted) and has no entity or lifecycle.

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-TAX-001 | A tax class code is unique within a store | tax_class | constraint | db |
| INV-TAX-002 | A tax class code is non-empty and at most 10 characters; the title is non-empty and at most 32 characters | tax_class | constraint | both |
| INV-TAX-003 | The code "DEFAULT" is reserved and may not be assigned to a user-created tax class | tax_class | constraint | app |
| INV-TAX-004 | A tax rate code is unique within a store | tax_rate | constraint | db |
| INV-TAX-005 | A tax rate value is present and stored with precision 7 and scale 4 | tax_rate | constraint | db |
| INV-TAX-006 | Every tax rate references an existing tax class within this service | tax_rate | referential | db |
| INV-TAX-007 | A tax rate's parent (compound base) reference, when present, must reference an existing tax rate | tax_rate | referential | db |
| INV-TAX-008 | A non-compound (non-piggyback) tax rate has no parent reference | tax_rate | cross-field | app |
| INV-TAX-009 | Each tax rate has at most one description per language | tax_rate_description | constraint | db |
| INV-TAX-010 | A tax class cannot be deleted while any product references it | tax_class | cross-entity | app |
| INV-TAX-011 | Each store has at most one tax configuration | tax_configuration | constraint | db |
| INV-TAX-012 | The tax basis of a configuration is one of StoreAddress, ShippingAddress, or BillingAddress | tax_configuration | constraint | both |

**Tier notes:**
- INV-TAX-001/004/005/006/007/009/011 are integrity invariants enforced by DB constraints
  (unique, FK, numeric precision, CHECK) — data integrity cannot depend on the app being the sole writer.
- INV-TAX-003 (reserved DEFAULT), INV-TAX-008 (piggyback→parent), and INV-TAX-010 (product association
  guard) are business invariants enforced in the application layer. INV-TAX-010 is cross-entity: the
  referencing side (`product.tax_class_id`) is owned by MS-04 catalog; MS-07 enforces the delete guard by
  querying catalog (BR-TAX-026), so it cannot be a local FK.
- INV-TAX-002/012 are `both`: length/format is a DB constraint and is also validated in the app for a
  clean 422 before persist.

## External / Cross-Service References (no DDL — do NOT own)

| Reference | Owner | Usage |
|-----------|-------|-------|
| `country_id` | MS-01 reference data | Jurisdiction match on tax_rate; resolved by ISO code on rate save (BR-TAX-016/017/018/027) |
| `zone_id` | MS-01 reference data | Structured jurisdiction on tax_rate (BR-TAX-016/017) |
| `language_id` | MS-01 reference data | tax_rate_description language scope (BR-TAX-017/018) |
| `merchant_store_id` | MS-03 store | Store scoping of all tax entities; store address for STOREADDRESS basis (BR-TAX-006/009) |
| product tax-class association | MS-04 catalog | Read on class delete to block deletion (BR-TAX-026); read to get an item's tax class during calculation (BR-TAX-011/012) |

## Boundary / Caller Note

The tax **calculation** engine (`POST /calculate`) is invoked by the ORDER service (MS-09) during
checkout. MS-09 is the caller; MS-07 owns the calculation. MS-07 does not persist tax results —
`TaxItem` lines are returned transiently to the caller.
