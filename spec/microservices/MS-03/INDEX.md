# MS-03 merchant-store — Spec Package Index

**Service ID:** MS-03 · **Name:** merchant-store · **Port:** 8003 · **Schema:** `merchant_store`
**Priority:** 1 (Core) · **Delivery Wave:** 1 · **Role:** multi-tenant anchor — every other service scopes by this store's id/code.
**Segment mapping:** Phase-1 Segment 11 (Merchant/Store & Content — store half). CMS content half → MS-11 content-cms.

## Purpose
Owns the merchant store record: identity/code, per-store configuration and defaults, supported languages, store lifecycle (create notification, decommission saga, delete/edit authorization), and branding/landing metadata. Content bytes (logo images, landing content body) are delegated to MS-11 content-cms; reference codes (country/zone/currency/language) are resolved against MS-01 reference-data as xref.

## Files
| File | Contents |
|------|----------|
| `00-component-inventory.md` | Legacy components in scope + cross-service xrefs |
| `01-business-rules.md` | 19 business rules (BR-MS-IDENT/FIELD/DFLT/PERS/LIFE/BRAND/LAND) with 8-dim preservation + examples |
| `02-domain-model.md` | PostgreSQL DDL (`merchant_store`, `merchant_language`), state model, invariants |
| `03-api-design.md` | 11 endpoints + 2 events |
| `04-api-contract.yaml` | OpenAPI 3.1 contract (naming authority) |
| `06-completion-summary.md` | Counts, decomposition rationale, net-new findings, coverage, preservation |
| `extraction-evidence.md` | Source files read (proof of work) |
| `FINAL-EXTRACTION-COMPLETE.md` | Extraction sign-off marker |

## Key Cross-References
- Phase-1 ids: `BR-MERCH-001..016` → re-decomposed into `BR-MS-*` (19 rules)
- Dependencies (Stage 1.5): MS-01 reference-data (REST), MS-11 content-cms (REST), all services via `merchant.deleted` (Event), notification via `store.created` (Event)

## Status
🟢 Extraction complete (provisional — pending Validator gate + Phase 4a sign-off). 05-dependencies.md deferred to Stage 1.5.
