# MS-07 (tax) — Specification Index

**Service ID**: MS-07
**Service Name**: tax
**Port**: 8007
**Database Schema**: `tax_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Status**: 🟢 100% COMPLETE
**Analysis mode**: Direct Source Read (no CAST)

## Purpose

MS-07 owns tax classes, tax rates, tax configuration, and the tax **calculation engine** — the single
place where tax is applied to an order. Catalog prices are tax-exclusive, so this engine is the sole
point tax is added. It is invoked by the order service (MS-09) at checkout.

## Metadata (authoritative counts — must match across all files)

| Metric | Count |
|--------|-------|
| Business rules | 28 |
| Rule group | BR-TAX (BR-TAX-001 … BR-TAX-028) |
| Owned tables | 4 |
| Data invariants | 12 |
| API endpoints | 13 |
| Preserved-and-flagged (D-06) rules | 4 (BR-TAX-003, BR-TAX-007, BR-TAX-019, BR-TAX-023) |

## Files

| File | Contents |
|------|----------|
| `00-component-inventory.md` | Legacy components in scope + disposition |
| `01-business-rules.md` | 28 business rules (BR-TAX-001..028), 8-dimension preservation tables, concrete examples |
| `02-domain-model.md` | Executable PostgreSQL DDL (4 tables), 12 data invariants |
| `03-api-design.md` | 13 API endpoints with rule coverage |
| `04-api-contract.yaml` | OpenAPI 3.1 contract (13 operations) |
| `06-completion-summary.md` | Verified counts, coverage, preservation, decomposition outcome |
| `extraction-evidence.md` | Source files actually read + per-component vectors |
| `FINAL-EXTRACTION-COMPLETE.md` | Sign-off checklist |

## Preservation Decision D-06 (preserve current behavior, do NOT fix)
- **BR-TAX-007** — tax-basis comparison is always false; jurisdiction is ALWAYS the billing address (basis-override branches are dead code). Preserved + flagged.
- **BR-TAX-019** — the tax-class argument does not filter the rate query; every store rate applies to every class. Preserved + flagged.
- **BR-TAX-003** — only the tax basis is persisted; the two collection flags revert to defaults on reload. Preserved + flagged.
- **BR-TAX-023** (net-new, same defect class) — duplicate-code tax lines are deduped to the first, not summed (sum computed but discarded). Preserved + flagged.
