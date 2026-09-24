# MS-10 Payment Service — Spec Index

## Service Metadata

| Attribute | Value |
|-----------|-------|
| Service ID | MS-10 |
| Service Name | payment-service |
| Port | 8010 |
| Database Schema | `payment_schema` |
| Target Stack | Python / FastAPI + PostgreSQL 15+ |
| Analysis Mode | Direct Source Read (no CAST) |
| Status | 🟡 Phase 4 extraction complete — pending Phase 4a |

## Counts (authoritative — consistent across all files)

| Metric | Count |
|--------|-------|
| Business rules (BR-PAY) | 31 |
| Owned tables | 2 |
| API endpoints | 12 |
| Data invariants (INV-PAY) | 6 |
| Domain events published | 2 |
| Extension points | 1 |

## Purpose

MS-10 owns payment orchestration, the transaction ledger, payment-method configuration, and the pluggable
payment-gateway SPI. Under BV-2/ADR-003 it owns ONLY its transaction ledger + payment-method configuration;
on capture/refund it publishes `payment.captured` / `payment.refunded` events consumed by MS-09 (order
service). There is NO cross-service order DB write — money-safety is guaranteed by reconciliation.

## Files

| File | Content |
|------|---------|
| `00-component-inventory.md` | Legacy components, owned tables, cross-service references |
| `01-business-rules.md` | 31 BR-PAY rules (H3 headers) with semantic preservation + examples |
| `02-domain-model.md` | DDL (2 tables), transaction state machine, 6 invariants, domain events, EXT-PAY-001 |
| `03-api-design.md` | 12 endpoints mapped to BR-IDs |
| `04-api-contract.yaml` | OpenAPI 3.1 — 12 operations |
| `06-completion-summary.md` | Counts, coverage, decomposition outcome, clarifications |
| `extraction-evidence.md` | 13 source files read; black-box call register |
| `FINAL-EXTRACTION-COMPLETE.md` | Sign-off marker |

## Owned tables

- `transaction` (legacy SM_TRANSACTION)
- `payment_method_configuration` (legacy SM_MERCHANT_CONFIGURATION encrypted PAYMENT config)

## Domain events (BV-2/ADR-003 seam)

- `payment.captured` → consumed by MS-09
- `payment.refunded` → consumed by MS-09

## Extension point

- `EXT-PAY-001` — Payment gateway plug-in engine (PaymentModule SPI + per-store encrypted config)

## D-06 preserved-and-flagged

- BR-PAY-022 (brand validation dead code) and BR-PAY-026 (unreachable guard) — preserved as-is, flagged for 4a.
