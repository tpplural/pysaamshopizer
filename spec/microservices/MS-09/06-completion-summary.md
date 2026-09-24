# MS-09 Order Service — Completion Summary

**Service ID**: MS-09
**Service Name**: order-service
**Port**: 8009
**Schema**: `order_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Analysis Mode**: Direct Source Read (no CAST)
**Status**: 🟡 Phase 4 extraction complete — pending Phase 4a review

## Counts (authoritative — match across all files)

| Metric | Count |
|--------|-------|
| Business rules (BR-ORD) | 32 |
| Owned tables | 10 |
| API endpoints | 16 |
| Data invariants (INV-ORD) | 7 |
| Domain events published | 1 (order.placed) |
| Domain events consumed | 2 (payment.captured, payment.refunded) |
| Source files read (in scope) | 22 |

## Rule inventory (32)

BR-ORD-001 … BR-ORD-032 (single group ORD, contiguous). No sub-rules, no folds, no splits — the Phase 1
catalog was one BR per behavioral seam and the deep read confirmed that grouping is faithful.

## Decomposition outcome (anti-number-chasing)

This is NOT a target-fitted count. 32 rules = the Phase 1 order catalog (32 rules over the order segment)
carried into Phase 4 and re-grounded against actual source, with the SAME BR-IDs preserved 1:1. The deep
read did not mechanically slice by proc — several source procedures decompose into multiple behavioral-seam
rules (e.g. `caculateOrder` → BR-ORD-001/002/003/004/005/006 along the pipeline seams; `process` →
BR-ORD-008/009), and multiple source sites collapse into one rule (BR-ORD-019 spans facade + controller;
BR-ORD-025 spans commit + pre-authorized commit). Net-new findings the deep read produced beyond P1 surface:

- **Net-new (architecture — BV-1):** the totals pipeline modeled with tax (MS-07) and shipping (MS-08) as
  SYNCHRONOUS STATELESS calculator reads folded into the OWNED grand total, with the ordered pipeline
  (subtotal→shipping→handling→tax→total, sorted by sortOrder) preserved. Order is the single source of truth.
- **Net-new (architecture — BV-2/ADR-003):** the legacy `PaymentServiceImpl` direct order-write is REPLACED
  by MS-09 CONSUMING `payment.captured` / `payment.refunded` and applying order state in its own transaction,
  idempotent on `transactionId` (INV-ORD-007). No cross-service order DB write is modeled.
- **Net-new (architecture — D-08):** the checkout charge-vs-persist window modeled as a SAGA (charge → persist
  → publish `order.placed`) with an idempotency key + a reconciliation net (Architecture §7: no PROCESSED
  order without a CAPTURED transaction). NOT 2PC.
- **Preserved defects/exposures (D-06):** rounding intent not enforced (BR-ORD-006); download IDOR + unenforced
  download-limit (BR-ORD-032); inverted transaction branch dropping pre-auth linkage (BR-ORD-021); free/unguarded
  status assignment — legal transition set NOT encoded (BR-ORD-029 + status lifecycle); masked-PAN + embedded
  CVV persistence PCI concern (BR-ORD-020); count/page filter precedence divergence (BR-ORD-015). All preserved
  as-is and flagged, NOT corrected.

## Totals pipeline coverage (BV-1 / ADR-001)

`OrderServiceImpl.caculateOrder` is the authoritative total engine. Subtotal computed locally (BR-ORD-001);
shipping (BR-ORD-002) + handling (BR-ORD-003) + tax lines (BR-ORD-004) folded in from MS-08/MS-07 as sync
reads; grand-total line + fixed display ordering (BR-ORD-005). Rounding intent preserved-and-flagged
(BR-ORD-006). Cart (MS-06) delegates its authoritative grand total here (BV-3). Order OWNS the total.

## Event modeling (BV-2 / ADR-003)

- **PUBLISHES** `order.placed` on successful checkout (BR-ORD-008/025).
- **CONSUMES** `payment.captured` → set order settled/Processed (money order → awaiting funds); idempotent on
  transactionId.
- **CONSUMES** `payment.refunded` → add refund total line, decrement total, set Refunded; idempotent on
  transactionId (INV-ORD-005/007).
- NO direct cross-service payment-writes-order path is modeled. Settlement facts arrive only via events.

## Checkout saga + reconciliation (D-08 / R-03)

Checkout = saga: CHARGE (MS-10, idempotent on checkout key) → PERSIST (local tx: order + initial status
history) → PUBLISH `order.placed`. The charge-vs-persist window is closed by a reconciliation job enforcing
the Architecture §7 money-safety invariant (no PROCESSED order without a CAPTURED transaction; orphan
charges compensated). NOT 2PC, no shared cross-service transaction.

## Order status lifecycle

States Ordered (initial) → Processed → Delivered / Refunded. Current status on `orders.order_status`;
append-only `order_status_history` audit (BR-ORD-009/010/029). **FLAG [D-06]:** the legacy encodes NO legal
transition map — status is set by free assignment (`OrderControler.saveOrder:341`). The transition table in
02-domain-model.md is the OBSERVED/intended forward flow, NOT an enforced map; the legal transition set
(forward-only? Delivered→Refunded? Refunded terminal?) is a 4a decision. App enforces only status ∈ enum
(INV-ORD-004) until then — no fabricated enforced map.

## D-06 preserved-and-flagged rules

- **BR-ORD-006** — monetary rounding intent not enforced at the calc layer (setScale result discarded); canonical scale/rounding is a 4a decision. `Preservation: FLAGGED [D-06 PRESERVED-AS-IS]`.
- **BR-ORD-032** — download path (a) no owner check → potential IDOR; (b) no downloadCount increment / no maxdays enforcement (fields exist: DOWNLOAD_MAXDAYS default 31, DOWNLOAD_COUNT). `Preservation: FLAGGED [D-06 PRESERVED-AS-IS]`.
- **BR-ORD-029 + status lifecycle** — legal transition set NOT encoded in legacy; captured as observed and flagged (do not invent an enforced map).
- **BR-ORD-020** — persisted masked PAN + embedded CVV/owner/expiry — PCI/PII; target should tokenize/never-persist; masking preserved. `FLAGGED [D-06]`.
- **BR-ORD-021** — inverted transaction-branch drops pre-auth linkage — likely defect, preserved + flagged.
- **BR-ORD-015** — count/page filter operator-precedence divergence — Low confidence, flagged.
- **BR-ORD-031** — integration REST path bypasses payment/status orchestration — behavioral divergence, flagged.

## Endpoint coverage (16)

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /calculate-total | POST | COVERED | BR-ORD-001..007, 017 |
| /shipping-summary | POST | COVERED | BR-ORD-024 |
| /checkout-context | GET | COVERED | BR-ORD-023, 026 |
| /validate | POST | COVERED | BR-ORD-019, 020, 022 |
| /payment/init/{paymentMethod} | POST | COVERED | BR-ORD-027 |
| / (place order) | POST | COVERED | BR-ORD-008, 009, 018..021, 025 |
| /integration/orders | POST | COVERED | BR-ORD-031 |
| /{orderId} | GET | COVERED | BR-ORD-014 |
| / (list) | GET | COVERED | BR-ORD-015 |
| /{orderId} | PUT | COVERED | BR-ORD-011 |
| /{orderId}/status | PATCH | COVERED | BR-ORD-010, 029 |
| /{orderId}/confirmation | GET | COVERED | BR-ORD-028 |
| /{orderId}/invoice | GET | COVERED | BR-ORD-013 |
| /{orderId}/downloads | GET | COVERED | BR-ORD-012, 016 |
| /{orderId}/downloads/{downloadId}/file | GET | COVERED | BR-ORD-032 |
| /{orderId}/refund | POST | COVERED | BR-ORD-030 |

## Items requiring human clarification (carried to Phase 4a)

- BR-ORD-006: canonical monetary scale/rounding rule (setScale discarded in legacy).
- BR-ORD-021: inverted transaction-branch — fix (forward pre-auth transaction) vs preserve.
- BR-ORD-032: download ownership check (IDOR) + download-limit enforcement (maxdays/downloadCount) — known gap or intended?
- CustomerOrdersController order-detail access control (fetch by orderId without customer-ownership check).
- BR-ORD-020 / PCI: confirm tokenize / never-persist policy; is CVV ever persisted?
- Order status lifecycle: the intended LEGAL transition set (forward-only? Delivered→Refunded only? Refunded terminal?) — needed to finalize the closed machine.
- BR-ORD-015: count vs page filter precedence semantics for order search.
- BR-ORD-031: is the REST integration channel a legitimate order-entry path with different rules, or should it converge on checkout orchestration?
- SCOPE: order_account / order_account_product / file_history are unwired recurring-billing + download-accounting scaffolding — in or out of the modernization target?
- INV-ORD-002 total-consistency + INV-ORD-001 status-history triggers: confirm DB-tier enforcement acceptable.
