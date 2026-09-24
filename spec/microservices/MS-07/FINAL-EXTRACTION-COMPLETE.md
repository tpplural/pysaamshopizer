# MS-07 (tax) — FINAL EXTRACTION COMPLETE

**Service ID**: MS-07
**Status**: 🟢 100% COMPLETE — Phase 4 spec package
**Analysis mode**: Direct Source Read (no CAST)
**Date**: 2026-02-14

## Authoritative Counts (identical across INDEX.md and 06-completion-summary.md)

| Metric | Count |
|--------|-------|
| Business rules (BR-TAX-001 … BR-TAX-028) | 28 |
| Semantic Preservation tables | 28 |
| Owned tables | 4 |
| Data invariants (INV-TAX-001 … INV-TAX-012) | 12 |
| API endpoints / OpenAPI operations | 13 |
| D-06 preserved-and-flagged rules | 4 (BR-TAX-003, 007, 019, 023) |

## Deliverables Checklist

- [x] `INDEX.md`
- [x] `00-component-inventory.md`
- [x] `01-business-rules.md` — 28 rules, each with Statement (domain terms only), Intent, Logic, Source Reference (backtick `Class.java:method:lines`), 8-dimension Semantic Preservation table, and a Concrete Example (success + error)
- [x] `02-domain-model.md` — executable PostgreSQL DDL (4 tables), 12 invariants
- [x] `03-api-design.md` — 13 endpoints
- [x] `04-api-contract.yaml` — OpenAPI 3.1, 13 operations, unique operationIds, all $refs resolve
- [x] `06-completion-summary.md` — verified counts, coverage, decomposition outcome, net-new findings
- [x] `extraction-evidence.md` — 15 source files read + per-component vectors
- [x] `FINAL-EXTRACTION-COMPLETE.md` (this file)

## Quality Gates

- [x] All BR-IDs numbered uniquely and contiguous (BR-TAX-001..028)
- [x] Every rule has a real source reference (backtick `Class.java:method:lines`), read this session
- [x] DDL is executable PostgreSQL with real column names traced to legacy columns / BR-IDs
- [x] Data invariants listed with enforcement tier; integrity invariants are db/both
- [x] API endpoints cover all CRUD + the calculation operation; coverage report present (11 covered, 2 CRUD-only)
- [x] No legacy table/column/method names leaked into any Statement (legacy mechanics in Logic only)
- [x] Concrete examples use real domain fields (no generic message envelopes)
- [x] calculateTax algorithm preserved exactly (compound stacking, percentage application, HALF_UP 2dp per-line rounding)
- [x] Metadata rule/table/endpoint/invariant counts equal actual content everywhere

## D-06 Preservation Confirmation

The following legacy behaviors are **preserved exactly and FLAGGED — NOT corrected**:
- **BR-TAX-007** — the tax-basis comparison (`taxBasisCalculation.name().equals(ENUM)`) is always false; the shipping/billing/store basis-override branches are dead code and tax is ALWAYS computed on the billing address. Preserved as-is; carried to Phase 4a as a known latent bug (BA decision, high business impact).
- **BR-TAX-019** — the tax-class query argument is accepted but never applied; every store+jurisdiction rate applies to every class bucket. Preserved as-is; flagged.
- **BR-TAX-003** — only the tax basis is serialized; the two collection-scope flags revert to defaults on reload. Preserved as-is; flagged.
- **BR-TAX-023** — duplicate-code tax lines are deduped to the first (the summed amount is computed but discarded). Preserved as-is; flagged.

## Boundary Notes (documented, not owned)
- Calculation is invoked by MS-09 (order) at checkout; MS-07 owns the calculation, does not persist results.
- `country_id`/`zone_id`/`language_id` are reference reads (MS-01); `merchant_store_id` is store (MS-03).
- Product tax-class association is a catalog read (MS-04) on class delete and to get an item's tax class.
- `tax_configuration` is owned by MS-07 but originates as a JSON blob in `MERCHANT_CONFIGURATION` (key `TAX_CONFIG`).

Ready for Phase 4a (Business Rule Validation). Graph import and git commit are the parent orchestrator's responsibility (NOT performed here).
