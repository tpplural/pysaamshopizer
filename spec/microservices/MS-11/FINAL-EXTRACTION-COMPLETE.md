# MS-11 Content / CMS Service — FINAL EXTRACTION COMPLETE

**Service ID**: MS-11
**Status**: 🟢 Phase 4 extraction complete (pending Phase 4a human review)
**Analysis Mode**: Direct Source Read (no CAST)
**Note**: FINAL service of the Shopizer 2.0.1 modernization.

## Deliverables present (9 files)

- [x] INDEX.md
- [x] 00-component-inventory.md
- [x] 01-business-rules.md (24 rules, all H3 `### BR-CMS-`)
- [x] 02-domain-model.md (2 tables, object store abstraction, 6 invariants, EXT-CMS-001)
- [x] 03-api-design.md (18 endpoints)
- [x] 04-api-contract.yaml (OpenAPI 3.1, 18 operations)
- [x] 06-completion-summary.md
- [x] extraction-evidence.md
- [x] FINAL-EXTRACTION-COMPLETE.md

## Final counts (consistent across files)

| Metric | Count |
|--------|-------|
| Business rules | 24 |
| Owned relational tables | 2 |
| Owned object stores (non-relational) | 1 |
| API endpoints | 18 |
| Data invariants | 6 |
| Domain events | 0 |
| Extension points | 1 |

## Key confirmations

- All 24 rule headers are H3 (`### `), not H2. Contiguous BR-CMS-001..024, single group CMS.
- Only BR-CMS rules were extracted — NO BR-MERCH rules (those belong to MS-03 merchant-store).
- Content model = **Box / Page / Section** only; landing page is a Section under code `LANDING_PAGE`; the
  sole publish flag is `visible`. There is **NO `published` and NO `linkToMenu`** column in 2.0.1 — confirmed
  absent from source and flagged for 4a.
- The binary store is modeled as an **owned object store behind an extension point (EXT-CMS-001)** —
  pluggable file store, legacy Infinispan → object store target (ADR-006/CMS). It is NOT Infinispan-specific
  and NOT a relational table (owned relational table count remains 2).
- BV-5: content-cms owns the bytes; store logos (BR-CMS-020, inbound from MS-03) and product images
  (BR-CMS-022, inbound from MS-04) are stored via this service.
- D-06 preserved-and-flagged: BR-CMS-016 (dead-code fallback), BR-CMS-015 (first-row fallback),
  BR-CMS-019 (inverted helper naming), BR-CMS-022 (silent empty-upload) — preserved as-is, NOT corrected.

Not performed (per instructions): graph import, git commit.
