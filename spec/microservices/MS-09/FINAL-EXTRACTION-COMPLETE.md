# MS-09 Order Service — FINAL EXTRACTION COMPLETE

**Service ID**: MS-09
**Status**: 🟢 Phase 4 extraction complete (pending Phase 4a human review)
**Analysis Mode**: Direct Source Read (no CAST)

## Deliverables present (9 files)

- [x] INDEX.md
- [x] 00-component-inventory.md
- [x] 01-business-rules.md (32 rules, all H3 `### BR-ORD-`)
- [x] 02-domain-model.md (10 tables, order status state machine, 7 invariants, domain events, checkout saga)
- [x] 03-api-design.md (16 endpoints)
- [x] 04-api-contract.yaml (OpenAPI 3.1, 16 operations)
- [x] 06-completion-summary.md
- [x] extraction-evidence.md
- [x] FINAL-EXTRACTION-COMPLETE.md

## Final counts (consistent across files)

| Metric | Count |
|--------|-------|
| Business rules | 32 |
| Owned tables | 10 |
| API endpoints | 16 |
| Data invariants | 7 |
| Domain events published | 1 (order.placed) |
| Domain events consumed | 2 (payment.captured, payment.refunded) |

## Key confirmations

- All 32 rule headers are H3 (`### BR-ORD-NNN:`), not H2.
- **BV-1 / ADR-001:** order is modeled as the AUTHORITATIVE totals owner — `caculateOrder` computes subtotal
  locally and folds tax (MS-07 `/calculate`) and shipping (MS-08 `/quote` + config) as SYNCHRONOUS STATELESS
  READS into the owned grand total; ordered pipeline (subtotal→shipping→handling→tax→total, sorted by
  sortOrder) preserved. Cart (MS-06) delegates its authoritative total here (BV-3).
- **BV-2 / ADR-003:** order CONSUMES `payment.captured` / `payment.refunded` (idempotent on transactionId) and
  PUBLISHES `order.placed`. NO cross-service payment-writes-order path is modeled — settlement facts arrive
  only via events, applied in MS-09's own transaction.
- **D-08 / R-03:** checkout modeled as a saga (charge → persist → publish) with idempotency + a reconciliation
  net (Architecture §7: no PROCESSED order without a CAPTURED transaction). NOT 2PC.
- **Status lifecycle:** Ordered/Processed/Delivered/Refunded captured as an entity state model; the legal
  transition set is FLAGGED as not-encoded-in-legacy (4a decision) — no fabricated enforced transition map.
- **D-06 preserved-and-flagged:** BR-ORD-006 (rounding), BR-ORD-032 (download IDOR + unenforced limit),
  BR-ORD-020 (masked-PAN/CVV — PCI), BR-ORD-021 (inverted transaction branch), BR-ORD-029/status-set,
  BR-ORD-015 (count/page precedence), BR-ORD-031 (REST bypass) — preserved as-is, NOT corrected.

Not performed (per instructions): graph import, git commit.
