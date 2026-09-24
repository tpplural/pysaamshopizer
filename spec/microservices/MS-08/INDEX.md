# MS-08 Shipping Service — Spec Index

**Service ID**: MS-08
**Service Name**: shipping
**Port**: 8008
**Schema**: `shipping_schema`
**Target stack**: Python / FastAPI + PostgreSQL 15+
**Analysis mode**: Direct Source Read (no CAST)
**Status**: 🟢 Extraction complete

## Purpose

Owns shipping-quote orchestration (the checkout quote pipeline), packaging (box bin-packing and per-item),
shipping configuration, free-shipping policy, shipping-option price selection, the custom weight-based
quote engine, and admin authoring of shipping configuration. Hosts pluggable quote providers behind a
provider extension point; external carrier gateways (UPS/USPS/CanadaPost) are out of scope.

## Metadata

| Attribute | Value |
|-----------|-------|
| Business rules | 34 (BR-SHIP-001..034, single group) |
| Owned relational tables | 4 (configuration documents) |
| Data invariants | 9 (INV-SHIP-001..009) |
| API endpoints | 20 |
| Extension points | 2 (EXT-SHIP-001, EXT-SHIP-002) |
| Greenfield rules | 0 |

## Files

| File | Contents |
|------|----------|
| `00-component-inventory.md` | Legacy components mapped to this service (in-scope + out-of-scope carriers) |
| `01-business-rules.md` | 34 business rules (BR-SHIP-001..034) with 8-dimension preservation tables + examples |
| `02-domain-model.md` | 4 configuration-document tables + 9 invariants (no persisted transactional entity) |
| `03-api-design.md` | 20 endpoints |
| `04-api-contract.yaml` | OpenAPI 3.1 — 20 operations |
| `06-completion-summary.md` | Verified counts, coverage, preserved quirks, net-new findings |
| `extraction-evidence.md` | Source files read this session |
| `FINAL-EXTRACTION-COMPLETE.md` | Sign-off marker |

## Data Ownership Note

Shipping owns no dedicated business table in the legacy system — all persistent state is per-store JSON
documents in `MERCHANT_CONFIGURATION` / `MODULE_CONFIGURATION`. The modernized service materializes these
as 4 configuration tables (config-as-tables) in `shipping_schema`. Quotes, options, summaries, and
packages are transient computed objects (response schemas), not tables.

## Callers & Dependencies

- Callers: order (MS-09), cart (MS-06).
- Reads (caller-supplied / other services): catalog/pricing (MS-04), reference data (MS-01), store (MS-03).
