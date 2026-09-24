# Customer Service (MS-05) — Domain Model

**Service ID**: MS-05 · **Schema**: `customer_schema` · **Target**: PostgreSQL 15+ (FastAPI/SQLAlchemy)

**Owned tables (8):** `customer` (embedded billing_*/delivery_* inline columns), `customer_group`, `customer_option`, `customer_option_description`, `customer_option_value`, `customer_option_value_description`, `customer_option_set`, `customer_attribute`.

**External references (no DDL here — id only):** `country`/`zone`/`language` (MS-01 reference data), `group`/`permission` (MS-02 identity). Foreign keys to these are modeled as plain id columns (no cross-service FK).

All identifiers are UUID in the target (legacy used table-sequencer BIGINT). Standard infrastructure columns `tenant_id`, `store_id`, `created_at`, `updated_at` are multi-tenancy/audit standard.

---

## Core Entities

```sql
-- ============================================================
-- customer : shopper identity + embedded billing & delivery address (BR-CUST-*)
-- ============================================================
CREATE TABLE customer (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id               INTEGER NOT NULL,                 -- Maps to CUSTOMER.MERCHANT_ID (external MS-01 store id)
    tenant_id              VARCHAR(64) NOT NULL,             -- Multi-tenancy standard
    user_name              VARCHAR(96),                      -- Maps to CUSTOMER.CUSTOMER_NICK (BR-CUST-001/005)
    email_address          VARCHAR(96) NOT NULL,             -- Maps to CUSTOMER.CUSTOMER_EMAIL_ADDRESS (BR-CUST-011/017)
    password               VARCHAR(255) NOT NULL,            -- Maps to CUSTOMER.CUSTOMER_PASSWORD; widened per BR-CUST-004 note
    anonymous              BOOLEAN NOT NULL DEFAULT TRUE,    -- Maps to CUSTOMER.CUSTOMER_ANONYMOUS (BR-CUST-010)
    gender                 CHAR(1) NOT NULL DEFAULT 'M'      -- Maps to CUSTOMER.CUSTOMER_GENDER (BR-CUST-027; default configurable in target)
                             CHECK (gender IN ('M','F')),
    date_of_birth          TIMESTAMP,                        -- Maps to CUSTOMER.CUSTOMER_DOB
    company                VARCHAR(100),                     -- Maps to CUSTOMER.CUSTOMER_COMPANY
    language_id            INTEGER NOT NULL,                 -- Maps to CUSTOMER.LANGUAGE_ID (external MS-01; BR-CUST-014)
    -- embedded billing (BR-CUST-011/013/019) — Maps to CUSTOMER.BILLING_*
    billing_first_name     VARCHAR(64) NOT NULL,
    billing_last_name      VARCHAR(64) NOT NULL,
    billing_company        VARCHAR(100),
    billing_street_address VARCHAR(256),
    billing_city           VARCHAR(100),
    billing_postcode       VARCHAR(20),
    billing_state          VARCHAR(100),
    billing_telephone      VARCHAR(32),
    billing_country_id     INTEGER NOT NULL,                 -- external MS-01 country id (billing country not-null)
    billing_zone_id        INTEGER,                          -- external MS-01 zone id (nullable; BR-CUST-019)
    -- embedded delivery (BR-CUST-012/013/019) — Maps to CUSTOMER.DELIVERY_* (all nullable)
    delivery_first_name    VARCHAR(64),
    delivery_last_name     VARCHAR(64),
    delivery_company       VARCHAR(100),
    delivery_street_address VARCHAR(256),
    delivery_city          VARCHAR(100),
    delivery_postcode      VARCHAR(20),
    delivery_state         VARCHAR(100),
    delivery_telephone     VARCHAR(32),
    delivery_country_id    INTEGER,
    delivery_zone_id       INTEGER,
    created_at             TIMESTAMP NOT NULL DEFAULT now(),
    updated_at             TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_customer_username_store UNIQUE (store_id, user_name)   -- INV-CUST-002 (BR-CUST-002; DB constraint added in target)
);
CREATE INDEX idx_customer_store ON customer (store_id);
CREATE INDEX idx_customer_email ON customer (store_id, email_address);

-- ============================================================
-- customer_group : shopper ↔ external group membership (BR-CUST-007/023/026)
-- ============================================================
CREATE TABLE customer_group (
    customer_id UUID NOT NULL REFERENCES customer(id) ON DELETE CASCADE,  -- INV-CUST-012
    group_id    INTEGER NOT NULL,                                          -- external MS-02 group id
    PRIMARY KEY (customer_id, group_id)
);

-- ============================================================
-- customer_option : merchant-defined custom field (BR-CUSTOPT-001/002/003/015)
-- ============================================================
CREATE TABLE customer_option (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id            INTEGER NOT NULL,                     -- Maps to CUSTOMER_OPTION.MERCHANT_ID
    tenant_id           VARCHAR(64) NOT NULL,
    code                VARCHAR(100) NOT NULL                 -- Maps to CUSTOMER_OPTION.CUSTOMER_OPT_CODE (BR-CUSTOPT-002)
                          CHECK (code ~ '^[a-zA-Z0-9_]*$'),   -- BR-CUSTOPT-002 (code format)
    option_type         VARCHAR(10),                          -- Maps to CUSTOMER_OPTION.CUSTOMER_OPTION_TYPE (Text/Radio/Select/Checkbox)
    sort_order          INTEGER NOT NULL DEFAULT 0,
    active              BOOLEAN NOT NULL DEFAULT FALSE,       -- Maps to CUSTOMER_OPT_ACTIVE (BR-CUSTOPT-015)
    public_option       BOOLEAN NOT NULL DEFAULT FALSE,       -- Maps to CUSTOMER_OPT_PUBLIC (BR-CUSTOPT-015)
    created_at          TIMESTAMP NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_customer_option_code UNIQUE (store_id, code)   -- INV-CUSTOPT-001 (BR-CUSTOPT-001)
);

-- ============================================================
-- customer_option_description : per-language option name (BR-CUSTOPT-003)
-- ============================================================
CREATE TABLE customer_option_description (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_option_id UUID NOT NULL REFERENCES customer_option(id) ON DELETE CASCADE,
    language_id        INTEGER NOT NULL,                      -- external MS-01 language id
    name               VARCHAR(255) NOT NULL,                 -- Required by BR-CUSTOPT-003
    CONSTRAINT uq_option_desc_lang UNIQUE (customer_option_id, language_id)
);

-- ============================================================
-- customer_option_value : selectable value for an option (BR-CUSTOPT-004/005/006)
-- ============================================================
CREATE TABLE customer_option_value (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id     INTEGER NOT NULL,                            -- Maps to CUSTOMER_OPTION_VALUE.MERCHANT_ID
    tenant_id    VARCHAR(64) NOT NULL,
    code         VARCHAR(100) NOT NULL                        -- Maps to CUSTOMER_OPT_VAL_CODE (BR-CUSTOPT-005)
                   CHECK (code ~ '^[a-zA-Z0-9_]*$'),          -- BR-CUSTOPT-005 (code format)
    sort_order   INTEGER NOT NULL DEFAULT 0,
    image        VARCHAR(255),                                -- Maps to CUSTOMER_OPT_VAL_IMAGE
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_customer_option_value_code UNIQUE (store_id, code)   -- INV-CUSTOPT-002 (BR-CUSTOPT-004)
);

-- ============================================================
-- customer_option_value_description : per-language value name (BR-CUSTOPT-006)
-- ============================================================
CREATE TABLE customer_option_value_description (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_option_value_id UUID NOT NULL REFERENCES customer_option_value(id) ON DELETE CASCADE,
    language_id              INTEGER NOT NULL,
    name                     VARCHAR(255) NOT NULL,           -- Required by BR-CUSTOPT-006
    CONSTRAINT uq_value_desc_lang UNIQUE (customer_option_value_id, language_id)
);

-- ============================================================
-- customer_option_set : allowed (option, value) binding (BR-CUSTOPT-007/008)
-- ============================================================
CREATE TABLE customer_option_set (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id                 INTEGER NOT NULL,
    tenant_id                VARCHAR(64) NOT NULL,
    customer_option_id       UUID NOT NULL REFERENCES customer_option(id) ON DELETE CASCADE,        -- INV-CUSTOPT-011 (cascade)
    customer_option_value_id UUID NOT NULL REFERENCES customer_option_value(id) ON DELETE CASCADE,  -- INV-CUSTOPT-011 (cascade)
    sort_order               INTEGER NOT NULL DEFAULT 0,
    created_at               TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_option_set_pair UNIQUE (customer_option_id, customer_option_value_id)  -- INV-CUSTOPT-008 (BR-CUSTOPT-008)
);

-- ============================================================
-- customer_attribute : a shopper's stored value for an option (BR-CUSTOPT-010/011/012)
-- ============================================================
CREATE TABLE customer_attribute (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id              UUID NOT NULL REFERENCES customer(id) ON DELETE CASCADE,   -- INV-CUST-013 (BR-CUST-028)
    customer_option_id       UUID NOT NULL REFERENCES customer_option(id) ON DELETE CASCADE,        -- INV-CUSTOPT-011 (BR-CUSTOPT-013)
    customer_option_value_id UUID NOT NULL REFERENCES customer_option_value(id) ON DELETE CASCADE,  -- INV-CUSTOPT-011 (BR-CUSTOPT-014)
    text_value               VARCHAR(4000),                   -- Maps to CUSTOMER_ATTR_TXT_VAL (BR-CUSTOPT-011)
    created_at               TIMESTAMP NOT NULL DEFAULT now(),
    updated_at               TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_attribute_option_customer UNIQUE (customer_option_id, customer_id)   -- INV-CUSTOPT-003 (one attribute per option per shopper)
);
CREATE INDEX idx_attribute_customer ON customer_attribute (customer_id);
```

## Entity State Model (Layer A)

Reference and option/value/set entities are configuration data with no lifecycle. Only the shopper has a lifecycle (the anonymous↔registered flag; there is no separate status column in the legacy).

#### customer lifecycle
- **States:** Anonymous (initial), Registered (terminal-for-identity), Deleted (terminal)
- **Transitions:**
  | From | To | Trigger (BR-ID) | Guard (precondition) |
  |------|----|-----------------|----------------------|
  | Anonymous | Registered | BR-CUST-010 | a real (encoded) password is set |
  | Anonymous | Deleted | BR-CUST-028 | delete request within owning store |
  | Registered | Deleted | BR-CUST-028 | delete request within owning store |

- Anonymous is the initial state (`anonymous = true` by default). Registered is reached by BR-CUST-010. Deleted is terminal (hard delete; row removed) and has no outgoing transitions. Every state is reachable; the only non-terminal state (Anonymous) has outgoing transitions; Registered may still be Deleted.

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-CUST-001 | Every shopper has a store and a language | customer | constraint | both |
| INV-CUST-002 | A username is unique within a store | customer | constraint | both |
| INV-CUST-003 | A shopper password is stored only in encoded form (never clear text) | customer | constraint | app |
| INV-CUST-004 | A shopper's gender, when set, is Male or Female | customer | constraint | db |
| INV-CUST-005 | A billing address has first name, last name and a country | customer | cross-field | both |
| INV-CUST-006 | For an address, a zone and a free-text state are mutually exclusive | customer | cross-field | app |
| INV-CUST-012 | Removing a shopper removes that shopper's group memberships | customer_group | cross-entity | db |
| INV-CUST-013 | Removing a shopper removes that shopper's attributes | customer_attribute | cross-entity | both |
| INV-CUSTOPT-001 | A customer option code is unique within a store | customer_option | constraint | both |
| INV-CUSTOPT-002 | A customer option value code is unique within a store | customer_option_value | constraint | both |
| INV-CUSTOPT-003 | A shopper holds at most one attribute per option | customer_attribute | constraint | both |
| INV-CUSTOPT-008 | An (option, value) binding is unique within a store | customer_option_set | constraint | both |
| INV-CUSTOPT-011 | Removing an option or value removes dependent attributes and bindings | customer_attribute | cross-entity | both |

**Invariant count: 13.**

> No logic is placed in the DB tier beyond integrity constraints/cascades above; there is no `### Database Logic Objects` section (default app-tier). Integrity invariants are enforced via the CHECK/UNIQUE/ON DELETE CASCADE clauses in the DDL above.

## Extensibility Signals (Layer B)

The customer option / option value / option set / attribute entities ARE the customer-configurability engine: a merchant defines per-store custom customer fields (type Text/Radio/Select/Checkbox), their allowed values and (option,value) bindings, and their active/public visibility; shoppers then fill them as attributes (BR-CUSTOPT-*). This mirrors the product-options engine of the catalog service.
