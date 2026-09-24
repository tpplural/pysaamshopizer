# MS-10 Payment Service — API Design

**Service ID**: MS-10
**Base path**: `/api/v1/payments`
**Port**: 8010
**Naming**: snake_case fields, snake_case query params, kebab-case paths, PascalCase enum values (shared-convention reconciliation, 2026-09-19)
**Global header**: `x-tenant-id` (required on every request); `x-store-id` (**required** on config + method + process operations — Concern B fix, was optional)
**Error body**: composes the shared `ErrorResponse` and adds an optional additive `message_key` (Concern E — `PaymentErrorResponse` allOf).

## Endpoints (12)

| # | Method | Endpoint | Description | Driven by |
|---|--------|----------|-------------|-----------|
| 1 | POST | /api/v1/payments/process | Process a payment (authorize / authorize+capture) for an order | BR-PAY-001, 002, 003, 004, 005, 006, 020, 021, 022, 025, 026, 029, 030 |
| 2 | POST | /api/v1/payments/initialize | Initialize a redirect/checkout token (not persisted) | BR-PAY-004, 005, 027 |
| 3 | POST | /api/v1/payments/orders/{orderId}/capture | Capture a prior authorization; publishes payment.captured | BR-PAY-007, 013 |
| 4 | POST | /api/v1/payments/orders/{orderId}/refund | Refund an order; publishes payment.refunded | BR-PAY-012, 012a, 012b, 014, 015 |
| 5 | GET | /api/v1/payments/orders/{orderId}/transactions | List an order's transactions (details rehydrated) | BR-PAY-017, 018 |
| 6 | GET | /api/v1/payments/orders/{orderId}/capturable-transaction | Get the capturable authorization for an order | BR-PAY-013 |
| 7 | GET | /api/v1/payments/orders/{orderId}/refundable-transaction | Get the refundable settled transaction for an order | BR-PAY-014 |
| 8 | GET | /api/v1/payments/methods | List region-eligible payment gateways for the store | BR-PAY-010 |
| 9 | GET | /api/v1/payments/accepted-methods | List the store's active accepted payment methods | BR-PAY-011 |
| 10 | GET | /api/v1/payments/config | Get the store's configured payment methods (decrypted metadata) | BR-PAY-008 |
| 11 | PUT | /api/v1/payments/config/{moduleCode} | Save/validate a payment-method configuration | BR-PAY-009 |
| 12 | DELETE | /api/v1/payments/config/{moduleCode} | Remove a payment-method configuration | BR-PAY-009b |

## Notes

- Endpoints 1, 3, 4 record ledger transactions. Endpoints 3 and 4 additionally publish domain events
  (`payment.captured` / `payment.refunded`) consumed by MS-09 — they do NOT write order data (BV-2/ADR-003).
- Endpoint 2 (initialize) returns a token and does NOT persist a ledger row (BR-PAY-005/027).
- Endpoints 5, 6, 7, 8, 9, 10 are read operations. `GET /methods` and `GET /accepted-methods` read store /
  gateway reference data (MS-03/MS-01) plus this service's config.
- Endpoints 11, 12 mutate `payment_method_configuration` only.
- The credit-card validation rules (BR-PAY-020/021/022/025) run inside endpoint 1 for credit-card payments.
  BR-PAY-022 brand validation is DEAD CODE preserved as-is (D-06) — only Luhn (BR-PAY-025) actually rejects.
- Card masking (BR-PAY-028) is an internal display utility, exercised where a stored card number is shown;
  it does not get its own public endpoint (no card PAN is exposed by this API).

## Gateway plug-in extension point (EXT-PAY-001)

The set of usable gateways is data-driven (per-store config) behind the PaymentModule SPI. Adding a gateway
does not add endpoints — it registers a new plug-in. `GET /methods` reflects the registered + region-eligible
gateways.
