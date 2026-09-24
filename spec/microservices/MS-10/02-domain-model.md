# MS-10 Payment Service — Domain Model

**Service ID**: MS-10
**Schema**: `payment_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Owned tables**: 2 (`transaction`, `payment_method_configuration`)

This service owns ONLY its transaction ledger and its payment-method configuration. Order status/total
changes are NOT owned here — they are emitted as domain events (`payment.captured` / `payment.refunded`)
and applied by MS-09 (order service). See the Domain Events section (BV-2 / ADR-003 seam).

## Core Entities

### transaction (legacy SM_TRANSACTION)

```sql
CREATE TABLE payment_schema.transaction (
    transaction_id      BIGINT        NOT NULL,                    -- Maps to SM_TRANSACTION.TRANSACTION_ID (table-generator seq)
    order_id            BIGINT        NULL,                        -- Maps to SM_TRANSACTION.ORDER_ID (FK to order owned by MS-09 — reference only, NOT a local FK)
    amount              NUMERIC(19,4) NOT NULL,                    -- Maps to SM_TRANSACTION.AMOUNT (money — exact decimal, fixes legacy double compare)
    currency_code       VARCHAR(3)    NOT NULL,                    -- Required by BR-PAY-001 (store currency is authoritative on the transaction)
    transaction_date    TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Maps to SM_TRANSACTION.TRANSACTION_DATE
    transaction_type    VARCHAR(20)   NOT NULL,                    -- Maps to SM_TRANSACTION.TRANSACTION_TYPE (Init/Authorize/Capture/AuthorizeCapture/Refund)
    payment_type        VARCHAR(20)   NULL,                        -- Maps to SM_TRANSACTION.PAYMENT_TYPE (CreditCard/Free/Cod/MoneyOrder/Paypal)
    payment_module_code VARCHAR(64)   NULL,                        -- Required by BR-PAY-007/012 (which gateway settled/refunded this transaction)
    details             JSONB         NULL,                        -- Maps to SM_TRANSACTION.DETAILS (gateway tokens/refs — legacy CLOB of JSON; BR-PAY-016/017)
    tenant_id           VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    created_by          VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    correlation_id      VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_transaction PRIMARY KEY (transaction_id),
    CONSTRAINT ck_transaction_type CHECK (transaction_type IN ('Init','Authorize','Capture','AuthorizeCapture','Refund')),
    CONSTRAINT ck_transaction_amount_positive CHECK (amount >= 0)
);

CREATE INDEX ix_transaction_order       ON payment_schema.transaction (tenant_id, order_id, transaction_date, transaction_id);
CREATE INDEX ix_transaction_type        ON payment_schema.transaction (tenant_id, order_id, transaction_type);
```

Note on ordering: `ix_transaction_order` includes `(transaction_date, transaction_id)` so the
capture/refund selection walks a DETERMINISTIC order — this fixes the legacy `listByOrder` no-ORDER-BY
hazard (BR-PAY-018).

### payment_method_configuration (legacy per-store encrypted PAYMENT config in SM_MERCHANT_CONFIGURATION)

```sql
CREATE TABLE payment_schema.payment_method_configuration (
    config_id           BIGINT        NOT NULL,                    -- surrogate key
    store_id            BIGINT        NOT NULL,                    -- Maps to SM_MERCHANT_CONFIGURATION.MERCHANT_STORE_ID (store owned by MS-03 — reference only)
    module_code         VARCHAR(64)   NOT NULL,                    -- Required by BR-PAY-002/009 (gateway plug-in code, e.g. paypal)
    active              BOOLEAN       NOT NULL DEFAULT false,      -- Maps to IntegrationConfiguration.active (BR-PAY-002/011)
    default_selected    BOOLEAN       NOT NULL DEFAULT false,      -- Maps to IntegrationConfiguration.defaultSelected (BR-PAY-011)
    transaction_mode    VARCHAR(20)   NULL,                        -- Maps to integrationKeys["transaction"] (BR-PAY-003; Authorize/AuthorizeCapture)
    config_blob         BYTEA         NOT NULL,                    -- Required by BR-PAY-008/009: encrypted per-store JSON (credentials never in clear text)
    tenant_id           VARCHAR(64)   NOT NULL,                    -- Multi-tenancy standard
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),      -- Audit/multi-tenancy standard
    created_by          VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    correlation_id      VARCHAR(64)   NULL,                        -- Audit/multi-tenancy standard
    CONSTRAINT pk_payment_method_configuration PRIMARY KEY (config_id),
    CONSTRAINT uq_payment_method_config UNIQUE (tenant_id, store_id, module_code),
    CONSTRAINT ck_config_transaction_mode CHECK (transaction_mode IS NULL OR transaction_mode IN ('Authorize','AuthorizeCapture'))
);

CREATE INDEX ix_config_store ON payment_schema.payment_method_configuration (tenant_id, store_id, active);
```

Legacy origin: in Shopizer the whole set of a store's payment methods lives as ONE encrypted JSON blob
under `SM_MERCHANT_CONFIGURATION` key="PAYMENT" (plus per-module custom rows). The modernized model keeps
one row per (store, method) with the encrypted blob retained for gateway credentials, exposing `active`,
`default_selected`, and `transaction_mode` as first-class columns for querying (BR-PAY-002/003/008/009/009b/011).

## Entity State Model (Layer A)

#### transaction lifecycle

- **States:** Init (transient, not persisted), Authorize (initial persisted), AuthorizeCapture (initial persisted, terminal-settled), Capture (terminal-settled), Refund (terminal)
- **Transitions:**

  | From | To | Trigger (BR-ID) | Guard (precondition) |
  |------|----|-----------------|----------------------|
  | (new) | Authorize | BR-PAY-004/005 | configured transaction mode = Authorize; gateway authorizes |
  | (new) | AuthorizeCapture | BR-PAY-004/005 | configured mode = AuthorizeCapture (default); gateway authorizes+captures |
  | Authorize | Capture | BR-PAY-007 | a capturable Authorize exists (BR-PAY-013); gateway captures |
  | AuthorizeCapture | Refund | BR-PAY-012 | a refundable settled transaction exists (BR-PAY-014); amount ≤ order total (BR-PAY-012a) |
  | Capture | Refund | BR-PAY-012 | a refundable settled transaction exists (BR-PAY-014); amount ≤ order total (BR-PAY-012a) |

  Init is a transient token step (BR-PAY-005/027) — it produces a token transaction that is NOT persisted, so it has no persisted-state transitions.

**Closed-machine notes (verified at 4a):**
- Initial persisted states are Authorize and AuthorizeCapture (reachable from a new payment via BR-PAY-004).
- Terminal states: Refund (no outgoing transitions). AuthorizeCapture and Capture are settled states whose only outgoing transition is to Refund.
- Every non-terminal state (Authorize, AuthorizeCapture, Capture) has an outgoing transition.
- Legacy has NO PARTIALLY_REFUNDED state — a partial refund lands the order at refunded (a repeat refund is bounded by BR-PAY-012a against the remaining total). Flagged for 4a.
- The ledger is append-only: each state is a NEW row (Authorize row, then a separate Capture row), not an in-place status update. The "state" of an order's payment is derived by scanning its transaction rows (BR-PAY-013/014).

## Data Invariants (Layer A)

| Invariant ID | Statement (domain terms) | Entity | Kind | Tier |
|--------------|--------------------------|--------|------|------|
| INV-PAY-001 | A capture transaction must have a prior authorization for the same order | transaction | cross-field | app |
| INV-PAY-002 | A refund transaction must have a prior settled (authorize-capture or capture) transaction for the same order | transaction | cross-field | app |
| INV-PAY-003 | Cumulative refunds for an order must not exceed the order total | transaction | constraint | app |
| INV-PAY-004 | A transaction amount is non-negative | transaction | constraint | both |
| INV-PAY-005 | A transaction's currency equals the store currency at the time it was recorded | transaction | constraint | app |
| INV-PAY-006 | A stored payment-method configuration never contains gateway credentials in clear text | payment_method_configuration | constraint | app |

Tier notes: INV-PAY-004 is enforced at the DB tier via the `ck_transaction_amount_positive` CHECK (and re-validated in the app). INV-PAY-001/002/003/005 are cross-entity/temporal business invariants enforced in the domain layer (they depend on scanning the order's ledger and on the order total known via the refund request context — not a single-row DB constraint). INV-PAY-006 is enforced by always encrypting the config blob before write (BR-PAY-009).

## Domain Events (BV-2 / ADR-003 seam — the money-safety boundary)

Payment does NOT write order data. On settlement/refund it records its ledger row and PUBLISHES an event
that MS-09 (order service) consumes to apply order status/total in MS-09's own transaction. There is no
shared order table and no cross-service DB write. Reconciliation guarantees: no order reaches a settled
state without a CAPTURED/AuthorizeCapture transaction, and no order reaches refunded without a REFUND
transaction.

### Published: payment.captured

- **Triggered by:** BR-PAY-006 (AuthorizeCapture settlement) and BR-PAY-007 (capture of a prior authorization)
- **Consumed by:** MS-09 (order service) — applies order settled status (money order → awaiting funds)
- **Payload:**
  ```json
  {
    "transactionId": "TX-9001",
    "orderId": "ORD-5001",
    "amount": 129.90,
    "currency": "USD",
    "transactionType": "Capture",
    "paymentType": "CreditCard",
    "timestamp": "2026-01-01T12:00:00Z"
  }
  ```
- **Guarantees:** at-least-once; MS-09 consumer is idempotent on `transactionId`.

### Published: payment.refunded

- **Triggered by:** BR-PAY-012 / BR-PAY-015 (refund recorded)
- **Consumed by:** MS-09 (order service) — adds refund line, decrements order total, sets order refunded
- **Payload:**
  ```json
  {
    "transactionId": "TX-9004",
    "orderId": "ORD-5001",
    "amount": 50.00,
    "currency": "USD",
    "transactionType": "Refund",
    "timestamp": "2026-01-01T13:00:00Z"
  }
  ```
- **Guarantees:** at-least-once; MS-09 consumer is idempotent on `transactionId`.

## Cross-Service / External References (NOT owned)

| Reference | Owner | How accessed |
|-----------|-------|--------------|
| Order status / total updates | MS-09 order-service | Applied by MS-09 consuming `payment.captured` / `payment.refunded` (event, NOT a DB write here) |
| Merchant store + currency | MS-03 store-service | Reference read (store currency authoritative per BR-PAY-001) |
| Country / region reference | MS-01 reference-data | Reference read (region eligibility, BR-PAY-010) |
| External payment gateways (PayPal, authorize.net, etc.) | External PSPs | Plug-in via PaymentModule SPI (EXT-PAY-001) — gateway internals OUT OF SCOPE |

## Extension Point (Layer B)

- **EXT-PAY-001 — Payment gateway plug-in engine.** Mechanism: plug-in interface (PaymentModule SPI:
  validateModuleConfiguration / initTransaction / authorize / capture / authorizeAndCapture / refund) +
  per-store encrypted config registry (`payment_method_configuration`). What varies per instance: which
  gateways are enabled, their credentials, active/default flags, transaction mode, and region eligibility.
  Used by BR-PAY-004, BR-PAY-007, BR-PAY-009, BR-PAY-012, BR-PAY-019, BR-PAY-027. See
  `spec/shared/extensibility-model.md` (to be compiled at Stage 1.8). New gateways are added by
  implementing the contract and registering — no core payment-logic change.
