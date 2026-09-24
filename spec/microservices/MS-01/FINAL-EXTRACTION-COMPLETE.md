# MS-01 reference-data — FINAL EXTRACTION COMPLETE

**Service:** MS-01 reference-data · **Port:** 8001 · **Schema:** `reference_data`
**Phase:** 4 (Specification Generation) — Extractor (Subagent B)
**Mode:** Direct Source Read (no CAST) · **Status:** 🟢 Extraction complete — awaiting Validator + human sign-off

## Deliverables produced
- [x] `INDEX.md`
- [x] `00-component-inventory.md`
- [x] `01-business-rules.md` — 26 implementable BR-IDs + 1 negative finding, all with 8-dim preservation tables
- [x] `02-domain-model.md` — 8 tables of executable PostgreSQL DDL + entity state model + 7 invariants
- [x] `03-api-design.md` — 14 endpoints, full coverage table
- [x] `04-api-contract.yaml` — OpenAPI 3.1, validated (14 paths, 14 ops, 0 dangling refs, 0 dup operationIds)
- [x] `06-completion-summary.md` — decomposition-outcome counts, coverage, preservation, 6 net-new findings
- [x] `extraction-evidence.md` — 20 source files read (full), 2 dead-code confirmed, 0 not found
- [ ] `05-dependencies.md` — NOT produced (Stage 1.5; reference-data is a leaf provider, calls no one)
- [ ] test files — NOT produced (Phase 4c)

## Quality gate self-check
- [x] Statement compliance: every Statement is a business sentence; legacy names only in Logic
- [x] Semantic preservation: 8-dimension table on every BR-ID; honest counts
- [x] Concrete example (success + error) on every implementable rule
- [x] DDL is executable PostgreSQL; every table has a PK
- [x] OpenAPI 3.1 valid; every 03-api-design endpoint has a contract path; responses ref components/schemas
- [x] BR-ID numbering per steering (BR-REF-<GROUP>-<NNN>); Phase 1 BR-REF-* cited as Cross-Reference
- [x] extraction-evidence lists every file read
- [x] completion summary states count as a decomposition outcome + cites net-new findings

## Human review pointers (Phase 4a)
1. Geo-zone disposition (BR-REF-SEED-GEO) — dead / future / used-elsewhere.
2. Cross-domain seed relocation (SEED-006/007) — confirm merchant/tax/catalog/system-config own their defaults.
3. Net-new defects NF-1..NF-3 — confirm fix-on-migration (not preserve-the-bug).
4. NF-2 currency name, NF-4 language sort order, NF-5 pinned country catalog, INV-REF-002 language unique — confirm target behavior.
