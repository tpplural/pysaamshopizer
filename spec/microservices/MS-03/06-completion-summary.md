# MS-03 merchant-store — Completion Summary

**Service:** MS-03 merchant-store · **Port:** 8003 · **Schema:** `merchant_store` · **Priority:** 1 (Core) · **Wave:** 1
**Analysis mode:** Direct Source Read (no CAST) · **Status:** 🟢 Extraction complete (provisional — pending Validator + 4a sign-off)

## Counts (verified against actual file content)

| Artifact | Count |
|----------|-------|
| Business rules (`01-business-rules.md`, `^### BR-MS-`) | 19 |
| Tables (`02-domain-model.md`, CREATE TABLE) | 2 (`merchant_store`, `merchant_language`) |
| Endpoints (`03-api-design.md` / `04-api-contract.yaml`) | 11 |
| Events | 2 (`store.created`, `merchant.deleted`) |
| Source files read | 7 (all ≤500 LOC, single-pass) |

## Rule count is a DECOMPOSITION OUTCOME (not a target)

**19 rules = 7 source components decomposed along behavioral seams, reconciled against 16 Phase-1 BR-MERCH ids.**

The Phase-1 pass grouped the store half into 16 BR-MERCH rules. The deep source read re-decomposed them by behavioral seam rather than 1:1 to Phase-1 ids:

- **Merges (Phase 1 → 1 rule):** Phase-1's per-field validation observations collapse into two behavior-level rules — BR-MS-FIELD-001 (the whole mandatory-field set as one "can this store operate?" constraint) and BR-MS-FIELD-002 (location resolvability). This follows the anti-mechanical-slicing rule (merge sequential parameter checks into one business constraint).
- **Splits along seams:** BR-MERCH-006/007/008/009 (defaults) are kept as four distinct defaulting rules because each writes different columns with different provenance (unit enums vs date parse vs boolean flags vs id allocation) — genuinely distinct behavior, not padding.
- **Boundary re-scoping:** logo/landing were entangled with CMS in Phase 1 (BR-CMS-020/024). Here they are re-cut at the service boundary — BR-MS-BRAND-001 and BR-MS-LAND-001 capture ONLY the store-side rule (filename metadata, landing anchoring), delegating bytes/content to MS-11 as xref. BR-MS-BRAND-002 (template) is net-new as a store-owned rule (Phase 1 folded it into CMS rendering).
- **Group mapping:** IDENT(3) + FIELD(2) + DFLT(4) + PERS(3) + LIFE(4) + BRAND(2) + LAND(1) = 19.

The count landed by decomposition, not by fitting a band. It sits at the low end of the Core-service guide (15–30) which is correct: MS-03 is a config/anchor service with no calculation or posting engine — the honest rule surface is small.

### Net-new findings from the deep read (beyond Phase 1)

1. **Self-addressed new-store notification (defect).** Source confirms `MerchantStoreController.java:349-353` sets both the email `from` AND `to` to the store's own address — the "new store" notification loops back to the store itself rather than reaching the platform operator/new admin. Captured as an Observation on BR-MS-LIFE-001, flagged for 4a as a fix-on-migration.
2. **Edit-own-store guard gap on create.** The tenant-binding guard (`:219`) only fires when the submitted store has an id; the create path (`id==null`) bypasses it entirely. Captured on BR-MS-LIFE-004 with a note that create must also be tenant-scoped in the target. (Confirms and sharpens the Phase-1 Medium-confidence flag.)
3. **Template-write asymmetry.** `saveTemplate` reads the template from the request body but applies and persists it to the *session/context* store (`StoreBrandingController.java:143-148`), while the general store-edit forces the template back to the session value (`:318`) — the theme is deliberately un-editable on the main form. Captured as BR-MS-BRAND-002 (store-owned rule Phase 1 did not isolate).
4. **DAO fetch asymmetry.** `getById`/`getMerchantStore(String)` eager-fetch the join graph, but `getMerchantStore(Integer)` does NOT `.fetch()` (lazy) — a latent lazy-load seam. Captured in BR-MS-PERS-002 provenance; in the target the single "fully-resolved load" contract removes the asymmetry.

## Endpoint Coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /api/v1/stores | GET | COVERED | BR-MS-IDENT-003 |
| /api/v1/stores | POST | COVERED | BR-MS-IDENT-001, BR-MS-FIELD-001/002, BR-MS-DFLT-001..004, BR-MS-PERS-001, BR-MS-LIFE-001 |
| /api/v1/stores/{code} | GET | COVERED | BR-MS-PERS-002/003 |
| /api/v1/stores/{code} | PUT | COVERED | BR-MS-PERS-001, BR-MS-LIFE-004, BR-MS-BRAND-002 |
| /api/v1/stores/{code} | DELETE | COVERED | BR-MS-LIFE-002/003 |
| /api/v1/stores/code-availability | GET | COVERED | BR-MS-IDENT-002 |
| /api/v1/stores/{code}/logo | PUT | COVERED | BR-MS-BRAND-001 |
| /api/v1/stores/{code}/logo | DELETE | COVERED | BR-MS-BRAND-001 |
| /api/v1/stores/{code}/template | PUT | COVERED | BR-MS-BRAND-002 |
| /api/v1/stores/{code}/landing | PUT | COVERED | BR-MS-LAND-001 |
| /api/v1/stores/{code}/landing | GET | COVERED | BR-MS-LAND-001 |

No CRUD-only or uncovered endpoints — every endpoint is driven by at least one business rule.

## Semantic Preservation

| Source Component | Flagged Dimensions | Status | Notes |
|------------------|--------------------|--------|-------|
| MerchantStore.java | none | OK | All defaults/validation dimensions preserved (BR-MS-IDENT/FIELD/DFLT/BRAND) |
| MeasureUnit.java | none | OK (accounted) | Enum constants captured in BR-MS-DFLT-001 |
| MerchantStoreServiceImpl.java | none | OK | Cascade re-expressed as saga; 8 delete targets preserved as consumers (BR-MS-LIFE-002) |
| MerchantStoreDaoImpl.java | none | OK | Fetch-join graph preserved as single resolved-load contract (BR-MS-PERS-002) |
| MerchantStoreController.java | none | OK | New-store/superadmin/edit-own guards preserved with defect observations (BR-MS-LIFE) |
| StoreBrandingController.java | none | OK | Logo bytes → MS-11 xref; filename metadata preserved (BR-MS-BRAND-001/002) |
| StoreLandingController.java | none | OK | Content body → MS-11 xref; store-side orchestration preserved (BR-MS-LAND-001) |

All 19 rules carry a full 8-dimension Semantic Preservation table. No CRITICAL or unresolved dimensions. Preservation is not "suspiciously uniform" — every table reflects the actual (small) control/data surface of a config/anchor service, and the vectors vary by rule (e.g. BR-MS-LIFE-002 carries 8 control-flow / 8 integrations for the cascade; BR-MS-DFLT-003 carries 0 control-flow for pure defaulting).

## Implicit-System Layers

- **Entity State Model (Layer A):** `merchant_store` machine present and closed — Transient(initial) → Active → Decommissioning → Decommissioned(terminal). Every transition names a BR-ID trigger + guard.
- **Data Invariants (Layer A):** INV-MS-001..005 listed with tiers. Integrity invariants (001/002/003/005) are `db`/`both`, enforced by inline CHECK/UNIQUE constraints. INV-MS-004 (≥1 language) is `app`.
- **Database Logic Objects (Layer C):** none — all logic app-tier except the integrity CHECK/UNIQUE constraints inline in the DDL.
- **Extension Points (Layer B):** none annotated in this pass (per-store config/template variation is data-driven config, deferred to Stage 1.8 compilation).

## Cross-Service (for Stage 1.5 / graph CALLS)

- MS-03 → MS-01 reference-data (REST): country/zone/currency/language code validation on write.
- MS-03 → MS-11 content-cms (REST): logo bytes (BR-MS-BRAND-001), landing content body (BR-MS-LAND-001).
- MS-03 → (all services) via `merchant.deleted` (Event): decommission saga fan-out (BR-MS-LIFE-002).
- MS-03 → notification via `store.created` (Event): new-store notification (BR-MS-LIFE-001).

## Files Produced
INDEX.md · 00-component-inventory.md · 01-business-rules.md · 02-domain-model.md · 03-api-design.md · 04-api-contract.yaml · 06-completion-summary.md · extraction-evidence.md · FINAL-EXTRACTION-COMPLETE.md
(05-dependencies.md deferred to Stage 1.5. No test files — Phase 4c.)
