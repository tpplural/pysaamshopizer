# Event Schema Index — Shopizer Modernization

> **Generated in Phase 4 Stage 1.5** (Event Schema Compilation). One YAML per unique domain event;
> payload fields derived from the triggering BR-IDs' Side Effects / Data. Every published event is
> checked for at least one consumer; dead events are flagged.

## Events

| Event | Schema file | Publisher | Triggered by | Consumer(s) | Verification |
|-------|-------------|-----------|--------------|-------------|--------------|
| `payment.captured` | [payment.captured.yaml](./payment.captured.yaml) | MS-10 payment | BR-PAY-006, BR-PAY-007 | MS-09 order | ✅ has consumer |
| `payment.refunded` | [payment.refunded.yaml](./payment.refunded.yaml) | MS-10 payment | BR-PAY-015 | MS-09 order | ✅ has consumer |
| `order.placed` | [order.placed.yaml](./order.placed.yaml) | MS-09 order | BR-ORD-008, BR-ORD-025 | *(none in scope)* | ⚠️ DEAD-among-set (see note) |
| `merchant.deleted` | [merchant.deleted.yaml](./merchant.deleted.yaml) | MS-03 merchant-store | BR-MS-LIFE-002 | MS-04, MS-05, MS-06, MS-07, MS-08, MS-09, MS-10, MS-11, MS-02 | ✅ has consumers (fan-out) |

## Publisher → Consumer verification result

- **`payment.captured`** — published by MS-10 (BR-PAY-006 AuthorizeCapture, BR-PAY-007 capture),
  consumed by MS-09 (idempotent on `transactionId`, INV-ORD-007). **Producer/consumer payloads agree**
  (both reference `transactionId, orderId, amount, currency, transactionType, paymentType, timestamp`).
- **`payment.refunded`** — published by MS-10 (BR-PAY-015), consumed by MS-09 (idempotent on
  `transactionId`). **Producer/consumer payloads agree** (`transactionId, orderId, amount, currency,
  transactionType, timestamp`).
- **`order.placed`** — published by MS-09 (BR-ORD-008 / BR-ORD-025). **No consumer exists among the 11
  in-scope services.** Its intended consumers (notifications, analytics, fulfillment) are downstream
  capabilities that were NOT scoped into this engagement. Cart teardown at checkout is a direct
  `DELETE /carts/{code}` from MS-09 (BR-ORD-025), NOT a consumption of this event.
  **→ Flagged as a DEAD-among-set event: intentional, not a defect.** No action required beyond keeping
  the schema published for the future downstream consumers.
- **`merchant.deleted`** — published by MS-03 (BR-MS-LIFE-002), consumed by all 8 store-scoped services
  (+ identity-admin). Discovered during compilation; not among the 3 originally-listed events but a
  real, rule-backed fan-out. All consumers own store-scoped data to purge. **Has consumers.**

## Dead-event summary

| Event | Dead? | Rationale |
|-------|-------|-----------|
| `order.placed` | Dead among the 11 in-scope services | Downstream notification/analytics/fulfillment consumers are out of scope; intentional. |

No event is published without a *defined* consumer intent. Only `order.placed` lacks an in-scope
consumer, and that is by design (downstream is out of scope).

## Notes on transport

The messaging transport is selected in `spec/shared/09-dependency-versions.md` (Redis Streams for the
v1 target — see that file for the pinned client and the rationale). All events are at-least-once with
consumer-side idempotency (payment events dedupe on `transactionId`; `order.placed` on `orderId`;
`merchant.deleted` on `merchantId`).
