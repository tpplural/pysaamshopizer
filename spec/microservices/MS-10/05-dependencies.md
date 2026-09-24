# Dependencies: payment (MS-10)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-10 is the SOURCE + documented domain events.

## Services Consumed

### order (MS-09) — realized as EVENTS, NOT a synchronous REST call (BV-2 / ADR-003)

The graph shows an MS-10 → MS-09 edge, but the specs decide its realization: **payment does NOT make a
synchronous REST write to order.** In the legacy `PaymentServiceImpl`, capture/refund wrote
`ORDERS` / `ORDER_TOTAL` / `ORDER_STATUS_HISTORY` directly (a cross-domain DB write). In the modernized
design that is FORBIDDEN — payment owns only its transaction ledger and PUBLISHES domain events; the
order service (MS-09) consumes them and applies order state in its own transaction, idempotent on
`transaction_id`. **This edge is therefore realized entirely by the two published events below**, not by
any REST call to MS-09.

payment makes no other outgoing SAAM-service calls. Its only external interaction is the payment
gateway via the SPI (EXT-PAY-001), which is a third-party PSP, not a SAAM microservice.

## Events Published

### Publishes: `payment.captured`
- **Triggered by:** BR-PAY-006 (order settlement signalled by event on AuthorizeCapture) and BR-PAY-007 (capture a prior authorization)
- **Channel:** `payment.captured`
- **Schema:** see `spec/shared/event-schemas/payment.captured.yaml`
  ```json
  { "transaction_id": "TX-9001", "order_id": "ORD-5001", "amount": 129.90, "currency": "USD",
    "transaction_type": "Capture", "payment_type": "CreditCard", "timestamp": "2026-01-01T12:00:00Z" }
  ```
  (Emitted on both single-step AuthorizeCapture — `transaction_type: "AuthorizeCapture"` — and capture
  of a prior authorization — `transaction_type: "Capture"`.)
- **Consumed by:** MS-09 order (applies settled/PROCESSED, or "awaiting funds" for MoneyOrder; appends status history; idempotent on `transaction_id`).
- **Guarantees:** at-least-once
- **Ordering:** by `order_id`

### Publishes: `payment.refunded`
- **Triggered by:** BR-PAY-015 (refund event — order-total decrement and refund line, consumed by order service)
- **Channel:** `payment.refunded`
- **Schema:** see `spec/shared/event-schemas/payment.refunded.yaml`
  ```json
  { "transaction_id": "TX-9004", "order_id": "ORD-5001", "amount": 50.00, "currency": "USD",
    "transaction_type": "Refund", "timestamp": "2026-01-01T12:05:00Z" }
  ```
- **Consumed by:** MS-09 order (appends the refund total line, decrements the order total, sets Refunded; idempotent on `transaction_id`).
- **Guarantees:** at-least-once
- **Ordering:** by `order_id`

## Events Consumed

- **`merchant.deleted`** (from MS-03) — payment owns store-scoped payment-method configuration; on
  store decommission it purges that store's configuration (BR-MS-LIFE-002 fan-out consumer). The
  transaction ledger is retained for audit/reconciliation. Inbound event, not an outgoing call.

## Inbound (for reference — NOT this service's dependencies)

- **MS-09 order** calls payment's charge endpoints synchronously as the checkout saga CHARGE step:
  `POST /process` (`processPayment`), `POST /orders/{orderId}/capture` (`capturePayment`),
  `POST /orders/{orderId}/refund` (`refundPayment`). Those are modeled as outgoing dependencies in
  `MS-09/05-dependencies.md`. The settlement result flows BACK to order via the events above — not via
  a payment→order REST write.

## Reconciliation (integration dimension)

- specIntegrations written into this file: **0 outbound sync SAAM-service calls**; **2 published events** (`payment.captured`, `payment.refunded`); 1 external PSP gateway (EXT-PAY-001, not a SAAM service).
- Integration count implied by MS-10 rules: **2 event publishes** (BR-PAY-006/007 → `payment.captured`, BR-PAY-015 → `payment.refunded`); no sync REST to order (BV-2). Gateway call via EXT-PAY-001.
- **Status: MATCH** — the MS-10 → MS-09 edge is correctly realized as events, not a REST write.
