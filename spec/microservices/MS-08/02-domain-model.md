# MS-08 Shipping Service — Domain Model

**Service ID**: MS-08
**Schema**: `shipping_schema`
**Target stack**: Python / FastAPI + PostgreSQL 15+

## Data Ownership Note (READ FIRST)

In the legacy system, shipping owns **no dedicated business table**. All persistent state is stored as
per-store JSON documents in a shared `MERCHANT_CONFIGURATION` table (keyed by config key, e.g.
`SHIPPING_CONFIG`, `SUPPORTED_CNTR`, `weightBased`, and an encrypted `SHIPPING` module list), plus module
definitions in a shared `MODULE_CONFIGURATION` table.

For the modernized service we materialize these **configuration documents as first-class tables** in
`shipping_schema` (config-as-tables), each with an explicit note tying it to its legacy JSON-blob origin.
This gives the service database-per-service ownership of its configuration while preserving the legacy
document semantics. **Owned relational tables: 4** (all configuration documents; there is no transactional
shipping entity — quotes and packages are computed, not persisted, by this service).

> The shipping **quote**, **option**, **summary**, and **package** are transient computed objects (returned
> to the caller, never persisted by this service). They are represented in the API contract (04) as
> response schemas, NOT as tables.

## Core Entities

### Table: shipping_configuration

The per-store shipping configuration document. Legacy origin: `MERCHANT_CONFIGURATION` row with
`KEY = 'SHIPPING_CONFIG'`, value = JSON of the legacy `ShippingConfiguration` object.

```sql
CREATE TABLE shipping_schema.shipping_configuration (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   VARCHAR(64) NOT NULL,               -- multi-tenancy standard (store scope)
    shipping_type               VARCHAR(20) NOT NULL DEFAULT 'National',      -- Required by BR-SHIP-003/004 (National|International). Enum casing normalized to PascalCase (Concern G).
    shipping_basis_type         VARCHAR(20) NOT NULL DEFAULT 'Shipping',      -- Maps to legacy ShippingConfiguration.shippingBasisType (Billing|Shipping); read by BR-SHIP-027 (currently unused)
    shipping_option_price_type  VARCHAR(20) NOT NULL DEFAULT 'All',           -- Required by BR-SHIP-016/017/018 (Least|Highest|All)
    shipping_package_type       VARCHAR(20) NOT NULL DEFAULT 'Item',          -- Required by BR-SHIP-009 (Item|Box)
    shipping_description        VARCHAR(30) NOT NULL DEFAULT 'SHORT_DESCRIPTION', -- Maps to legacy ShippingConfiguration.shippingDescription (free-text descriptor key, not a normalized domain enum — unchanged)
    free_shipping_type          VARCHAR(20),                        -- Required by BR-SHIP-010 free-shipping scope (National|International, nullable)
    box_width                   INTEGER NOT NULL DEFAULT 0,         -- Required by BR-SHIP-023/024/025/034
    box_height                  INTEGER NOT NULL DEFAULT 0,         -- Required by BR-SHIP-023/024/025/034
    box_length                  INTEGER NOT NULL DEFAULT 0,         -- Required by BR-SHIP-023/024/025/034
    box_weight                  NUMERIC(10,2) NOT NULL DEFAULT 0,   -- Required by BR-SHIP-025/034 (rounded 2dp)
    max_weight                  NUMERIC(10,2) NOT NULL DEFAULT 0,   -- Required by BR-SHIP-023/024/025 (box max weight)
    free_shipping_enabled       BOOLEAN NOT NULL DEFAULT FALSE,     -- Required by BR-SHIP-010/033
    order_total_free_shipping   NUMERIC(12,2),                      -- Required by BR-SHIP-010/033 (threshold, nullable)
    handling_fees               NUMERIC(12,2),                      -- Required by BR-SHIP-011/033 (flat fee, nullable)
    tax_on_shipping             BOOLEAN NOT NULL DEFAULT FALSE,     -- Required by BR-SHIP-011/019/033
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(), -- Audit/multi-tenancy standard
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(), -- Audit/multi-tenancy standard
    CONSTRAINT uq_shipping_config_tenant UNIQUE (tenant_id)
);
CREATE INDEX idx_shipping_config_tenant ON shipping_schema.shipping_configuration (tenant_id);
```

### Table: supported_country

The per-store list of supported shipping destination countries (used for International eligibility).
Legacy origin: `MERCHANT_CONFIGURATION` row with `KEY = 'SUPPORTED_CNTR'`, value = JSON array of ISO codes.

```sql
CREATE TABLE shipping_schema.supported_country (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     VARCHAR(64) NOT NULL,          -- multi-tenancy standard (store scope)
    country_code  VARCHAR(2) NOT NULL,           -- Required by BR-SHIP-004 (ISO country code)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Audit standard
    CONSTRAINT uq_supported_country UNIQUE (tenant_id, country_code)
);
CREATE INDEX idx_supported_country_tenant ON shipping_schema.supported_country (tenant_id);
```

### Table: shipping_module_configuration

The per-store configured shipping providers (which providers exist, their active flag, and provider
settings). Legacy origin: encrypted `MERCHANT_CONFIGURATION` row with `KEY = 'SHIPPING'`, value =
encrypted JSON map of `IntegrationConfiguration`. The `settings` payload remains encrypted at rest
(BR-SHIP-031). Region eligibility (BR-SHIP-007) derives from module definitions; here we keep the
per-store activation + settings.

```sql
CREATE TABLE shipping_schema.shipping_module_configuration (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      VARCHAR(64) NOT NULL,         -- multi-tenancy standard (store scope)
    module_code    VARCHAR(64) NOT NULL,         -- Required by BR-SHIP-006/031 (provider code, e.g. 'weightBased')
    active         BOOLEAN NOT NULL DEFAULT FALSE,   -- Required by BR-SHIP-006 (first-active-wins selection)
    regions        JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Required by BR-SHIP-007 (region eligibility set; '*' = all)
    settings_encrypted TEXT,                      -- Required by BR-SHIP-031 (encrypted integration settings/credentials)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Audit standard
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Audit standard
    CONSTRAINT uq_shipping_module UNIQUE (tenant_id, module_code)
);
CREATE INDEX idx_shipping_module_tenant ON shipping_schema.shipping_module_configuration (tenant_id);
```

### Table: custom_weight_quote_configuration

The per-store custom weight-based provider configuration: its regions, the countries each region covers,
and the weight→price brackets. Legacy origin: `MERCHANT_CONFIGURATION` row with `KEY = 'weightBased'`,
value = JSON of `CustomShippingQuotesConfiguration` (regions[] → countries[] + quoteItems[]). Modelled as
one row per store with the full region/bracket structure held as JSONB (matching the legacy document
shape and the authoring rules in BR-SHIP-032).

```sql
CREATE TABLE shipping_schema.custom_weight_quote_configuration (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    VARCHAR(64) NOT NULL,           -- multi-tenancy standard (store scope)
    module_code  VARCHAR(64) NOT NULL DEFAULT 'weightBased',  -- Required by BR-SHIP-026 (provider code)
    active       BOOLEAN NOT NULL DEFAULT FALSE, -- Maps to legacy CustomShippingQuotesConfiguration.active
    regions      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Required by BR-SHIP-027/029/032: [{custom_region_name, countries[], quote_items:[{maximum_weight,price}]}]
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Audit standard
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Audit standard
    CONSTRAINT uq_custom_weight_tenant UNIQUE (tenant_id)
);
CREATE INDEX idx_custom_weight_tenant ON shipping_schema.custom_weight_quote_configuration (tenant_id);
```

## Cross-Boundary Reads (NOT owned by this service)

These are read via the caller/other services, NOT owned tables here (database-per-service):

| Concept | Owner service | How consumed | Used by |
|---------|---------------|--------------|---------|
| Product weight/height/length/width, virtual/shippable flags, attributes | catalog (MS-04) | passed in the quote request payload by the caller (order MS-09 / cart MS-06) | BR-SHIP-020/021/022 |
| Product final price | catalog/pricing (MS-04) | passed in / resolved by caller | BR-SHIP-008 |
| Country name / ISO reference data | reference data (MS-01) | reference lookup | BR-SHIP-015 |
| Store country of origin | store (MS-03) | request context | BR-SHIP-003/004/007/010 |
| Merchant operational log | system/logging | log write (side effect) | BR-SHIP-012/023/024 |

## Entity State Model (Layer A)

The configuration tables are mutable settings documents with **no lifecycle** (no status column, no state
machine) — omitted per template guidance. The **shipping quote** is a transient computed object, not a
persisted entity; its outcome codes are captured as response state, not a stored lifecycle:

#### shipping quote outcome (transient — computed, not persisted)
- **Outcome codes:** `OK` (options present), `NO_SHIPPING_TO_SELECTED_COUNTRY`, `NO_SHIPPING_MODULE_CONFIGURED`, `ERROR` (external/legacy status codes — kept UPPER_CASE), plus `free_shipping` (no options, early return)
- These are response values produced by BR-SHIP-003/004/005/006/007/010/012/013. No persisted transition
  exists — there is no table to enforce a state machine against, so no closed-machine section applies.

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-SHIP-001 | A store has at most one shipping configuration document | shipping_configuration | constraint | db |
| INV-SHIP-002 | A store's shipping type is one of National or International | shipping_configuration | constraint | both |
| INV-SHIP-003 | A store's shipping option price type is one of Least, Highest, or All | shipping_configuration | constraint | both |
| INV-SHIP-004 | A store's shipping package type is one of Item or Box | shipping_configuration | constraint | both |
| INV-SHIP-005 | For box packaging, box volume (width×length×height) and max weight must both be greater than zero | shipping_configuration | cross-field | app |
| INV-SHIP-006 | A supported destination country appears at most once per store | supported_country | constraint | db |
| INV-SHIP-007 | A provider code is configured at most once per store | shipping_module_configuration | constraint | db |
| INV-SHIP-008 | Within a custom weight-based region, each maximum-weight bracket is unique and every bracket weight is greater than zero | custom_weight_quote_configuration | constraint | app |
| INV-SHIP-009 | Custom weight-based region names are unique per store, and a country appears at most once per region | custom_weight_quote_configuration | constraint | app |

**Invariant count: 9.**

Notes:
- INV-SHIP-001/006/007 are enforced by the DB unique constraints declared above (`db`).
- INV-SHIP-002/003/004 are enforceable both by a DB CHECK constraint and by the application enum
  validation (`both`); the API contract enums are the app-tier enforcement.
- INV-SHIP-005/008/009 involve JSONB document structure / cross-field computation and are enforced in the
  domain layer (`app`) — they mirror the legacy controller validators (BR-SHIP-023, BR-SHIP-032).

No `### Database Logic Objects` section: no business logic was placed in the DB tier for this service
(app-first default). Integrity invariants INV-SHIP-001/006/007 are plain UNIQUE constraints on the base
DDL above, not procedural DB objects.
