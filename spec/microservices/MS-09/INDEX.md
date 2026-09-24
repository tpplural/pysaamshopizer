# MS-09 Order Service — Spec Index

## Service Metadata

| Attribute | Value |
|-----------|-------|
| Service ID | MS-09 |
| Service Name | order-service |
| Port | 8009 |
| Database Schema | `order_schema` |
| Target Stack | Python / FastAPI + PostgreSQL 15+ |
| Analysis Mode | Direct Source Read (no CAST) |
| Status | 🟡 Phase 4 extraction complete — pending Phase 4a |

## Counts (authoritative — consistent across all files)

| Metric | Count |
|--------|-------|
| Business rules (BR-ORD) | 32 |
| Owned tables | 10 |
| API endpoints | 16 |
| Data invariants (INV-ORD) | 7 |
| Domain events published | 1 |
| Domain events consumed | 2 |

## Purpose

MS-09 is the orchestrator hub and the authoritative order-totals engine. It owns the order aggregate, order
products, the ordered order-total pipeline, the order status lifecycle, and checkout/order-placement
orchestration. Under BV-1/ADR-001 it OWNS the order total — tax (MS-07) and shipping (MS-08) are synchronous
stateless calculator reads folded into the owned computation. Under BV-2/ADR-003 it CONSUMES
`payment.captured` / `payment.refunded` from MS-10 and applies order state in its own transaction
(idempotent on transactionId) — there is NO cross-service order write from payment. Checkout is a saga
(charge → persist → publish `order.placed`) with idempotency + reconciliation, NOT 2PC (D-08).

## Files

| File | Content |
|------|---------|
| `00-component-inventory.md` | Legacy components, 10 owned tables, cross-service references |
| `01-business-rules.md` | 32 BR-ORD rules (H3 headers) with 8-dim semantic preservation + examples |
| `02-domain-model.md` | DDL (10 tables), order status state machine, 7 invariants, domain events, checkout saga |
| `03-api-design.md` | 16 endpoints mapped to BR-IDs |
| `04-api-contract.yaml` | OpenAPI 3.1 — 16 operations |
| `06-completion-summary.md` | Counts, coverage, decomposition outcome, clarifications |
| `extraction-evidence.md` | 22 source files read; black-box call register |
| `FINAL-EXTRACTION-COMPLETE.md` | Sign-off marker |

## Owned tables (10)

- `orders` (legacy ORDERS)
- `order_product` (legacy ORDER_PRODUCT)
- `order_total` (legacy ORDER_TOTAL)
- `order_status_history` (legacy ORDER_STATUS_HISTORY)
- `order_product_price` (legacy ORDER_PRODUCT_PRICE)
- `order_product_download` (legacy ORDER_PRODUCT_DOWNLOAD)
- `order_product_attribute` (legacy ORDER_PRODUCT_ATTRIBUTE)
- `order_account` (legacy ORDER_ACCOUNT — recurring-billing scaffolding, 4a scope)
- `order_account_product` (legacy ORDER_ACCOUNT_PRODUCT — recurring-billing scaffolding)
- `file_history` (legacy FILE_HISTORY — download accounting, unused by download path)

## Architecture seams

- **BV-1 / ADR-001 — totals engine:** order OWNS the total; tax (MS-07) + shipping (MS-08) are sync reads.
- **BV-2 / ADR-003 — payment events:** CONSUMES `payment.captured` / `payment.refunded` (idempotent on transactionId); PUBLISHES `order.placed`. No cross-service order write.
- **D-08 / R-03 — checkout saga:** charge → persist → publish, idempotency + reconciliation (no PROCESSED order without a CAPTURED transaction). NOT 2PC.

## Domain events

- Published: `order.placed` → downstream (notifications/fulfillment/analytics)
- Consumed: `payment.captured` (from MS-10) → set order settled/Processed
- Consumed: `payment.refunded` (from MS-10) → refund line + decrement + set Refunded

## Order status lifecycle

Ordered (initial) → Processed → Delivered / Refunded. **FLAG [D-06]:** the legal transition set is NOT
encoded in legacy (free assignment) — captured as observed, finalized at 4a (no fabricated enforced map).

## D-06 preserved-and-flagged

- BR-ORD-006 (rounding intent not enforced), BR-ORD-032 (download IDOR + unenforced download-limit),
  BR-ORD-020 (masked-PAN/CVV persistence — PCI), BR-ORD-021 (inverted transaction branch), BR-ORD-029 +
  status lifecycle (transition set not encoded), BR-ORD-015 (count/page precedence), BR-ORD-031 (REST path
  bypasses orchestration) — all preserved as-is and flagged for 4a.
