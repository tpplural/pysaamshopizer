# MS-09 Order Service — API Design

**Service ID**: MS-09
**Base path**: `/api/v1/orders`
**Port**: 8009
**Naming**: snake_case fields, snake_case query params, kebab-case paths, PascalCase enum values (shared-convention reconciliation, 2026-09-19)
**Global header**: `x-tenant-id` (required on every request); `x-store-id` (**required** on all order + checkout + config operations — Concern B fix, was optional)

## Endpoints (16)

| # | Method | Endpoint | Description | Driven by |
|---|--------|----------|-------------|-----------|
| 1 | POST | /api/v1/orders/calculate-total | Compute the authoritative order total (owns total; calls tax + shipping as sync reads) | BR-ORD-001, 002, 003, 004, 005, 006, 007, 017 |
| 2 | POST | /api/v1/orders/shipping-summary | Derive the shipping summary from a selected quote option | BR-ORD-024 |
| 3 | GET | /api/v1/orders/checkout-context | Resolve cart + payment methods + prefilled customer for checkout | BR-ORD-023, 026 |
| 4 | POST | /api/v1/orders/validate | Validate a checkout submission (billing/delivery/payment/shipping/card) | BR-ORD-019, 020, 022 |
| 5 | POST | /api/v1/orders/payment/init/{paymentMethod} | Initiate a PayPal Express pre-authorization | BR-ORD-027 |
| 6 | POST | /api/v1/orders | Place an order (checkout saga: charge → persist → publish order.placed) | BR-ORD-008, 009, 018, 019, 020, 021, 025 |
| 7 | POST | /api/v1/integration/orders | Integration channel: create an order without payment orchestration | BR-ORD-031 |
| 8 | GET | /api/v1/orders/{orderId} | Fetch the full order aggregate | BR-ORD-014 |
| 9 | GET | /api/v1/orders | List store orders with filters + paging | BR-ORD-015 |
| 10 | PUT | /api/v1/orders/{orderId} | Save/update an order (create-vs-update discriminator) | BR-ORD-011 |
| 11 | PATCH | /api/v1/orders/{orderId}/status | Admin status change + audit history entry | BR-ORD-010, 029 |
| 12 | GET | /api/v1/orders/{orderId}/confirmation | Confirmation view with cross-store ownership guard | BR-ORD-028 |
| 13 | GET | /api/v1/orders/{orderId}/invoice | Generate the order invoice (PDF) | BR-ORD-013 |
| 14 | GET | /api/v1/orders/{orderId}/downloads | List an order's downloadable products | BR-ORD-012, 016 |
| 15 | GET | /api/v1/orders/{orderId}/downloads/{downloadId}/file | Stream a digital product file (IDOR + limits FLAG) | BR-ORD-032 |
| 16 | POST | /api/v1/orders/{orderId}/refund | Admin refund (delegates to payment; settlement via event) | BR-ORD-030 |

## Notes

- **BV-1 (order owns the total):** endpoint 1 (`calculate-total`) is the authoritative total engine. It
  computes the subtotal locally, then calls tax (MS-07 `/calculate`) and shipping (MS-08 `/quote` + config)
  as SYNCHRONOUS STATELESS READS and folds their results into its own computation (BR-ORD-001..005). The cart
  service (MS-06) delegates its authoritative grand total to this endpoint.
- **BV-2 (order consumes payment events):** endpoint 16 (`refund`) and the capture action delegate to MS-10;
  the resulting settlement facts arrive as `payment.captured` / `payment.refunded` which MS-09 CONSUMES
  (idempotent on transaction_id). There is NO endpoint by which payment writes order state directly.
- **D-08 (checkout saga):** endpoint 6 (`POST /orders`) runs the saga (charge → persist → publish
  `order.placed`) with an `idempotency_key`. The charge-vs-persist window is closed by the reconciler
  (no PROCESSED order without a CAPTURED transaction). NOT 2PC.
- Endpoint 11 (`PATCH .../status`) sets status by the OBSERVED lifecycle; the legal transition set is NOT
  enforced (legacy encodes none — 4a decision). The app validates only status ∈ enum + writes a history row.
- Endpoint 15 preserves the legacy download behavior (no ownership check → IDOR; no count increment / no
  max-days enforcement) as-is and FLAGS it (D-06) — target should return 403 + enforce limits.
- Endpoints 8, 9, 12, 13, 14, 15 are reads. Endpoints 6, 7, 10, 11, 16 mutate order state (or delegate).

## Total-engine dependency (BV-1)

`POST /calculate-total` is the single source of truth for order totals. Tax and shipping are cross-service
calculators consumed synchronously here; the total aggregation and grand-total line are OWNED by MS-09. The
ordered pipeline (subtotal → shipping → handling → tax lines → grand total, sorted by sort_order) is preserved.
