# MS-04 Catalog Service — Domain Model

**Service ID:** MS-04
**Database schema:** `catalog_schema`
**Target DDL dialect:** PostgreSQL 15+

Column names are derived from the legacy Shopizer schema (traceable to source tables/columns). Every table
is owned by the catalog service. `PRODUCT_CATEGORY` is the product↔category join. Standard multi-tenancy
and audit columns (`merchant_id`, `created_at`, `updated_at`, `created_by`) are infrastructure-standard.

## Core Entities

```sql
-- ============================ PRODUCT TYPE (reference) ============================
CREATE TABLE product_type (
    id                BIGINT PRIMARY KEY,
    code              VARCHAR(100) NOT NULL,                 -- legacy PRD_TYPE_CODE (e.g. GENERAL)
    allow_add_to_cart BOOLEAN      NOT NULL DEFAULT TRUE,    -- legacy PRD_TYPE_ADD_TO_CART (BR-CATPROD-024)
    merchant_id       BIGINT       NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ,
    CONSTRAINT uq_product_type_code UNIQUE (merchant_id, code)
);

-- ============================ MANUFACTURER ============================
CREATE TABLE manufacturer (
    id           BIGINT PRIMARY KEY,
    code         VARCHAR(100) NOT NULL,
    sort_order   INTEGER      NOT NULL DEFAULT 0,            -- BR-CATMAN-006
    merchant_id  BIGINT       NOT NULL,                      -- store scoping (BR-CATMAN-003)
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ,
    CONSTRAINT uq_manufacturer_code UNIQUE (merchant_id, code)
);

CREATE TABLE manufacturer_description (
    id              BIGINT PRIMARY KEY,
    manufacturer_id BIGINT       NOT NULL REFERENCES manufacturer(id) ON DELETE CASCADE,
    language_id     BIGINT       NOT NULL,
    name            VARCHAR(120) NOT NULL,
    description     TEXT,
    CONSTRAINT uq_manufacturer_desc_lang UNIQUE (manufacturer_id, language_id)  -- BR-CATMAN-007
);

-- ============================ CATEGORY ============================
CREATE TABLE category (
    id              BIGINT PRIMARY KEY,
    code            VARCHAR(100) NOT NULL,                   -- BR-CATCAT-004
    parent_id       BIGINT REFERENCES category(id) ON DELETE CASCADE,  -- BR-CATCAT-012 subtree cascade
    lineage         VARCHAR(255) NOT NULL DEFAULT '/',       -- BR-CATCAT-001/002/005 tree path
    depth           INTEGER      NOT NULL DEFAULT 0,         -- BR-CATCAT-001/002
    sort_order      INTEGER      NOT NULL DEFAULT 0,         -- BR-CATCAT-014
    visible         BOOLEAN      NOT NULL DEFAULT TRUE,      -- BR-CATCAT-014
    category_status BOOLEAN      NOT NULL DEFAULT TRUE,      -- BR-CATCAT-014
    merchant_id     BIGINT       NOT NULL,                   -- BR-CATCAT-009
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ,
    CONSTRAINT uq_category_code UNIQUE (merchant_id, code)   -- BR-CATCAT-003
);
CREATE INDEX ix_category_lineage ON category (merchant_id, lineage);  -- lineage-prefix subtree queries

CREATE TABLE category_description (
    id            BIGINT PRIMARY KEY,
    category_id   BIGINT       NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    language_id   BIGINT       NOT NULL,
    name          VARCHAR(120) NOT NULL,
    description   TEXT,
    meta_title    VARCHAR(120),
    meta_keywords VARCHAR(255),
    meta_description VARCHAR(255),
    sef_url       VARCHAR(120),
    highlight     VARCHAR(120),
    CONSTRAINT uq_category_desc_lang UNIQUE (category_id, language_id)
);

-- ============================ PRODUCT (aggregate root) ============================
CREATE TABLE product (
    id                 BIGINT PRIMARY KEY,
    sku                VARCHAR(100) NOT NULL,                -- BR-CATPROD-008 (^[a-zA-Z0-9_]*$)
    manufacturer_id    BIGINT REFERENCES manufacturer(id),
    product_type_id    BIGINT REFERENCES product_type(id),
    tax_class_id       BIGINT,                               -- external (tax service); no DDL here
    available          BOOLEAN      NOT NULL DEFAULT TRUE,   -- BR-CATPROD-009/010
    date_available     TIMESTAMPTZ  NOT NULL DEFAULT now(),  -- BR-CATPROD-009/010
    product_virtual    BOOLEAN      NOT NULL DEFAULT FALSE,  -- BR-CATPROD-017/018
    product_ship       BOOLEAN      NOT NULL DEFAULT FALSE,
    product_free       BOOLEAN      NOT NULL DEFAULT FALSE,
    product_length     NUMERIC(19,4),
    product_width      NUMERIC(19,4),
    product_height     NUMERIC(19,4),
    product_weight     NUMERIC(19,4),
    review_avg         NUMERIC(19,4),                        -- BR-CATREV-001
    review_count       INTEGER,                              -- BR-CATREV-001
    quantity_ordered   INTEGER,
    sort_order         INTEGER      NOT NULL DEFAULT 0,      -- BR-CATPROD-009
    merchant_id        BIGINT       NOT NULL,                -- BR-CATPROD-025
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ,
    CONSTRAINT chk_product_sku_format CHECK (sku ~ '^[a-zA-Z0-9_]*$' AND sku <> '')  -- BR-CATPROD-008
);
CREATE INDEX ix_product_visibility ON product (merchant_id, available, date_available);  -- BR-CATPROD-010 hot path
CREATE INDEX ix_product_manufacturer ON product (manufacturer_id);  -- BR-CATMAN-002 count

CREATE TABLE product_description (
    id            BIGINT PRIMARY KEY,
    product_id    BIGINT       NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    language_id   BIGINT       NOT NULL,
    name          VARCHAR(120) NOT NULL,
    description   TEXT,
    meta_title    VARCHAR(120),
    meta_keywords VARCHAR(255),
    meta_description VARCHAR(255),
    sef_url       VARCHAR(120),
    CONSTRAINT uq_product_desc_lang UNIQUE (product_id, language_id)
);

CREATE TABLE product_category (                              -- product↔category join (BR-CATPROD-014, BR-CATCAT-013)
    product_id  BIGINT NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

CREATE TABLE product_availability (
    id                     BIGINT PRIMARY KEY,
    product_id             BIGINT      NOT NULL REFERENCES product(id) ON DELETE CASCADE,  -- BR-CATPROD-004 orphan removal
    region                 VARCHAR(4)  NOT NULL DEFAULT '*',   -- BR-CATPROD-015 ALL_REGIONS; BR-CATPRICE-002
    region_variant         VARCHAR(4),
    status                 BOOLEAN     NOT NULL DEFAULT TRUE,  -- BR-CATPROD-015
    quantity               INTEGER     NOT NULL DEFAULT 0,     -- BR-CATPROD-015/026
    quantity_ord_min       INTEGER     NOT NULL DEFAULT 0,     -- BR-CATPROD-015/026
    quantity_ord_max       INTEGER     NOT NULL DEFAULT 0,     -- BR-CATPROD-015/026
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_availability_product ON product_availability (product_id, region);

CREATE TABLE product_price (
    id                          BIGINT PRIMARY KEY,
    product_availability_id     BIGINT      NOT NULL REFERENCES product_availability(id) ON DELETE CASCADE,
    code                        VARCHAR(100) NOT NULL DEFAULT 'base',   -- BR-CATPRICE-014 (^[a-zA-Z0-9_]*$)
    default_price               BOOLEAN     NOT NULL DEFAULT FALSE,     -- BR-CATPRICE-001
    price_type                  VARCHAR(20) NOT NULL DEFAULT 'ONE_TIME',-- BR-CATPRICE-014 (ONE_TIME|MONTHLY)
    amount                      NUMERIC(19,4) NOT NULL DEFAULT 0,       -- BR-CATPRICE-001/007
    special_amount              NUMERIC(19,4),                          -- BR-CATPRICE-004/005/006/008
    special_start_date          TIMESTAMPTZ,                            -- BR-CATPRICE-004/005/011
    special_end_date            TIMESTAMPTZ,                            -- BR-CATPRICE-004/005/011
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_price_code_format CHECK (code ~ '^[a-zA-Z0-9_]*$' AND code <> '')  -- BR-CATPRICE-014
);
CREATE INDEX ix_price_availability_default ON product_price (product_availability_id, default_price);

CREATE TABLE product_price_description (
    id          BIGINT PRIMARY KEY,
    product_price_id BIGINT   NOT NULL REFERENCES product_price(id) ON DELETE CASCADE,
    language_id BIGINT        NOT NULL,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    CONSTRAINT uq_price_desc_lang UNIQUE (product_price_id, language_id)
);

CREATE TABLE product_digital (
    id          BIGINT PRIMARY KEY,
    product_id  BIGINT       NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    file_name   VARCHAR(255) NOT NULL,                       -- BR-CATPROD-017
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_digital_product_file UNIQUE (product_id, file_name)  -- BR-CATPROD-019
);

CREATE TABLE product_relationship (
    id           BIGINT PRIMARY KEY,
    code         VARCHAR(100) NOT NULL,                      -- BR-CATPROD-022 group code
    product_id   BIGINT REFERENCES product(id) ON DELETE CASCADE,  -- NULL for a group header (BR-CATPROD-022)
    related_product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    active       BOOLEAN     NOT NULL DEFAULT TRUE,          -- BR-CATPROD-023
    merchant_id  BIGINT      NOT NULL,                       -- BR-CATPROD-022 store scoping
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_relationship_group ON product_relationship (merchant_id, code, active);

-- ============================ OPTIONS / VALUES / ATTRIBUTES ============================
CREATE TABLE product_option (
    id                 BIGINT PRIMARY KEY,
    code               VARCHAR(100) NOT NULL,                -- BR-CATOPT-003 (^[a-zA-Z0-9_]*$)
    option_type        VARCHAR(20),                          -- BR-CATOPT-017/022 (Text|Radio|Select|Checkbox)
    read_only          BOOLEAN     NOT NULL DEFAULT FALSE,
    merchant_id        BIGINT      NOT NULL,                 -- BR-CATOPT-006
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_option_code UNIQUE (merchant_id, code),    -- BR-CATOPT-004
    CONSTRAINT chk_option_code_format CHECK (code ~ '^[a-zA-Z0-9_]*$' AND code <> '')  -- BR-CATOPT-003
);

CREATE TABLE product_option_description (
    id               BIGINT PRIMARY KEY,
    product_option_id BIGINT      NOT NULL REFERENCES product_option(id) ON DELETE CASCADE,
    language_id      BIGINT       NOT NULL,
    name             VARCHAR(120) NOT NULL,
    description      TEXT,
    CONSTRAINT uq_option_desc_lang UNIQUE (product_option_id, language_id)  -- BR-CATOPT-007
);

CREATE TABLE product_option_value (
    id                       BIGINT PRIMARY KEY,
    code                     VARCHAR(100) NOT NULL,          -- BR-CATOPT-005
    display_only             BOOLEAN     NOT NULL DEFAULT FALSE,  -- BR-CATOPT-017/027
    merchant_id              BIGINT      NOT NULL,           -- BR-CATOPT-006
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_option_value_code UNIQUE (merchant_id, code),  -- BR-CATOPT-005
    CONSTRAINT chk_option_value_code_format CHECK (code ~ '^[a-zA-Z0-9_]*$' AND code <> '')
);

CREATE TABLE product_option_value_description (
    id                       BIGINT PRIMARY KEY,
    product_option_value_id  BIGINT      NOT NULL REFERENCES product_option_value(id) ON DELETE CASCADE,
    language_id              BIGINT       NOT NULL,
    name                     VARCHAR(120) NOT NULL,          -- BR-CATOPT-018 truncated to 15 for text values
    description              TEXT,
    CONSTRAINT uq_option_value_desc_lang UNIQUE (product_option_value_id, language_id)  -- BR-CATOPT-007
);

CREATE TABLE product_attribute (
    id                      BIGINT PRIMARY KEY,
    product_id              BIGINT      NOT NULL REFERENCES product(id) ON DELETE CASCADE,          -- BR-CATOPT-002
    product_option_id       BIGINT      NOT NULL REFERENCES product_option(id) ON DELETE CASCADE,   -- BR-CATOPT-008
    product_option_value_id BIGINT      NOT NULL REFERENCES product_option_value(id) ON DELETE CASCADE, -- BR-CATOPT-009
    attribute_price         NUMERIC(19,4),                  -- BR-CATOPT-013 (legacy PRODUCT_ATRIBUTE_PRICE); pricing add-on
    attribute_weight        NUMERIC(19,4),                  -- BR-CATOPT-015
    sort_order              INTEGER,                        -- BR-CATOPT-014
    attribute_free          BOOLEAN     NOT NULL DEFAULT FALSE,
    attribute_default       BOOLEAN     NOT NULL DEFAULT FALSE,   -- BR-CATPRICE-009
    attribute_required      BOOLEAN     NOT NULL DEFAULT FALSE,
    attribute_display_only  BOOLEAN     NOT NULL DEFAULT FALSE,   -- BR-CATOPT-017
    attribute_discounted    BOOLEAN     NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_attribute_triple UNIQUE (product_option_id, product_option_value_id, product_id)  -- BR-CATOPT-001
);

CREATE TABLE product_image (
    id            BIGINT PRIMARY KEY,
    product_id    BIGINT       NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    product_image VARCHAR(255) NOT NULL,                     -- file name; sized via L-/S- prefix (BR-CATIMG-004)
    default_image BOOLEAN      NOT NULL DEFAULT FALSE,       -- BR-CATIMG-003
    image_type    VARCHAR(20),
    image_url     VARCHAR(255),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE product_image_description (
    id               BIGINT PRIMARY KEY,
    product_image_id BIGINT       NOT NULL REFERENCES product_image(id) ON DELETE CASCADE,
    language_id      BIGINT       NOT NULL,
    name             VARCHAR(120),
    description      TEXT,
    alt_tag          VARCHAR(120),
    CONSTRAINT uq_image_desc_lang UNIQUE (product_image_id, language_id)
);

CREATE TABLE product_review (
    id            BIGINT PRIMARY KEY,
    product_id    BIGINT       NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    customer_id   BIGINT       NOT NULL,                     -- BR-CATREV-002 (external customer service)
    review_rating NUMERIC(19,4) NOT NULL,                   -- BR-CATREV-001
    review_date   DATE         NOT NULL,                     -- BR-CATREV-005
    status        INTEGER,                                   -- dormant moderation lifecycle (see invariants)
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_review_product_customer ON product_review (product_id, customer_id);  -- BR-CATREV-002/007

CREATE TABLE product_review_description (
    id               BIGINT PRIMARY KEY,
    product_review_id BIGINT      NOT NULL REFERENCES product_review(id) ON DELETE CASCADE,
    language_id      BIGINT       NOT NULL,
    description      TEXT         NOT NULL,                  -- BR-CATREV-003
    CONSTRAINT uq_review_desc_lang UNIQUE (product_review_id, language_id)
);
```

## Entity State Model

### Product lifecycle
- **States:** Draft (initial), Published, Archived (terminal)
- Draft = `available = false OR date_available > now`; Published = `available = true AND date_available <= now` (BR-CATPROD-010); Archived on delete (BR-CATPROD-006).
- The `product_virtual` flag is an orthogonal characteristic toggled by digital-file attach/detach (BR-CATPROD-017/018), not a lifecycle state.

| From | To | Trigger (BR-ID) | Guard |
|------|----|-----------------|-------|
| Draft | Published | BR-CATPROD-010 | available true AND date_available reached |
| Published | Draft | BR-CATPROD-009 | availability withdrawn or date pushed to future |
| Draft | Archived | BR-CATPROD-006 | product and store present |
| Published | Archived | BR-CATPROD-006 | product and store present |

### ProductPrice discount lifecycle (time-based)
- **States:** BasePrice (initial), DiscountActive, DiscountExpired
- Transitions are time-driven by the special date window (BR-CATPRICE-004/005/006), not by explicit commands; DiscountExpired reverts to BasePrice display.

### ProductRelationship group lifecycle
- **States:** Active (initial), Inactive, Deleted (terminal)

| From | To | Trigger (BR-ID) | Guard |
|------|----|-----------------|-------|
| Active | Inactive | BR-CATPROD-022 | deactivateGroup on code |
| Inactive | Active | BR-CATPROD-022 | activateGroup on code |
| Active | Deleted | BR-CATPROD-022 | deleteGroup |
| Inactive | Deleted | BR-CATPROD-022 | deleteGroup |

### Category tree position (structural "state")
Category has no status workflow; its meaningful state is its position in the tree (lineage/depth), mutated by the reparenting engine (BR-CATCAT-005/006). Root = `parent_id IS NULL AND lineage = '/' AND depth = 0`.

## Data Invariants

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-CAT-001 | A product has at least one availability | product | constraint | app |
| INV-CAT-002 | A product SKU is non-empty and alphanumeric-with-underscores | product | constraint | both |
| INV-CAT-003 | A category code is unique within its store | category | constraint | db |
| INV-CAT-004 | A child category's lineage equals parent lineage + parent id + "/" and depth equals parent depth + 1 | category | computed | app |
| INV-CAT-005 | A product binds a given (option, value) pair at most once | product_attribute | constraint | db |
| INV-CAT-006 | An option/value/category/manufacturer has at most one description per language | *_description | constraint | db |
| INV-CAT-007 | A product has at most one downloadable file with a given name | product_digital | constraint | db |
| INV-CAT-008 | A manufacturer cannot be deleted while any product references it | manufacturer | cross-entity | app |
| INV-CAT-009 | product.review_avg = mean of review_rating and review_count = count of reviews (maintained on create only; drifts on delete) | product | computed | app |
| INV-CAT-010 | Only the all-regions availability contributes to final price | product_price | constraint | app |

> INV-CAT-009 is a KNOWN drift point (D-06 preserved): the aggregate is maintained on review create but not on delete. Tagged `app` to preserve legacy behavior; a hardened target would make it `both` (recompute) — flagged for P4a, not changed here.

## DDL Quality Notes
- Every non-standard column traces to a legacy column or a BR-ID (annotated inline).
- `tax_class_id` is retained as a reference id only (tax logic is owned by the tax service; no tax DDL here — see BR-CATPRICE tax note).
- `customer_id` on `product_review` references the customer service (no FK across service boundary).
- `attribute_price` intentionally maps the misspelled legacy column `PRODUCT_ATRIBUTE_PRICE` to a domain-appropriate name.
