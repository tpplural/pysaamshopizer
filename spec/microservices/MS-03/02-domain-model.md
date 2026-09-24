# MS-03 merchant-store — Domain Model

**Schema:** `merchant_store` · **Target DB:** PostgreSQL · **Multi-tenancy anchor:** this service's `merchant_store.id` / `merchant_store.store_code` is the tenant key every other service scopes by.

Reference data (country, zone, currency, language) is owned by **MS-01 reference-data**. Those values are stored here as **cross-reference codes (xref), NOT foreign keys** — database-per-service means MS-03 cannot FK into MS-01's tables. Codes are validated via REST on write (BR-MS-FIELD-001, BR-MS-PERS-002).

## Core Entities

```sql
-- =====================================================================
-- merchant_store : the tenant/store record and its per-store config
-- Maps to legacy MERCHANT_STORE (MerchantStore.java)
-- =====================================================================
CREATE TABLE merchant_store (
    id                        BIGINT       NOT NULL,
        -- Maps to MERCHANT_STORE.MERCHANT_ID; allocator-assigned (BR-MS-DFLT-004)
    store_code                VARCHAR(100) NOT NULL,
        -- Maps to MERCHANT_STORE.STORE_CODE; unique tenant key, regex ^[a-zA-Z0-9_]*$ (BR-MS-IDENT-001)
    store_name                VARCHAR(100) NOT NULL,
        -- Maps to MERCHANT_STORE.STORE_NAME (BR-MS-FIELD-001)
    store_phone               VARCHAR(50)  NOT NULL,
        -- Maps to MERCHANT_STORE.STORE_PHONE (BR-MS-FIELD-001)
    store_email               VARCHAR(60)  NOT NULL,
        -- Maps to MERCHANT_STORE.STORE_EMAIL; valid email (BR-MS-FIELD-001, notification target BR-MS-LIFE-001)
    store_address             VARCHAR(255),
        -- Maps to MERCHANT_STORE.STORE_ADDRESS (optional)
    store_city                VARCHAR(100) NOT NULL,
        -- Maps to MERCHANT_STORE.STORE_CITY (BR-MS-FIELD-001)
    store_postal_code         VARCHAR(15)  NOT NULL,
        -- Maps to MERCHANT_STORE.STORE_POSTAL_CODE (BR-MS-FIELD-001)
    country_iso               VARCHAR(3)   NOT NULL,
        -- xref MS-01 reference-data COUNTRY.iso; NOT a FK (BR-MS-FIELD-001/002)
    zone_code                 VARCHAR(10),
        -- xref MS-01 ZONE.code; nullable — used when country has zones (BR-MS-FIELD-002)
    store_state_province      VARCHAR(100),
        -- Maps to MERCHANT_STORE.STORE_STATE_PROV; free-text state when no zone (BR-MS-FIELD-002)
    default_language_code     VARCHAR(5)   NOT NULL,
        -- xref MS-01 LANGUAGE.code; store's default locale (BR-MS-FIELD-001)
    currency_code             VARCHAR(3)   NOT NULL,
        -- xref MS-01 CURRENCY.code; billing currency (BR-MS-FIELD-001)
    weight_unit               VARCHAR(5)   NOT NULL DEFAULT 'LB',
        -- Maps to MERCHANT_STORE.WEIGHTUNITCODE; one of LB, KG (BR-MS-DFLT-001)
    dimension_unit            VARCHAR(5)   NOT NULL DEFAULT 'IN',
        -- Maps to MERCHANT_STORE.SEIZEUNITCODE (legacy "seize" misspelling); one of CM, IN (BR-MS-DFLT-001)
    in_business_since         DATE,
        -- Maps to MERCHANT_STORE.IN_BUSINESS_SINCE; defaults to creation date (BR-MS-DFLT-002)
    use_cache                 BOOLEAN      NOT NULL DEFAULT FALSE,
        -- Maps to MERCHANT_STORE.USE_CACHE (BR-MS-DFLT-003)
    currency_format_national  BOOLEAN      NOT NULL DEFAULT FALSE,
        -- Maps to MERCHANT_STORE.CURRENCY_FORMAT_NATIONAL (BR-MS-DFLT-003)
    store_template            VARCHAR(25),
        -- Maps to MERCHANT_STORE.STORE_TEMPLATE; theme, set only via branding (BR-MS-BRAND-002)
    invoice_template          VARCHAR(25),
        -- Maps to MERCHANT_STORE.INVOICE_TEMPLATE (Required by BR-MS-BRAND-002 sibling: per-store invoice theme)
    domain_name               VARCHAR(80),
        -- Maps to MERCHANT_STORE.DOMAIN_NAME (Required by BR-MS-FIELD/DFLT config surface: per-store domain)
    continue_shopping_url      VARCHAR(150),
        -- Maps to MERCHANT_STORE.CONTINUESHOPPINGURL (per-store config surface)
    store_logo                VARCHAR(100),
        -- Maps to MERCHANT_STORE.STORE_LOGO; filename only, bytes in MS-11 (BR-MS-BRAND-001)
    is_default                BOOLEAN      NOT NULL DEFAULT FALSE,
        -- Required by BR-MS-IDENT-003: marks the reserved DEFAULT store hidden from listings
    tenant_id                 BIGINT,
        -- Audit/multi-tenancy standard (self-referential tenant anchor = id for real stores)
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT now(),
        -- Audit/multi-tenancy standard
    updated_at                TIMESTAMPTZ  NOT NULL DEFAULT now(),
        -- Audit/multi-tenancy standard
    created_by                VARCHAR(100),
        -- Audit/multi-tenancy standard
    CONSTRAINT pk_merchant_store PRIMARY KEY (id),
    CONSTRAINT uq_merchant_store_code UNIQUE (store_code),
    CONSTRAINT ck_merchant_store_code_format CHECK (store_code ~ '^[a-zA-Z0-9_]*$'),
        -- Enforces BR-MS-IDENT-001 regex at the DB tier
    CONSTRAINT ck_merchant_store_weight_unit CHECK (weight_unit IN ('LB','KG')),
        -- Enforces BR-MS-DFLT-001 weight enum
    CONSTRAINT ck_merchant_store_dimension_unit CHECK (dimension_unit IN ('CM','IN')),
        -- Enforces BR-MS-DFLT-001 dimension enum
    CONSTRAINT ck_merchant_store_location CHECK (zone_code IS NOT NULL OR store_state_province IS NOT NULL)
        -- Enforces BR-MS-FIELD-002: a zone OR a free-text state must be present
);

CREATE INDEX ix_merchant_store_country ON merchant_store (country_iso);
CREATE INDEX ix_merchant_store_currency ON merchant_store (currency_code);
CREATE INDEX ix_merchant_store_default ON merchant_store (is_default);

-- =====================================================================
-- merchant_language : the set of languages a store supports (>= 1)
-- Maps to legacy MERCHANT_LANGUAGE join table (MerchantStore.languages M2M)
-- =====================================================================
CREATE TABLE merchant_language (
    id             BIGINT       NOT NULL,
        -- surrogate PK for the association row
    merchant_id    BIGINT       NOT NULL,
        -- FK to merchant_store.id (same-service FK, allowed)
    language_code  VARCHAR(5)   NOT NULL,
        -- xref MS-01 LANGUAGE.code; a supported locale (BR-MS-FIELD-001)
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
        -- Audit/multi-tenancy standard
    CONSTRAINT pk_merchant_language PRIMARY KEY (id),
    CONSTRAINT fk_merchant_language_store FOREIGN KEY (merchant_id)
        REFERENCES merchant_store (id) ON DELETE CASCADE,
    CONSTRAINT uq_merchant_language UNIQUE (merchant_id, language_code)
        -- a language appears at most once per store
);

CREATE INDEX ix_merchant_language_store ON merchant_language (merchant_id);
```

## Cross-Reference (xref) Codes — resolved via MS-01, NOT foreign keys

| Column | xref target (MS-01 reference-data) | Resolved by | Rule |
|--------|-----------------------------------|-------------|------|
| `merchant_store.country_iso` | `COUNTRY.iso` | REST validate on write | BR-MS-FIELD-001/002 |
| `merchant_store.zone_code` | `ZONE.code` | REST validate on write (nullable) | BR-MS-FIELD-002 |
| `merchant_store.currency_code` | `CURRENCY.code` | REST validate on write | BR-MS-FIELD-001 |
| `merchant_store.default_language_code` | `LANGUAGE.code` | REST validate on write | BR-MS-FIELD-001 |
| `merchant_language.language_code` | `LANGUAGE.code` | REST validate on write | BR-MS-FIELD-001 |

## Entity State Model (Layer A)

### merchant_store lifecycle
- **States:** Transient (initial — no id yet), Active (persistent), Decommissioning, Decommissioned (terminal)
- **Transitions:**

  | From | To | Trigger (BR-ID) | Guard (precondition) |
  |------|----|-----------------|----------------------|
  | Transient | Active | BR-MS-PERS-001 / BR-MS-DFLT-004 | all mandatory fields valid; code unique; id allocated |
  | Active | Active | BR-MS-PERS-001 | editing own store (BR-MS-LIFE-004) |
  | Active | Decommissioning | BR-MS-LIFE-002 | caller is superadmin (BR-MS-LIFE-003); store is not the reserved DEFAULT |
  | Decommissioning | Decommissioned | BR-MS-LIFE-002 | all `merchant.deleted` consumers acknowledged |

**Closed-machine rules (verified at 4a):**
- Transient is the only initial state; Decommissioned is the only terminal state (no outgoing transitions).
- Every non-terminal state (Transient, Active, Decommissioning) has at least one outgoing transition.
- Decommissioned is reachable: Transient → Active → Decommissioning → Decommissioned.
- No operation moves a store to a state outside this model. The reserved DEFAULT store never leaves Active (it cannot be deleted — BR-MS-IDENT-003 / BR-MS-LIFE-002 guard).

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-MS-001 | A store code is unique and contains only letters, digits, and underscores | merchant_store | constraint | both |
| INV-MS-002 | A store has a resolvable location: a zone or a free-text state/province | merchant_store | cross-field | both |
| INV-MS-003 | A store's weight unit is LB or KG and its dimension unit is CM or IN | merchant_store | constraint | both |
| INV-MS-004 | A store supports at least one language | merchant_store + merchant_language | cross-entity | app |
| INV-MS-005 | A language appears at most once among a store's supported languages | merchant_language | constraint | db |

**Tier notes:**
- INV-MS-001, INV-MS-002, INV-MS-003, INV-MS-005 are integrity invariants enforced at the DB tier via the CHECK/UNIQUE constraints in the DDL above (`ck_merchant_store_code_format`, `ck_merchant_store_location`, `ck_merchant_store_weight_unit`, `ck_merchant_store_dimension_unit`, `uq_merchant_language`) — data integrity cannot depend on the app being the sole writer.
- INV-MS-004 (at-least-one-language) is enforced in the domain layer on save (`app`) — a "no language rows" state cannot be expressed as a single-row CHECK without a trigger, and the business rule is validated before persist (BR-MS-FIELD-001).

_No `### Database Logic Objects` section: all logic for MS-03 is app-tier except the mandatory-DB integrity invariants above, which are plain CHECK/UNIQUE constraints already inline in the Core Entities DDL (no views, functions, procedures, or triggers required)._
