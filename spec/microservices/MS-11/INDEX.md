# MS-11 Content / CMS Service — Spec Index

## Service Metadata

| Attribute | Value |
|-----------|-------|
| Service ID | MS-11 |
| Service Name | content-cms |
| Port | 8011 |
| Database Schema | `content_schema` |
| Target Stack | Python / FastAPI + PostgreSQL 15+ |
| Analysis Mode | Direct Source Read (no CAST) |
| Status | 🟡 Phase 4 extraction complete — pending Phase 4a |

## Counts (authoritative — consistent across all files)

| Metric | Count |
|--------|-------|
| Business rules (BR-CMS) | 24 |
| Owned relational tables | 2 |
| Owned object stores (non-relational) | 1 |
| API endpoints | 18 |
| Data invariants (INV-CMS) | 6 |
| Domain events published | 0 |
| Extension points | 1 |

## Purpose

MS-11 owns the CMS content subsystem — content boxes, pages, sections (including the store landing page),
their localized descriptions — AND the binary object store for static files and images. Under **BV-5** it
owns the binary BYTES; catalog (MS-04) and merchant-store (MS-03) keep blob metadata + a reference key and
delegate byte storage/retrieval here. Store logos and product images are stored VIA this service (inbound
callers). It is the FINAL service of the Shopizer 2.0.1 modernization.

## Files

| File | Content |
|------|---------|
| `00-component-inventory.md` | Legacy components, owned tables, cross-service references |
| `01-business-rules.md` | 24 BR-CMS rules (H3 headers) with 8-dim semantic preservation + examples |
| `02-domain-model.md` | DDL (2 tables), object store abstraction, 6 invariants, EXT-CMS-001 |
| `03-api-design.md` | 18 endpoints mapped to BR-IDs |
| `04-api-contract.yaml` | OpenAPI 3.1 — 18 operations |
| `06-completion-summary.md` | Counts, coverage, decomposition outcome, clarifications |
| `extraction-evidence.md` | 11 primary source files read; black-box call register |
| `FINAL-EXTRACTION-COMPLETE.md` | Sign-off marker |

## Owned tables

- `content` (legacy CONTENT)
- `content_description` (legacy CONTENT_DESCRIPTION)

Object store (bytes) is owned but non-relational — behind EXT-CMS-001.

## Content model (2.0.1 code evidence)

- Content type set is fixed: **Box / Page / Section** (`ContentType.java`). Landing page is a **Section**
  under the reserved code `LANDING_PAGE`; boxes are Box; pages are Page.
- Single visibility flag: `visible` (boolean). **NO `published` and NO `linkToMenu` column exist in 2.0.1** —
  those are later-version features, explicitly out of scope (flagged for 4a).

## File / object-store extension point (BV-5)

- `EXT-CMS-001` — pluggable content-file/object store (get/put/remove + image variants). Legacy Infinispan →
  object store target (ADR-006/CMS). content-cms owns the bytes; MS-03 logo (BR-CMS-020) and MS-04 product
  images (BR-CMS-022) are stored via this service.

## D-06 preserved-and-flagged

- BR-CMS-016 (duplicated `uniqueResult`→`list` fallback dead code), BR-CMS-015 (first-row fallback masking
  multiplicity), BR-CMS-019 (inverted `addFile`/`addImage` helper naming), BR-CMS-022 (silent empty-upload
  no-op) — preserved exactly as-is and FLAGGED for 4a.
