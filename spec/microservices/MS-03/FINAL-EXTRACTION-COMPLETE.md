# MS-03 merchant-store — FINAL EXTRACTION COMPLETE

**Extractor (Phase 4 Subagent B) sign-off.**

- **Service:** MS-03 merchant-store · **Mode:** Direct Source Read (no CAST)
- **Source files read:** 7 / 7 (all ≤500 LOC, single-pass) — 0 not found
- **Rules extracted:** 19 (`BR-MS-*`), reconciled against Phase-1 `BR-MERCH-001..016`
- **Tables:** 2 (`merchant_store`, `merchant_language`)
- **Endpoints:** 11 · **Events:** 2 (`store.created`, `merchant.deleted`)

## Quality self-checks (pre-Validator)
- [x] Every Statement is a semantic business sentence — no legacy table/column/@var names, no SQL (legacy names confined to Logic/Source Reference/DDL comments).
- [x] Every one of the 19 rules has an 8-dimension Semantic Preservation table with honest Source vs Spec counts.
- [x] Every rule has a Concrete Example (≥1 success + ≥1 error, domain fields, realistic values).
- [x] `02-domain-model.md` is executable PostgreSQL; every table has a PK; reference codes are xref (not FK).
- [x] `04-api-contract.yaml` is OpenAPI 3.1; every `03-api-design.md` endpoint has a contract path; responses ref `components/schemas`.
- [x] Source References use `ClassName.java:method:lines` form.
- [x] Completion summary framed as a decomposition outcome with 4 net-new findings + endpoint coverage + preservation tables.
- [x] Scope boundary honored: logo bytes, landing content body, and cascade targets modeled as xref to MS-11/others; only the store-side rule captured.

## Known observations forwarded to Phase 4a
1. Self-addressed new-store notification (from==to store email) — BR-MS-LIFE-001, likely defect.
2. Edit-own-store guard bypassed on create (id==null) — BR-MS-LIFE-004, guard gap.
3. Template deliberately un-editable via the main store form — BR-MS-BRAND-002 (behavior, not defect).
4. DAO fetch asymmetry (integer-lookup is lazy) — resolved by the single resolved-load contract (BR-MS-PERS-002).

Ready for Validator (Subagent C).
