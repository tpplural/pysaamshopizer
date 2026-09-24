# MS-01 reference-data — Specification Package Index

**Service ID:** MS-01
**Service Name:** reference-data
**Port:** 8001
**DB Schema:** `reference_data`
**Priority:** 1 (Core) · **Delivery Wave:** 0
**Analysis Mode:** Direct Source (no CAST)
**Legacy System:** Shopizer 2.0.1 (Java / Spring MVC, JPA/Hibernate, QueryDSL/Mysema, EhCache)
**Status:** 🟢 Extraction complete — pending Validator + human sign-off

## Purpose (one line)
Authoritative, read-mostly reference/geo data — countries, zones (states/provinces), currencies,
languages, geo-zones — plus ISO/code resolution for every other service and a seed-once bootstrap.

## Package Contents

| File | Purpose |
|------|---------|
| `INDEX.md` | This file |
| `00-component-inventory.md` | Legacy components read, classification, disposition |
| `01-business-rules.md` | 26 business rules (BR-REF-*) with semantic statements, preservation tables, examples |
| `02-domain-model.md` | Executable PostgreSQL DDL + entity state model + data invariants |
| `03-api-design.md` | REST endpoints (method, path, purpose, coverage) |
| `04-api-contract.yaml` | OpenAPI 3.1 contract (naming authority for tests + code gen) |
| `06-completion-summary.md` | Decomposition-outcome counts, coverage table, preservation summary, net-new findings |
| `extraction-evidence.md` | Every source file read (path, LOC, sections, rules extracted) |
| `FINAL-EXTRACTION-COMPLETE.md` | Sign-off checklist |

## NOT in this package (generated later)
- `05-dependencies.md` — Stage 1.5 (reference-data is a leaf provider; calls no one)
- `07-workflows.md` — Stage 1.6
- `08-dtos/` — Phase 4c Stage 0 (after tech stack confirmed)
- test suites — Phase 4c

## Traceability
Phase 1 segment: **Segment 13 (Reference data)** · Phase 1 rules: `BR-REF-001..027` (27).
Phase 4 deep re-extraction yields **26 target rules** (`BR-REF-RES-*`, `BR-REF-LST-*`, `BR-REF-CAC-*`,
`BR-REF-LNG-*`, `BR-REF-API-*`, `BR-REF-SEED-*`) + 1 negative finding. Each cites its Phase 1 origin as Cross-Reference.
The count is a decomposition/merge outcome — see `06-completion-summary.md`, not a target.
