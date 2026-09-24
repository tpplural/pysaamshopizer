# Cart Service (MS-06) — Domain Model

**Service ID**: MS-06
**Schema**: `cart_schema`
**Target**: PostgreSQL 15+ (FastAPI / SQLAlchemy or asyncpg)

Owned tables (3): `shopping_cart`, `shopping_cart_item`, `shopping_cart_attribute_item`
(legacy `SHOPPING_CART` / `SHOPPING_CART_ITEM` / `SHOPPING_CART_ATTR_ITEM`).

**External reads (NOT owned, no DDL here):**
- `product`, `product_attribute` — Catalog/Pricing service (MS-04). Referenced by id only.
- `merchant_store` — Reference/Store service (MS-03). Referenced by id only.
- Authoritative order/tax/shipping totals — Order service (MS-09). No total/tax/shipping tables live here (decision BV-3).

The cart persists only its own aggregate. Product/attribute/store rows are referenced by opaque id; the
line's `item_price` is a **snapshot** captured from MS-04 pricing (BR-CART-009/018), not a foreign key into
a price table.

---

## Core Entities (executable DDL)

```sql
CREATE SCHEMA IF NOT EXISTS cart_schema;

-- =========================================================================
-- shopping_cart  (legacy SHOPPING_CART)
-- =========================================================================
CREATE TABLE cart_schema.shopping_cart (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- legacy SHP_CART_ID (SM_SEQUENCER)
    cart_code       VARCHAR(64)  NOT NULL,          -- legacy SHP_CART_CODE — client-facing token (BR-CART-001/002)
    merchant_id     BIGINT       NOT NULL,          -- legacy MERCHANT_ID — store ref (MS-03), BR-CART-003
    customer_id     BIGINT       NULL,              -- legacy CUSTOMER_ID — optional shopper owner (MS-05), BR-CART-004
    -- audit / multi-tenancy standard
    tenant_id       VARCHAR(64)  NOT NULL,          -- multi-tenancy standard
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),   -- audit standard (legacy AuditSection)
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),   -- audit standard
    CONSTRAINT uq_shopping_cart_code UNIQUE (merchant_id, cart_code)   -- INV-CART-001 (BR-CART-002/003)
);

CREATE INDEX ix_shopping_cart_customer ON cart_schema.shopping_cart (merchant_id, customer_id);  -- BR-CART-005
CREATE INDEX ix_shopping_cart_code     ON cart_schema.shopping_cart (cart_code);                 -- BR-CART-002

-- =========================================================================
-- shopping_cart_item  (legacy SHOPPING_CART_ITEM)
-- =========================================================================
CREATE TABLE cart_schema.shopping_cart_item (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- legacy SHP_CART_ITEM_ID
    cart_id         BIGINT       NOT NULL,          -- legacy SHP_CART_ID (FK to shopping_cart)
    product_id      BIGINT       NOT NULL,          -- legacy PRODUCT_ID — catalog ref (MS-04), BR-CART-007
    quantity        INTEGER      NOT NULL DEFAULT 1,-- legacy QUANTITY — BR-CART-006/017
    item_price      NUMERIC(15,2) NULL,             -- legacy transient itemPrice — price snapshot (BR-CART-009/018)
    product_virtual BOOLEAN      NOT NULL DEFAULT FALSE,  -- legacy transient productVirtual (BR-CART-009/011)
    tenant_id       VARCHAR(64)  NOT NULL,          -- multi-tenancy standard
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT fk_cart_item_cart FOREIGN KEY (cart_id)
        REFERENCES cart_schema.shopping_cart (id) ON DELETE CASCADE,   -- BR-CART-019/020 (orphan removal)
    CONSTRAINT ck_cart_item_qty CHECK (quantity >= 1)                  -- INV-CART-003 (BR-CART-017)
);

CREATE INDEX ix_cart_item_cart    ON cart_schema.shopping_cart_item (cart_id);
CREATE INDEX ix_cart_item_product ON cart_schema.shopping_cart_item (product_id);   -- BR-CART-011 duplicate detection

-- =========================================================================
-- shopping_cart_attribute_item  (legacy SHOPPING_CART_ATTR_ITEM)
-- =========================================================================
CREATE TABLE cart_schema.shopping_cart_attribute_item (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- legacy SHP_CART_ATTR_ITEM_ID
    cart_item_id         BIGINT  NOT NULL,          -- legacy SHP_CART_ITEM_ID (FK to shopping_cart_item)
    product_attribute_id BIGINT  NOT NULL,          -- legacy PRODUCT_ATTR_ID — catalog ref (MS-04), BR-CART-010
    tenant_id            VARCHAR(64) NOT NULL,       -- multi-tenancy standard
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_cart_attr_item FOREIGN KEY (cart_item_id)
        REFERENCES cart_schema.shopping_cart_item (id) ON DELETE CASCADE,  -- BR-CART-019 cascade
    CONSTRAINT uq_cart_attr UNIQUE (cart_item_id, product_attribute_id)    -- INV-CART-006 (BR-CART-010)
);

CREATE INDEX ix_cart_attr_item ON cart_schema.shopping_cart_attribute_item (cart_item_id);
```

---

## Entity State Model (Layer A)

Only `shopping_cart` has a lifecycle. `shopping_cart_item` and `shopping_cart_attribute_item` are leaf/child
rows with no independent status (their lifecycle is subordinate to the cart aggregate). The lifecycle is
IMPLICIT in the legacy (`obsolete` is a transient flag, not a persisted status column — BR-CART-021).

#### shopping_cart lifecycle
- **States:** Anonymous (initial), CustomerOwned, Deleted (terminal)
- **Transitions:**

  | From | To | Trigger (BR-ID) | Guard (precondition) |
  |------|----|-----------------|----------------------|
  | Anonymous | Anonymous | BR-CART-007..019 | item add/update/remove leaves ≥1 line, no owner set |
  | Anonymous | CustomerOwned | BR-CART-004 / BR-CART-022 | a shopper is associated (created with customer, or merged on login) |
  | CustomerOwned | CustomerOwned | BR-CART-007..019 | item add/update/remove leaves ≥1 line |
  | Anonymous | Deleted | BR-CART-020 / BR-CART-021 | last item removed, OR read finds cart empty / all products gone |
  | CustomerOwned | Deleted | BR-CART-020 / BR-CART-021 / BR-CART-022 | last item removed; obsolete on read; session cart discarded after merge |

**Closed-machine check:**
- `Anonymous` is the sole initial state; `Deleted` is terminal (no outgoing transitions).
- Every non-terminal state (`Anonymous`, `CustomerOwned`) has outgoing transitions.
- Every state is reachable from `Anonymous`.
- No operation drives the cart to a state outside this set. "Obsolete" is not a persisted state — it is the
  transient computation (BR-CART-021) that decides the `→ Deleted` transition on read.

---

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-CART-001 | A cart's client token is unique within its store | shopping_cart | constraint | db |
| INV-CART-002 | A cart must belong to exactly one store | shopping_cart | constraint | both |
| INV-CART-003 | A line item's quantity is always at least one | shopping_cart_item | constraint | both |
| INV-CART-004 | A line item's subtotal preview equals its unit price times its quantity | shopping_cart_item | computed | app |
| INV-CART-005 | A shopper has at most one active cart per store | shopping_cart | constraint | both |
| INV-CART-006 | A selected option appears at most once on a line and must belong to the line's product | shopping_cart_attribute_item | cross-field | both |

**Tier notes:**
- **INV-CART-001** — enforced by `uq_shopping_cart_code (merchant_id, cart_code)`; DB integrity (closes the
  duplicate-token window the legacy tolerated in BR-CART-002/005).
- **INV-CART-002** — `merchant_id NOT NULL` (db) + app guard on every lookup (BR-CART-003).
- **INV-CART-003** — `CHECK (quantity >= 1)` (db) + app guard (BR-CART-017). Note: the legacy enforced this
  only on update, not add (BR-CART-011); the DB CHECK makes it uniform.
- **INV-CART-004** — computed (`sub_total = item_price * quantity`), preview only; the authoritative total is
  MS-09's (BV-3). App-tier; a hardcoded subtotal is a visible violation of the source expression.
- **INV-CART-005** — target-hardening of BR-CART-005 (legacy silently returned the first of several). Enforce
  via partial/unique index on `(merchant_id, customer_id)` for owned carts in the app + DB.
- **INV-CART-006** — `uq_cart_attr (cart_item_id, product_attribute_id)` (db) + product-ownership guard in app
  (BR-CART-010/023).

No `### Database Logic Objects` section — all cart logic is app-tier. The only DB-tier objects are the
integrity constraints above (expressed as UNIQUE/CHECK/FK in the Core Entities DDL), not procedures/triggers.
Totals/tax/shipping are owned by MS-09 and are not represented as DB objects here.

## Invariant count: 6 (INV-CART-001 .. INV-CART-006)
