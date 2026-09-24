# MS-09 Order Service — Domain Model

**Service ID**: MS-09
**Schema**: `order_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Owned tables**: 10 (`orders`, `order_product`, `order_total`, `order_status_history`, `order_product_price`, `order_product_download`, `order_product_attribute`, `order_account`, `order_account_product`, `file_history`)

MS-09 is the **authoritative order-totals engine** (BV-1/ADR-001) and the **orchestrator hub**. It OWNS the
order aggregate and ALL order-state transitions. Tax (MS-07) and shipping (MS-08) are cross-service
synchronous stateless reads folded into the OWNED total computation. Payment (MS-10) settlement is applied
by CONSUMING `payment.captured` / `payment.refunded` — there is NO cross-service order DB write from payment
(BV-2/ADR-003). See the Domain Events and Checkout Saga sections.

The `SM_SEQUENCER` table is NOT owned (it is the shared JPA table-generator; in the target, identity is a
DB sequence / surrogate key per table). `order_account`, `order_account_product` and `file_history` are
carried as owned tables (recurring-billing + download-accounting scaffolding present in the legacy order
family) but are NOT wired into the checkout/download flows in 2.0.1 — flagged for 4a scope decision.

## Core Entities

### orders (legacy ORDERS)

```sql
CREATE TABLE order_schema.orders (
    order_id             BIGINT        NOT NULL,                    -- Maps to ORDERS.ORDER_ID (table-generator seq)
    order_status         VARCHAR(20)   NOT NULL DEFAULT 'Ordered',  -- Maps to ORDERS.ORDER_STATUS (BR-ORD-009; enum Ordered/Processed/Delivered/Refunded)
    order_total          NUMERIC(19,4) NULL,                        -- Maps to ORDERS.ORDER_TOTAL (grand total, BR-ORD-005/018)
    currency_code        VARCHAR(3)    NULL,                        -- Maps to ORDERS.CURRENCY_ID→currency code (BR-ORD-018 snapshot)
    currency_value       NUMERIC(19,4) NOT NULL DEFAULT 1,          -- Maps to ORDERS.CURRENCY_VALUE (exchange rate snapshot)
    customer_id          BIGINT        NULL,                        -- Maps to ORDERS.CUSTOMER_ID (customer owned by MS-05 — reference only, detachable)
    customer_email       VARCHAR(50)   NOT NULL,                    -- Maps to ORDERS.CUSTOMER_EMAIL_ADDRESS (BR-ORD-029)
    store_id             BIGINT        NOT NULL,                    -- Maps to ORDERS.MERCHANTID (store owned by MS-03 — reference; cross-store guard BR-ORD-028)
    date_purchased       DATE          NULL,                        -- Maps to ORDERS.DATE_PURCHASED (BR-ORD-018)
    order_date_finished  TIMESTAMPTZ   NULL,                        -- Maps to ORDERS.ORDER_DATE_FINISHED
    channel              VARCHAR(20)   NULL,                        -- Maps to ORDERS.CHANNEL (OrderChannel enum)
    order_type           VARCHAR(20)   NOT NULL DEFAULT 'Order',    -- Maps to ORDERS.ORDER_TYPE (OrderType enum)
    payment_type         VARCHAR(20)   NULL,                        -- Maps to ORDERS.PAYMENT_TYPE (BR-ORD-020)
    payment_module_code  VARCHAR(64)   NULL,                        -- Maps to ORDERS.PAYMENT_MODULE_CODE (BR-ORD-018)
    shipping_module_code VARCHAR(64)   NULL,                        -- Maps to ORDERS.SHIPPING_MODULE_CODE (BR-ORD-018)
    ip_address           VARCHAR(64)   NULL,                        -- Maps to ORDERS.IP_ADDRESS
    locale               VARCHAR(16)   NULL,                        -- Maps to ORDERS.LOCALE (BR-ORD-018 money formatting)
    billing              JSONB         NULL,                        -- Maps to ORDERS embedded Billing (BR-ORD-018/019/022)
    delivery             JSONB         NULL,                        -- Maps to ORDERS embedded Delivery (BR-ORD-018/019)
    credit_card          JSONB         NULL,                        -- Maps to ORDERS embedded CreditCard: MASKED PAN only (BR-ORD-020 — PCI FLAG)
    last_modified        TIMESTAMPTZ   NULL,                        -- Maps to ORDERS.LAST_MODIFIED (BR-ORD-029)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    created_by           VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_orders PRIMARY KEY (order_id),
    CONSTRAINT ck_orders_status CHECK (order_status IN ('Ordered','Processed','Delivered','Refunded')),
    CONSTRAINT ck_orders_total_nonneg CHECK (order_total IS NULL OR order_total >= 0)
);

CREATE INDEX ix_orders_store        ON order_schema.orders (tenant_id, store_id, date_purchased DESC, order_id);
CREATE INDEX ix_orders_customer     ON order_schema.orders (tenant_id, store_id, customer_id);
```

### order_product (legacy ORDER_PRODUCT)

```sql
CREATE TABLE order_schema.order_product (
    order_product_id     BIGINT        NOT NULL,                    -- Maps to ORDER_PRODUCT.ORDER_PRODUCT_ID
    order_id             BIGINT        NOT NULL,                    -- Maps to ORDER_PRODUCT.ORDER_ID (aggregate root)
    product_sku          VARCHAR(100)  NULL,                        -- Maps to ORDER_PRODUCT.PRODUCT_SKU (BR-ORD-018 snapshot)
    product_name         VARCHAR(255)  NULL,                        -- Maps to ORDER_PRODUCT.PRODUCT_NAME (snapshot)
    product_quantity     INTEGER       NOT NULL,                    -- Maps to ORDER_PRODUCT.PRODUCT_QUANTITY (BR-ORD-018; qty >= 1)
    one_time_charge      NUMERIC(19,4) NOT NULL,                    -- Maps to ORDER_PRODUCT.ONE_TIME_CHARGE (NOT NULL in legacy)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_product PRIMARY KEY (order_product_id),
    CONSTRAINT fk_order_product_order FOREIGN KEY (order_id) REFERENCES order_schema.orders (order_id),
    CONSTRAINT ck_order_product_qty CHECK (product_quantity >= 1)
);

CREATE INDEX ix_order_product_order ON order_schema.order_product (tenant_id, order_id);
```

### order_total (legacy ORDER_TOTAL)

```sql
CREATE TABLE order_schema.order_total (
    order_total_id       BIGINT        NOT NULL,                    -- Maps to ORDER_TOTAL.ORDER_TOTAL_ID
    order_id             BIGINT        NOT NULL,                    -- Maps to ORDER_TOTAL.ORDER_ID
    module_code          VARCHAR(64)   NULL,                        -- Maps to ORDER_TOTAL.MODULE (subtotal/shipping/handling/tax/total/itemprice/refund — BR-ORD-001..005)
    total_type           VARCHAR(20)   NULL,                        -- Maps to ORDER_TOTAL.ORDER_TOTAL_TYPE (SUBTOTAL/SHIPPING/HANDLING/TAX/TOTAL/PRODUCT)
    total_code           VARCHAR(64)   NULL,                        -- Maps to ORDER_TOTAL.ORDER_TOTAL_CODE (e.g. order.total.subtotal)
    total_text           VARCHAR(255)  NULL,                        -- Maps to ORDER_TOTAL.TEXT (display label; tax label BR-ORD-004)
    total_value          NUMERIC(19,4) NOT NULL,                    -- Maps to ORDER_TOTAL.VALUE (BR-ORD-005; NOT NULL)
    sort_order           INTEGER       NOT NULL DEFAULT 0,          -- Maps to ORDER_TOTAL.SORT_ORDER (display order BR-ORD-005)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_total PRIMARY KEY (order_total_id),
    CONSTRAINT fk_order_total_order FOREIGN KEY (order_id) REFERENCES order_schema.orders (order_id)
);

CREATE INDEX ix_order_total_order ON order_schema.order_total (tenant_id, order_id, sort_order);
```

### order_status_history (legacy ORDER_STATUS_HISTORY)

```sql
CREATE TABLE order_schema.order_status_history (
    order_status_history_id BIGINT     NOT NULL,                    -- Maps to ORDER_STATUS_HISTORY.ORDER_STATUS_HISTORY_ID
    order_id             BIGINT        NOT NULL,                    -- Maps to ORDER_STATUS_HISTORY.ORDER_ID
    status               VARCHAR(20)   NOT NULL,                    -- Maps to ORDER_STATUS_HISTORY.STATUS (BR-ORD-009/010/029)
    date_added           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Maps to ORDER_STATUS_HISTORY.DATE_ADDED (BR-ORD-009)
    customer_notified    BOOLEAN       NOT NULL DEFAULT false,      -- Maps to ORDER_STATUS_HISTORY.CUSTOMER_NOTIFIED (BR-ORD-029)
    comments             VARCHAR(4000) NULL,                        -- Maps to ORDER_STATUS_HISTORY.COMMENTS (BR-ORD-029)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_status_history PRIMARY KEY (order_status_history_id),
    CONSTRAINT fk_osh_order FOREIGN KEY (order_id) REFERENCES order_schema.orders (order_id),
    CONSTRAINT ck_osh_status CHECK (status IN ('Ordered','Processed','Delivered','Refunded'))
);

CREATE INDEX ix_osh_order ON order_schema.order_status_history (tenant_id, order_id, date_added);
```

### order_product_price (legacy ORDER_PRODUCT_PRICE)

```sql
CREATE TABLE order_schema.order_product_price (
    order_product_price_id BIGINT      NOT NULL,                    -- Maps to ORDER_PRODUCT_PRICE.ORDER_PRODUCT_PRICE_ID
    order_product_id     BIGINT        NOT NULL,                    -- Maps to ORDER_PRODUCT_PRICE.ORDER_PRODUCT_ID
    price_code           VARCHAR(64)   NULL,                        -- Maps to ORDER_PRODUCT_PRICE.PRODUCT_PRICE_CODE (BR-ORD-001 additional prices)
    product_price        NUMERIC(19,4) NOT NULL,                    -- Maps to ORDER_PRODUCT_PRICE.PRODUCT_PRICE (snapshot BR-ORD-018)
    is_default           BOOLEAN       NOT NULL DEFAULT true,       -- Maps to ORDER_PRODUCT_PRICE.DEFAULT_PRICE (BR-ORD-001)
    price_name           VARCHAR(255)  NULL,                        -- Maps to ORDER_PRODUCT_PRICE.PRODUCT_PRICE_NAME
    price_type           VARCHAR(20)   NULL,                        -- Required by BR-ORD-001 (ONE_TIME vs recurring additional price)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_product_price PRIMARY KEY (order_product_price_id),
    CONSTRAINT fk_opp_order_product FOREIGN KEY (order_product_id) REFERENCES order_schema.order_product (order_product_id)
);

CREATE INDEX ix_opp_order_product ON order_schema.order_product_price (tenant_id, order_product_id);
```

### order_product_download (legacy ORDER_PRODUCT_DOWNLOAD)

```sql
CREATE TABLE order_schema.order_product_download (
    order_product_download_id BIGINT   NOT NULL,                    -- Maps to ORDER_PRODUCT_DOWNLOAD.ORDER_PRODUCT_DOWNLOAD_ID
    order_product_id     BIGINT        NOT NULL,                    -- Maps to ORDER_PRODUCT_DOWNLOAD.ORDER_PRODUCT_ID
    product_filename     VARCHAR(255)  NOT NULL,                    -- Maps to ORDER_PRODUCT_DOWNLOAD.ORDER_PRODUCT_FILENAME (BR-ORD-032)
    max_days             INTEGER       NOT NULL DEFAULT 31,         -- Maps to ORDER_PRODUCT_DOWNLOAD.DOWNLOAD_MAXDAYS (default 31 — BR-ORD-032 unenforced FLAG)
    download_count       INTEGER       NOT NULL DEFAULT 0,          -- Maps to ORDER_PRODUCT_DOWNLOAD.DOWNLOAD_COUNT (BR-ORD-032 never incremented FLAG)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_product_download PRIMARY KEY (order_product_download_id),
    CONSTRAINT fk_opd_order_product FOREIGN KEY (order_product_id) REFERENCES order_schema.order_product (order_product_id),
    CONSTRAINT ck_opd_count_nonneg CHECK (download_count >= 0)
);

CREATE INDEX ix_opd_order_product ON order_schema.order_product_download (tenant_id, order_product_id);
```

### order_product_attribute (legacy ORDER_PRODUCT_ATTRIBUTE)

```sql
CREATE TABLE order_schema.order_product_attribute (
    order_product_attribute_id BIGINT  NOT NULL,                    -- Maps to ORDER_PRODUCT_ATTRIBUTE.ORDER_PRODUCT_ATTRIBUTE_ID
    order_product_id     BIGINT        NOT NULL,                    -- Maps to ORDER_PRODUCT_ATTRIBUTE.ORDER_PRODUCT_ID
    attribute_name       VARCHAR(255)  NULL,                        -- Maps to ORDER_PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_NAME (snapshot BR-ORD-018)
    attribute_value      VARCHAR(255)  NULL,                        -- Maps to ORDER_PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_VAL_NAME
    attribute_price      NUMERIC(19,4) NULL,                        -- Maps to ORDER_PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_PRICE
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_product_attribute PRIMARY KEY (order_product_attribute_id),
    CONSTRAINT fk_opa_order_product FOREIGN KEY (order_product_id) REFERENCES order_schema.order_product (order_product_id)
);

CREATE INDEX ix_opa_order_product ON order_schema.order_product_attribute (tenant_id, order_product_id);
```

### order_account (legacy ORDER_ACCOUNT — recurring-billing scaffolding, not wired in 2.0.1)

```sql
CREATE TABLE order_schema.order_account (
    order_account_id     BIGINT        NOT NULL,                    -- Maps to ORDER_ACCOUNT.ORDER_ACCOUNT_ID
    order_id             BIGINT        NOT NULL,                    -- Maps to ORDER_ACCOUNT.ORDER_ID
    account_start_date   DATE          NULL,                        -- Maps to ORDER_ACCOUNT.ORDER_ACCOUNT_START_DATE (billing window start)
    account_end_date     DATE          NULL,                        -- Maps to ORDER_ACCOUNT.ORDER_ACCOUNT_END_DATE (billing window end)
    bill_day             INTEGER       NULL,                        -- Maps to ORDER_ACCOUNT.ORDER_ACCOUNT_BILL_DAY (INV-ORD-006)
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_account PRIMARY KEY (order_account_id),
    CONSTRAINT fk_oa_order FOREIGN KEY (order_id) REFERENCES order_schema.orders (order_id),
    CONSTRAINT ck_oa_window CHECK (account_end_date IS NULL OR account_start_date IS NULL OR account_end_date >= account_start_date)
);
```

### order_account_product (legacy ORDER_ACCOUNT_PRODUCT — recurring-billing scaffolding)

```sql
CREATE TABLE order_schema.order_account_product (
    order_account_product_id BIGINT    NOT NULL,                    -- Maps to ORDER_ACCOUNT_PRODUCT.ORDER_ACCOUNT_PRODUCT_ID
    order_account_id     BIGINT        NOT NULL,                    -- Maps to ORDER_ACCOUNT_PRODUCT.ORDER_ACCOUNT_ID
    payment_frequency    VARCHAR(20)   NULL,                        -- Maps to ORDER_ACCOUNT_PRODUCT payment frequency type
    product_amount       NUMERIC(19,4) NULL,                        -- Maps to ORDER_ACCOUNT_PRODUCT recurring amount
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_order_account_product PRIMARY KEY (order_account_product_id),
    CONSTRAINT fk_oap_order_account FOREIGN KEY (order_account_id) REFERENCES order_schema.order_account (order_account_id)
);
```

### file_history (legacy FILE_HISTORY — download-accounting entity, unused by the download path)

```sql
CREATE TABLE order_schema.file_history (
    file_history_id      BIGINT        NOT NULL,                    -- Maps to FILE_HISTORY primary key
    order_product_download_id BIGINT   NULL,                        -- Maps to FILE_HISTORY download reference (download-accounting)
    download_date        TIMESTAMPTZ   NULL,                        -- Maps to FILE_HISTORY download timestamp
    downloaded_by        VARCHAR(64)   NULL,                        -- Maps to FILE_HISTORY actor
    tenant_id            VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    correlation_id       VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_file_history PRIMARY KEY (file_history_id),
    CONSTRAINT fk_fh_download FOREIGN KEY (order_product_download_id) REFERENCES order_schema.order_product_download (order_product_download_id)
);
```

## Entity State Model (Layer A)

#### orders lifecycle

- **States:** Ordered (initial), Processed, Delivered (terminal-ish), Refunded (terminal-ish)
- **Enum values (legacy `OrderStatus.java:3-14`):** `"ordered" / "processed" / "delivered" / "refunded"`.
- **Transitions (as OBSERVED — the legacy encodes NO legal-transition map; any state may be set from any state via admin edit):**

  | From | To | Trigger (BR-ID) | Guard (precondition) |
  |------|----|-----------------|----------------------|
  | (new) | Ordered | BR-ORD-009 | order placed with no status; initial history row written |
  | Ordered | Processed | BR-ORD-029 (also via consumed `payment.captured`) | admin edit / settlement fact applied by MS-09 |
  | Ordered | Delivered | BR-ORD-029 | admin free assignment (unguarded in legacy) |
  | Ordered | Refunded | BR-ORD-029 (also via consumed `payment.refunded`) | admin free assignment / refund settlement applied |
  | Processed | Delivered | BR-ORD-029 | admin free assignment |
  | Processed | Refunded | BR-ORD-029 (also via consumed `payment.refunded`) | admin / refund settlement applied |
  | Delivered | Refunded | BR-ORD-029 (also via consumed `payment.refunded`) | admin / refund settlement applied |

**Closed-machine notes (verified at 4a):**
- Initial state: Ordered (BR-ORD-009). Every state is reachable from Ordered.
- Every non-terminal state (Ordered, Processed) has an outgoing transition. Delivered and Refunded are the
  observed end states (each still admits admin edits in the legacy — they are terminal-ish, not hard-terminal).
- **FLAG [D-06 — status transition set NOT encoded in legacy]:** the legacy places NO transition guard
  (`OrderControler.saveOrder:341` sets status by free assignment, BR-ORD-029). The transition table above is
  the OBSERVED / intended forward flow (Ordered→Processed→Delivered, Refunded reachable on refund), NOT an
  enforced map. The LEGAL transition set (forward-only? is Delivered→Refunded permitted? is Refunded
  terminal?) is a **Phase 4a decision** — the modernized generator MUST NOT invent an enforced map here; the
  closed machine is finalized at 4a. Until then the app enforces only "status ∈ enum" (INV-ORD-004) and
  writes a history row per change (BR-ORD-010).
- The current status lives on `orders.order_status`; `order_status_history` is the append-only audit trail
  (each change writes a new row — BR-ORD-009/010/029).

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-ORD-001 | An order's current status must be mirrored by at least one status-history entry | orders | cross-entity | both |
| INV-ORD-002 | An order's grand total equals its subtotal plus shipping plus handling plus the sum of its tax lines | orders | computed | both |
| INV-ORD-003 | An ordered line's quantity is at least one and its one-time charge is present | order_product | constraint | both |
| INV-ORD-004 | An order's status is always one of the defined order states | orders | constraint | both |
| INV-ORD-005 | A cumulative refund recorded against an order never exceeds the order total | orders | constraint | app |
| INV-ORD-006 | A recurring billing account's end date is not earlier than its start date | order_account | cross-field | both |
| INV-ORD-007 | A settlement fact from a payment event is applied to an order at most once | orders | constraint | app |

Tier notes:
- **INV-ORD-002 is computed** — source expression: `order_total = subtotal + (freeShipping ? 0 : shipping) + handling + SUM(tax_lines)` (BR-ORD-005). A hardcoded/placeholder order total is a visible violation. Enforced `both` (app computes; a DB trigger cross-checks the persisted total against its total lines).
- **INV-ORD-001 is an integrity invariant** (status must have a backing history row) → `both`: enforced by a DB trigger (`trg_order_status_history_required`) plus the app writing history on every status change (BR-ORD-009/010).
- **INV-ORD-003 / INV-ORD-004** are enforced by DB CHECK constraints (`ck_order_product_qty`, `ck_orders_status`) and re-validated in the app.
- **INV-ORD-006** enforced by the `ck_oa_window` CHECK.
- **INV-ORD-005 (refund ≤ total)** and **INV-ORD-007 (idempotent settlement)** are temporal/business invariants over the consumed payment-event stream — enforced in the domain layer (they depend on the order's applied-event set and the refund context, not a single-row DB constraint). INV-ORD-007 is backed by a processed-event dedupe keyed on `transactionId`.

### Database Logic Objects (Layer C — mandatory-DB integrity only)

| Name | Kind | Implements | Enforces Invariant | Migration Order | Binding | Placement |
|------|------|------------|--------------------|-----------------|---------|-----------|
| trg_order_status_history_required | trigger |  | INV-ORD-001 | 30 | trigger — no app call (fires on INSERT/UPDATE of orders.order_status) | mandatory-db-integrity |
| trg_order_total_consistency | trigger |  | INV-ORD-002 | 31 | trigger — no app call (validates orders.order_total against SUM(order_total.total_value) of component lines) | mandatory-db-integrity |

> Both triggers are integrity invariants (Layer A), NOT Phase 4b placement decisions. Their executable DDL is
> generated as ordered migrations (order 30/31) against the base tables above. All other order logic stays
> app-tier (default) — the read-heavy `listByStore` (BR-ORD-015) and `getById` (BR-ORD-014) are flagged in
> Phase 1 Layer C for 4b performance evidence only, NOT for a tier move.

## Domain Events

MS-09 PUBLISHES `order.placed` on successful checkout and CONSUMES `payment.captured` / `payment.refunded`
from MS-10. Consuming (not being written to) is the BV-2/ADR-003 money-safety seam: MS-09 owns and enforces
all order-state transitions and applies settlement facts in ITS OWN transaction, idempotent on
`transactionId` (INV-ORD-007). There is no shared order table and no cross-service write from payment.

### Published: order.placed

- **Triggered by:** BR-ORD-008 / BR-ORD-025 (order successfully persisted at checkout)
- **Consumed by:** downstream (notifications, analytics, fulfillment; cart teardown is local to checkout)
- **Payload:**
  ```json
  {
    "orderId": "ORD-5001",
    "storeId": "STORE-1",
    "customerId": "CUST-9",
    "total": 130.38,
    "currency": "USD",
    "status": "Ordered",
    "hasDownloads": true,
    "timestamp": "2026-01-01T12:00:00Z"
  }
  ```
- **Guarantees:** at-least-once; downstream consumers idempotent on `orderId`.

### Consumed: payment.captured (from MS-10)

- **Emitted by:** MS-10 on AuthorizeCapture settlement or capture of a prior authorization
- **Handler behavior (in MS-09's own transaction):**
  ```
  on payment.captured{transactionId, orderId, amount, transactionType, paymentType, ...}:
     if already processed transactionId → ACK, no-op            # INV-ORD-007 idempotency
     load order(orderId)
     if paymentType == MoneyOrder → mark order awaiting funds   # money order → awaiting funds
     else → set order settled/PROCESSED + append status-history (BR-ORD-009/010)
     record processed transactionId
  ```
- **Idempotency:** dedupe on `transactionId` (INV-ORD-007). At-least-once delivery tolerated.

### Consumed: payment.refunded (from MS-10)

- **Emitted by:** MS-10 on refund recorded
- **Handler behavior (in MS-09's own transaction):**
  ```
  on payment.refunded{transactionId, orderId, amount, ...}:
     if already processed transactionId → ACK, no-op            # INV-ORD-007 idempotency
     load order(orderId)
     require cumulative refunds + amount <= order.total         # INV-ORD-005
     append refund OrderTotal line (module="refund"); decrement order total
     set order status Refunded + append status-history (BR-ORD-010)
     record processed transactionId
  ```
- **Idempotency:** dedupe on `transactionId` (INV-ORD-007).

## Checkout Saga / Reconciliation (D-08 / R-03)

Checkout is a **saga with idempotency + reconciliation — NOT 2PC** and NOT a shared cross-service
transaction. `processOrder → process` (BR-ORD-008) runs:

1. **CHARGE step (distributed):** invoke MS-10 payment charge with the checkout idempotency key. Retried
   safely because the charge endpoint is idempotent on that key.
2. **PERSIST step (local tx):** insert the order aggregate + initial status history (BR-ORD-008/009).
3. **PUBLISH:** emit `order.placed` (BR-ORD-025).

The **charge-vs-persist window** (payment charged but order not persisted, or vice versa) is closed by a
**reconciliation job** enforcing the Architecture §7 money-safety invariant: **no PROCESSED order without a
CAPTURED transaction** (and no CAPTURED transaction stranded without an order — it drives compensation:
persist/complete the order or refund the orphan charge). Settlement facts still flow via the consumed
`payment.captured` / `payment.refunded` events (idempotent on `transactionId`). No 2PC, no distributed lock.

## Cross-Service / External References (NOT owned)

| Reference | Owner | How accessed |
|-----------|-------|--------------|
| Tax calculation | MS-07 tax-service | Synchronous stateless read (`/calculate`) folded into the OWNED total (BV-1, BR-ORD-004) |
| Shipping quote + configuration | MS-08 shipping-service | Synchronous stateless read (`/quote`, config) folded into the OWNED total (BV-1, BR-ORD-002/003/024) |
| Payment charge / capture / refund + settlement | MS-10 payment-service | Charge = saga CHARGE step (BR-ORD-008/030); settlement applied by CONSUMING `payment.captured` / `payment.refunded` (BV-2) — NO cross-service order write |
| Cart to convert to order | MS-06 cart-service | Cart is the source basket (BV-3 — cart delegates its authoritative total here); cart deleted on commit (BR-ORD-025) |
| Customer | MS-05 customer-service | Reference read + create on checkout (BR-ORD-008/025) |
| Country / zone / language reference | MS-01 reference-data | Reference read (address display, BR-ORD-028) |
| Merchant store | MS-03 store-service | Reference read (cross-store guard BR-ORD-028; defaults BR-ORD-023) |
| Email (confirmation / registration / download) | Email integration | Outbound notification (BR-ORD-025) — failures do not roll back the order |
| Digital content file | Content integration | Outbound read for download delivery (BR-ORD-032) |
| Invoice document | Invoice module | Outbound PDF render (BR-ORD-013) |
| External PayPal Express | External PSP (via MS-10 SPI) | Pre-auth init redirect (BR-ORD-027) |
