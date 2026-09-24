# MS-11 Content / CMS Service — Domain Model

**Service ID**: MS-11
**Schema**: `content_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Owned relational tables**: 2 (`content`, `content_description`)
**Owned non-relational store**: 1 object store (binary bytes) behind EXT-CMS-001 — NOT a relational table

This service owns the CMS content rows (`content`, `content_description`) AND the binary **object store** for
static files and images. Under **BV-5** it owns the binary BYTES; catalog (MS-04) and merchant-store (MS-03)
keep their own blob METADATA + a reference `blob_key` and delegate byte storage to this service. The object
store is modeled as a pluggable abstraction (EXT-CMS-001), not a relational table.

## Core Entities

### content (legacy CONTENT)

```sql
CREATE TABLE content_schema.content (
    content_id       BIGINT       NOT NULL,                     -- Maps to CONTENT.CONTENT_ID (table-generator CONTENT_SEQ_NEXT_VAL)
    store_id         BIGINT       NOT NULL,                     -- Maps to CONTENT.MERCHANT_ID (store owned by MS-03 — reference only, NOT a local FK)
    code             VARCHAR(100) NOT NULL,                     -- Maps to CONTENT.CODE (business key; required by BR-CMS-001)
    content_type     VARCHAR(10)  NULL,                         -- Maps to CONTENT.CONTENT_TYPE (Box/Page/Section — BR-CMS-003)
    content_position VARCHAR(10)  NULL,                         -- Maps to CONTENT.CONTENT_POSITION (Left/Right, nullable — BR-CMS-006)
    visible          BOOLEAN      NOT NULL DEFAULT false,       -- Maps to CONTENT.VISIBLE (sole publish flag — BR-CMS-008; NO published/linkToMenu in 2.0.1)
    sort_order       INTEGER      NOT NULL DEFAULT 0,           -- Maps to CONTENT.SORT_ORDER (BR-CMS-007)
    tenant_id        VARCHAR(64)  NOT NULL,                     -- Multi-tenancy standard
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),       -- Audit/multi-tenancy standard
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),       -- Audit/multi-tenancy standard
    created_by       VARCHAR(64)  NULL,                         -- Audit/multi-tenancy standard
    correlation_id   VARCHAR(64)  NULL,                         -- Audit/multi-tenancy standard
    CONSTRAINT pk_content PRIMARY KEY (content_id),
    CONSTRAINT uq_content_store_code UNIQUE (tenant_id, store_id, code),
    CONSTRAINT ck_content_type CHECK (content_type IS NULL OR content_type IN ('Box','Page','Section')),
    CONSTRAINT ck_content_position CHECK (content_position IS NULL OR content_position IN ('Left','Right'))
);

CREATE INDEX ix_content_store_type ON content_schema.content (tenant_id, store_id, content_type, sort_order);
CREATE INDEX ix_content_code       ON content_schema.content (tenant_id, store_id, code);
```

Note: `uq_content_store_code` enforces BR-CMS-001 ((store, code) unique). `ix_content_store_type` includes
`sort_order` so the store-scoped, type-filtered listings (BR-CMS-014) walk a deterministic ascending order.

### content_description (legacy CONTENT_DESCRIPTION)

```sql
CREATE TABLE content_schema.content_description (
    content_description_id BIGINT       NOT NULL,               -- surrogate key (legacy Description id, table-generator)
    content_id             BIGINT       NOT NULL,               -- Maps to CONTENT_DESCRIPTION.CONTENT_ID (parent; required by BR-CMS-010)
    language_id            BIGINT       NOT NULL,               -- Maps to CONTENT_DESCRIPTION.LANGUAGE_ID (language owned by MS-01 — reference only)
    name                   VARCHAR(120) NOT NULL,               -- Maps to Description.NAME (required by BR-CMS-011)
    title                  VARCHAR(100) NULL,                   -- Maps to Description.TITLE
    body                   TEXT         NULL,                   -- Maps to Description.DESCRIPTION (CLOB rich-text body — BR-CMS-011)
    friendly_url           VARCHAR(120) NULL,                   -- Maps to CONTENT_DESCRIPTION.SEF_URL (storefront friendly URL — BR-CMS-016)
    meta_title             VARCHAR(255) NULL,                   -- Maps to CONTENT_DESCRIPTION.META_TITLE (SEO — BR-CMS-011)
    meta_keywords          VARCHAR(255) NULL,                   -- Maps to CONTENT_DESCRIPTION.META_KEYWORDS (SEO — BR-CMS-011)
    meta_description        VARCHAR(255) NULL,                  -- Maps to CONTENT_DESCRIPTION.META_DESCRIPTION (SEO — BR-CMS-011)
    tenant_id              VARCHAR(64)  NOT NULL,               -- Multi-tenancy standard
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT now(), -- Audit/multi-tenancy standard
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT now(), -- Audit/multi-tenancy standard
    created_by             VARCHAR(64)  NULL,                   -- Audit/multi-tenancy standard
    correlation_id         VARCHAR(64)  NULL,                   -- Audit/multi-tenancy standard
    CONSTRAINT pk_content_description PRIMARY KEY (content_description_id),
    CONSTRAINT fk_content_description_content FOREIGN KEY (content_id)
        REFERENCES content_schema.content (content_id) ON DELETE CASCADE,
    CONSTRAINT uq_content_description_lang UNIQUE (content_id, language_id)
);

CREATE INDEX ix_content_description_url ON content_schema.content_description (tenant_id, friendly_url);
```

Note: `uq_content_description_lang` enforces BR-CMS-010 (one description per content per language).
`ON DELETE CASCADE` realizes the legacy cascade-ALL delete (BR-CMS-018) at the DB tier (integrity invariant
INV-CMS-002). `ix_content_description_url` supports the friendly-URL lookup (BR-CMS-016).

## Owned Object Store (Layer B — NOT a relational table)

The physical binary store (static files + images, including logos and product images) is an **owned object
store**, not a relational table. It is accessed exclusively through EXT-CMS-001 (get / put / remove + image
variants). Objects are addressed by a composite key:

```
object key := (tenant_id, store_code, file_content_type, file_name)
file_content_type ∈ { StaticFile, Image, Logo, Product, ProductLarge, Property, Manufacturer, ProductDigital }
```

This service owns the BYTES for all of the above (BV-5). MS-03 (Logo) and MS-04 (Product/ProductLarge) hold
only metadata + a `blob_key` on their side and call this service to store/retrieve. There is intentionally
**no relational metadata table** for stored files in this baseline (the legacy Infinispan store held only
bytes keyed by name); the object store enumerates file names on demand (BR-CMS-021 / BR-CMS-022). If a future
iteration needs queryable file metadata, it would be added as a new owned table and counted then — it does
not exist now, so the owned-relational-table count remains 2.

## Entity State Model (Layer A)

The content subsystem has **no workflow lifecycle** in this baseline. `content.visible` is a plain boolean
publish flag with no transition guard (BR-CMS-008) — there is no Draft/Published/Archived machine, and there
is deliberately NO `published` or `linkToMenu` column in 2.0.1. `content_description` has no independent
lifecycle (it is a cascade child of `content`). Per the template, an entity with no lifecycle is omitted from
the state-machine section; this note records the deliberate absence so the generator does not synthesize a
state machine the source does not have. Create/save/delete are covered as data operations by
BR-CMS-009 / BR-CMS-017 / BR-CMS-018.

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-CMS-001 | A content item's code is unique within its store | content | constraint | db |
| INV-CMS-002 | A localized description cannot exist without its parent content | content_description | referential | db |
| INV-CMS-003 | A content item has at most one description per language | content_description | constraint | db |
| INV-CMS-004 | A content item's kind is one of box, page, or section | content | constraint | both |
| INV-CMS-005 | A content box's position, when set, is left or right | content | constraint | both |
| INV-CMS-006 | Every localized description has a non-empty name | content_description | constraint | both |

Tier notes: INV-CMS-001 is enforced by `uq_content_store_code`; INV-CMS-002 by the `fk_content_description_content`
FK with `ON DELETE CASCADE`; INV-CMS-003 by `uq_content_description_lang`. These three are integrity invariants
(uniqueness / referential) and are therefore **mandatory-DB** (`db`). INV-CMS-004/005/006 are value-domain
business invariants enforced both by CHECK/NOT NULL constraints and by the application layer (`both`).

## Cross-Service / External References (NOT owned)

| Reference | Owner | How accessed |
|-----------|-------|--------------|
| Merchant store (id, code, template, languages) | MS-03 store-service | Reference read; store code partitions the object store (BR-CMS-021); template drives view suffix (BR-CMS-023) |
| Language (id, code) | MS-01 reference-data | Reference read; descriptions bind to canonical language by code (BR-CMS-012) |
| Store logo bytes (inbound) | MS-03 store-service (metadata owner) | MS-03 calls this service to store/remove LOGO bytes (BR-CMS-020) — content-cms owns the bytes (BV-5) |
| Product image bytes (inbound) | MS-04 catalog (metadata owner) | MS-04 calls this service to store/retrieve PRODUCT/PRODUCTLARGE bytes (BR-CMS-022) — content-cms owns the bytes (BV-5) |

## Extension Point (Layer B)

- **EXT-CMS-001 — Pluggable content-file / object store.** Mechanism: a file-store SPI (get file / get file
  names / get files / put file / put files / remove file / remove files) with an image-variant path. What
  varies per deployment: the physical backend. The **legacy** implementation is an Infinispan tree cache
  (`CmsStaticContentFileManagerInfinispanImpl`); the **modernized target** replaces it with an object store
  (S3-compatible / blob store) per ADR-006/CMS. Used by BR-CMS-019, BR-CMS-020, BR-CMS-021, BR-CMS-022. The
  service logic dispatches to the resolved SPI and NEVER references Infinispan directly (Infinispan internals
  are out of scope). See `spec/shared/extensibility-model.md` (to be compiled at Stage 1.8). Swapping the
  backend requires implementing the SPI and registering it — no CMS content-logic change.
