# MS-11 Content / CMS Service — Completion Summary

**Service ID**: MS-11
**Service Name**: content-cms
**Port**: 8011
**Schema**: `content_schema`
**Target Stack**: Python / FastAPI + PostgreSQL 15+
**Analysis Mode**: Direct Source Read (no CAST)
**Status**: 🟡 Phase 4 extraction complete — pending Phase 4a review

## Counts (authoritative — match across all files)

| Metric | Count |
|--------|-------|
| Business rules (BR-CMS) | 24 |
| Owned relational tables | 2 |
| Owned object stores (non-relational) | 1 |
| API endpoints | 18 |
| Data invariants (INV-CMS) | 6 |
| Domain events published | 0 |
| Extension points | 1 (EXT-CMS-001) |
| Source files read (primary, in scope) | 11 |

## Rule inventory (24)

BR-CMS-001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012, 013, 014, 015, 016, 017, 018, 019, 020,
021, 022, 023, 024. Contiguous, single group CMS, all H3 (`### BR-CMS-`).

## Decomposition outcome (anti-number-chasing)

This is NOT a target-fitted count. The combined merchant+content Phase 1 segment catalogued 40 rules — 16
BR-MERCH (extracted into MS-03) and 24 BR-CMS. Only the 24 BR-CMS rules are in scope here; the exact P1
BR-IDs were carried forward and re-grounded against the actual 2.0.1 source. The deep read confirmed P1's
CMS grouping was faithful and surfaced concrete net-new findings this spec records:

- **Net-new (data-integrity elevation):** the legacy cascade-ALL delete (BR-CMS-018) and the composite
  uniqueness constraints (BR-CMS-001/010) are elevated to **mandatory-DB integrity invariants**
  (INV-CMS-001/002/003) with FK `ON DELETE CASCADE`, rather than relying on the app being the sole writer.
- **Net-new (later-version absence confirmed):** the 2.0.1 `Content` entity has **only** `visible` — no
  `published` and no `linkToMenu` column. The absence is confirmed from source and recorded in BR-CMS-008
  and the domain model so the generator does not synthesize a publish state machine that the source lacks.
- **Net-new (BV-5 blob-ownership seam):** the object store is modeled as an owned non-relational store behind
  EXT-CMS-001, with store logos (MS-03) and product images (MS-04) as inbound byte-storage callers — a
  service-boundary clarification not visible at P1 surface level.
- **Preserved defects (D-06):** BR-CMS-016 (duplicated `uniqueResult`→`list` dead-code fallback in the
  friendly-URL lookup), BR-CMS-015 (first-row fallback masking multiplicity), BR-CMS-019 (inverted
  `addFile`/`addImage` helper naming), and BR-CMS-022 (silent empty-upload no-op) preserved exactly and
  flagged — NOT corrected.

## Content model coverage

Content type set is fixed to **Box / Page / Section** (BR-CMS-003). The landing page is a Section under the
reserved code `LANDING_PAGE` (BR-CMS-009/024). Kind is owned by the endpoint (BR-CMS-004). Position is an
optional Left/Right for boxes only (BR-CMS-006). Visibility (`visible`, BR-CMS-008) is the sole publish flag
and is applied only on storefront reads; there is NO `published` and NO `linkToMenu` in 2.0.1 (flagged for
4a). There is no workflow state machine — see the deliberate state-model absence note in 02-domain-model.md.

## File / object-store coverage (BV-5)

content-cms owns the binary bytes for static files and images (including logos and product images), stored
behind EXT-CMS-001 (pluggable file store; legacy Infinispan → object store per ADR-006/CMS). File type routes
the target store (BR-CMS-019). The store is partitioned by store code (BR-CMS-021). Uploads build typed file
objects from multipart parts (BR-CMS-022). Store logos (BR-CMS-020) are stored via inbound MS-03 calls;
product images (BR-CMS-022) via inbound MS-04 calls. Infinispan internals are OUT OF SCOPE.

## Data invariants (6)

INV-CMS-001 (code unique per store, db), INV-CMS-002 (description requires parent content, db/referential),
INV-CMS-003 (one description per language, db), INV-CMS-004 (content kind domain, both), INV-CMS-005 (box
position domain, both), INV-CMS-006 (description name non-empty, both). The three integrity invariants
(001/002/003) are mandatory-DB.

## Endpoint coverage (18)

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /pages | GET | COVERED | BR-CMS-014 |
| /pages | POST | COVERED | BR-CMS-001, 003, 004, 007, 010, 011, 012, 013, 017 |
| /pages/{contentId} | GET | COVERED | BR-CMS-005 |
| /pages/{contentId} | PUT | COVERED | BR-CMS-011, 012, 017 |
| /pages/{contentId} | DELETE | COVERED | BR-CMS-018 |
| /boxes | GET | COVERED | BR-CMS-014 |
| /boxes | POST | COVERED | BR-CMS-004, 006, 007, 010, 011, 012, 013, 017 |
| /code-available | GET | COVERED | BR-CMS-002 |
| /landing | PUT | COVERED | BR-CMS-009, 012, 024 |
| /storefront/landing | GET | COVERED | BR-CMS-023, 024 |
| /storefront/pages/{friendlyUrl} | GET | COVERED | BR-CMS-008, 016, 023 |
| /stores/{storeCode}/files | GET | COVERED | BR-CMS-021 |
| /stores/{storeCode}/files | POST | COVERED | BR-CMS-019, 021, 022 |
| /stores/{storeCode}/files/{fileName} | DELETE | COVERED | BR-CMS-019, 021 |
| /stores/{storeCode}/images | GET | COVERED | BR-CMS-021 |
| /stores/{storeCode}/images | POST | COVERED | BR-CMS-019, 021, 022 |
| /stores/{storeCode}/logo | POST | COVERED | BR-CMS-019, 020, 022 |
| /stores/{storeCode}/logo | DELETE | COVERED | BR-CMS-019, 020 |

## Items requiring human clarification (carried to Phase 4a)

- `published` / `linkToMenu`: confirmed absent in 2.0.1 (`Content` has only `visible`). Confirm these are
  later-version features and out of the modernization baseline scope.
- BR-CMS-016: the DAO runs `uniqueResult` then a redundant `query.list()` fallback on the same query — dead
  code vs. defensive? Preserved as-is (D-06).
- BR-CMS-015: language-aware `getByCode` returns `results.get(0)` when size ≥ 1 rather than asserting
  uniqueness — acceptable given the (store, code) constraint, or a latent multi-description bug?
- BR-CMS-019: `addFile()` routes to the static store and `addImage()` to the image store — the helper names
  are inverted vs the two SPI beans. Confirm the intended routing (IMAGE/STATIC_FILE → static store).
- BR-CMS-022: an empty upload list falls into a silent empty else branch (no UI feedback) — intended no-op or
  missing feedback?
- BV-5: confirm logo (MS-03) and product-image (MS-04) byte storage are inbound to content-cms and that
  content-cms is the sole byte owner.
- EXT-CMS-001: confirm the object-store target (S3-compatible / blob store) per ADR-006/CMS replaces the
  legacy Infinispan tree cache.
