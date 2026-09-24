# MS-10 Payment Service — Completion Summary

**Service ID**: MS-10
**Service Name**: payment-service
**Port**: 8010
**Schema**: `payment_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Analysis Mode**: Direct Source Read (no CAST)
**Status**: 🟡 Phase 4 extraction complete — pending Phase 4a review

## Counts (authoritative — match across all files)

| Metric | Count |
|--------|-------|
| Business rules (BR-PAY) | 31 |
| Owned tables | 2 |
| API endpoints | 12 |
| Data invariants (INV-PAY) | 6 |
| Domain events published | 2 (payment.captured, payment.refunded) |
| Extension points | 1 (EXT-PAY-001) |
| Source files read (in scope) | 13 |

## Rule inventory (31)

BR-PAY-001, 002, 003, 004, 005, 006, 007, 008, 009, **009b**, 010, 011, 012, **012a**, **012b**, 013, 014,
015, 016, 017, 018, 019, 020, 021, 022, 025, 026, 027, 028, 029, 030.

- Sub-rule ids: BR-PAY-009b, BR-PAY-012a, BR-PAY-012b (importer regex supports trailing lowercase letter).
- BR-PAY-023 (Amex) and BR-PAY-024 (Diners/Discovery) are FOLDED into BR-PAY-022 (same enum-vs-String dead-code defect).

## Decomposition outcome (anti-number-chasing)

This is NOT a target-fitted count. It is the Phase 1 catalog (31 rules over the payment segment) carried
into Phase 4 and re-grounded against the actual source, with the exact same BR-IDs preserved. The deep read
confirmed P1's grouping was faithful and surfaced concrete net-new findings the spec now records:

- **Net-new (design correction):** BR-PAY-018 modernized with a deterministic `ORDER BY (transaction_date, transaction_id)` to eliminate the legacy `listByOrder` no-ORDER-BY correctness hazard that BR-PAY-013/014 depend on.
- **Net-new (money-safety architecture):** BR-PAY-006/007/015 re-modeled from direct cross-domain ORDER writes into `payment.captured` / `payment.refunded` domain events consumed by MS-09 (BV-2/ADR-003) — a service-boundary correction that did not exist at P1 surface level.
- **Net-new (precision):** transaction `amount` and refund comparisons modeled as exact `NUMERIC(19,4)` to fix the legacy `double` comparison in BR-PAY-012a/012b (flagged for 4a).
- **Preserved defects (D-06):** BR-PAY-022 brand validation dead code and BR-PAY-026 unreachable guard preserved exactly and flagged — not corrected.

## Transaction state machine coverage

States: Init (transient), Authorize, AuthorizeCapture, Capture, Refund. Transitions driven by BR-PAY-004/005
(entry), BR-PAY-007 (Authorize→Capture), BR-PAY-012 (settled→Refund). Ledger is append-only (each state is a
new row). Closed-machine verified in 02-domain-model.md. No PARTIALLY_REFUNDED state (flagged for 4a).

## Credit-card validation coverage

BR-PAY-020 (orchestration) → BR-PAY-021 (expiry, no-upper-bound-on-month quirk preserved) → BR-PAY-022 (brand
length/prefix — DEAD CODE, preserved + flagged) → BR-PAY-025 (Luhn — the only check that actually runs).
BR-PAY-028 (display masking, fixed-width) preserved.

## BV-2 / ADR-003 event-emission modeling

Payment owns ONLY `transaction` + `payment_method_configuration`. On capture/refund it records the ledger row
and publishes `payment.captured` / `payment.refunded` (payload: transactionId, orderId, amount, currency,
transactionType, timestamp). MS-09 (order service) consumes these and applies order status/total in its own
transaction. NO shared order table, NO cross-service ORDER DB write. Money-safety guaranteed by reconciliation.

## D-06 preserved-and-flagged rules

- **BR-PAY-022** (+ folded 023/024): brand validation is dead code (`CreditCardType.X.equals(creditCard.name())` always false). `Preservation: FLAGGED [D-06 PRESERVED-AS-IS]`. To Phase 4a.
- **BR-PAY-026**: capture-via-processPayment guard unreachable. `Preservation: FLAGGED [D-06 PRESERVED-AS-IS]`. To Phase 4a.

## Endpoint coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /process | POST | COVERED | BR-PAY-001..006, 020-022, 025, 026, 029, 030 |
| /initialize | POST | COVERED | BR-PAY-004, 005, 027 |
| /orders/{orderId}/capture | POST | COVERED | BR-PAY-007, 013 |
| /orders/{orderId}/refund | POST | COVERED | BR-PAY-012, 012a, 012b, 014, 015 |
| /orders/{orderId}/transactions | GET | COVERED | BR-PAY-017, 018 |
| /orders/{orderId}/capturable-transaction | GET | COVERED | BR-PAY-013 |
| /orders/{orderId}/refundable-transaction | GET | COVERED | BR-PAY-014 |
| /methods | GET | COVERED | BR-PAY-010 |
| /accepted-methods | GET | COVERED | BR-PAY-011 |
| /config | GET | COVERED | BR-PAY-008 |
| /config/{moduleCode} | PUT | COVERED | BR-PAY-009 |
| /config/{moduleCode} | DELETE | COVERED | BR-PAY-009b |

## Items requiring human clarification (carried to Phase 4a)

- BR-PAY-022/023/024: brand validation intentionally disabled vs defect to reimplement — BA decision (D-06).
- BR-PAY-026: should modernized service explicitly reject CAPTURE/INIT/REFUND in the transaction config key?
- BR-PAY-014: refund-target selection precedence + dead REFUND branch; should prior partial refunds reduce the refundable base at selection time?
- BR-PAY-012a/012b: double vs BigDecimal comparison for money (modernized as NUMERIC — confirm).
- BR-PAY-018/013/014: legacy ordering hazard (modernized with deterministic ORDER BY — confirm intended order).
- SECURITY/PCI: legacy persists PAN/CVV on the order; confirm tokenize/never-persist policy.
- SECURITY: encryption key management/rotation for gateway credentials.
- DATA_OWNERSHIP: capture/refund order-state transitions are event-driven (ADR-003) — confirmed by BV-2.
- BR-PAY-027: should INIT be a first-class SPI operation in the target design?
