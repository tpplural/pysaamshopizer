# MS-07 (tax) — Completion Summary

**Service ID**: MS-07
**Status**: 🟢 100% COMPLETE
**Analysis mode**: Direct Source Read (no CAST)

## Verified Counts (match INDEX.md and FINAL-EXTRACTION-COMPLETE.md)

| Metric | Count | Source of truth |
|--------|-------|-----------------|
| Business rules | 28 | `grep -c '^### BR-TAX-' 01-business-rules.md` |
| Semantic Preservation tables | 28 | one per rule |
| Owned tables | 4 | `02-domain-model.md` (tax_class, tax_rate, tax_rate_description, tax_configuration) |
| Data invariants | 12 | INV-TAX-001 … INV-TAX-012 in `02-domain-model.md` |
| API endpoints | 13 | `03-api-design.md` / operations in `04-api-contract.yaml` |
| D-06 preserved-and-flagged rules | 4 | BR-TAX-003, 007, 019, 023 |

## Rule Count as a Decomposition Outcome (NOT a target)

28 rules = 15 source components deeply read, decomposed along behavioral seams:
- The `calculateTax` engine (one method) was decomposed along its distinct behavioral seams — config
  resolution, basis selection, collection gates, per-class grouping, shipping bucketing, rate lookup
  (zone vs state), percentage application, compound stacking, rounding, consolidation, empty semantics —
  yielding ~19 rules from ONE method (a genuine split by seam, not a 1:1 proc→rule slice).
- The two admin controllers contributed the tax-class and tax-rate CRUD/validation rules (BR-TAX-025..028).
- The config POJO contributed the persistence/defaulting rules (BR-TAX-001/002/003/010).

**Net-new findings from the deep read (beyond P1 grouping):**
- **BR-TAX-023 (net-new preservation flag):** the duplicate-code consolidation computes a summed amount
  but never stores it back into the map — a discarded-computation defect of the SAME class as the named
  D-06 items. The deep read promoted this from a P1 medium note to a first-class FLAGGED rule.
- **Wire-format/semantic detail:** the null-vs-empty-list distinction of the calculation result
  (BR-TAX-024) is a precise outcome contract the caller (MS-09) must honor — surfaced explicitly.
- Confirmed (not new) but load-bearing: the always-false basis comparison (BR-TAX-007) and the
  unused tax-class query argument (BR-TAX-019) were verified directly in source this session.

No count was fitted to a band; the number fell out of the seam decomposition above.

## Endpoint Coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /api/v1/tax/calculate | POST | COVERED | BR-TAX-002,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,019,020,021,022,023,024 |
| /api/v1/tax/configuration | GET | COVERED | BR-TAX-001,002 |
| /api/v1/tax/configuration | PUT | COVERED | BR-TAX-001,003 |
| /api/v1/tax/tax-classes | GET | COVERED | BR-TAX-025 |
| /api/v1/tax/tax-classes | POST | COVERED | BR-TAX-025 |
| /api/v1/tax/tax-classes/{id} | GET | CRUD-ONLY | — (read + ownership guard) |
| /api/v1/tax/tax-classes/{id} | PUT | COVERED | BR-TAX-025 |
| /api/v1/tax/tax-classes/{id} | DELETE | COVERED | BR-TAX-026 |
| /api/v1/tax/tax-rates | GET | COVERED | BR-TAX-028 |
| /api/v1/tax/tax-rates | POST | COVERED | BR-TAX-027 |
| /api/v1/tax/tax-rates/{id} | GET | COVERED | BR-TAX-028 |
| /api/v1/tax/tax-rates/{id} | PUT | COVERED | BR-TAX-027 |
| /api/v1/tax/tax-rates/{id} | DELETE | CRUD-ONLY | — (id guard then delete) |

- 13 endpoints; 11 COVERED, 2 CRUD-ONLY.

## calculateTax Engine Coverage

The engine is fully decomposed with the algorithm preserved exactly:
- Config resolution + default basis (BR-TAX-001/002); basis-address selection (BR-TAX-004/005/006) and
  the always-false comparison that renders them dead (BR-TAX-007, D-06);
- collection-scope gates (BR-TAX-008/009/010); per-tax-class subtotal grouping (BR-TAX-011/012/013);
- shipping+handling always into the DEFAULT bucket (BR-TAX-014/015);
- rate lookup zone-vs-state paths + priority ordering + the unused class argument (BR-TAX-016/017/018/019, D-06);
- percentage application, compound (piggyback) stacking, per-line HALF_UP 2dp rounding (BR-TAX-020/021/022);
- consolidation by code with dedup-to-first (BR-TAX-023, D-06); null-vs-empty result semantics (BR-TAX-024).

## Semantic Preservation

| Source Component | Flagged Dimensions | Status | Notes |
|------------------|--------------------|--------|-------|
| TaxServiceImpl (calculateTax) | none | OK | all 8 dimensions preserved; algorithm written out explicitly |
| TaxConfiguration (POJO) | none (behavior preserved) | FLAGGED (D-06) | collection flags not serialized — preserved as-is (BR-TAX-003) |
| TaxBasisCalculation (enum) | none | FLAGGED (D-06) | always-false comparison preserved (BR-TAX-007) |
| TaxRateDaoImpl | none | FLAGGED (D-06) | unused taxClass arg preserved (BR-TAX-019) |
| TaxClassController | none | OK | class CRUD + guards |
| TaxRatesController | none | OK | rate CRUD + validation |
| TaxConfigurationController | none | OK | config edit/save |

Per-component source vectors are recorded in `extraction-evidence.md`.

## Zero-Loss / Black-Box Call Register

| Called Unit | Called By (BR-ID) | Disposition | Rationale / New BR-IDs |
|-------------|-------------------|-------------|------------------------|
| taxRateService.listByCountryZoneAndTaxClass | BR-TAX-016 | EXTRACTED | BR-TAX-017,019 (DAO) |
| taxRateService.listByCountryStateProvinceAndTaxClass | BR-TAX-016 | EXTRACTED | BR-TAX-018,019 (DAO) |
| taxClassService.getByCode | BR-TAX-012 | EXTRACTED | BR-TAX-012/025 (DAO/controller) |
| merchantConfigurationService.getMerchantConfiguration | BR-TAX-001 | OUT_OF_SCOPE | external system config store (MS-03/shared); MS-07 reads/writes its own TAX_CONFIG document only |
| productService.listByTaxClass | BR-TAX-026 | OUT_OF_SCOPE | catalog read (MS-04) — cross-service dependency, not owned |

No unresolved black-box callees. Register mechanism: spec-Logic grep (Direct Source mode; no CAST call-graph). Reported as "no evidence of black-box sub-calls" — the within-service callees are all extracted.

## Human Clarification Items (carried to Phase 4a)
- BR-TAX-007 (D-06): preserve always-billing-address behavior, or honor configured basis? (high business impact)
- BR-TAX-019 (D-06): rates apply globally vs should be scoped to product tax class?
- BR-TAX-003 (D-06): persist the two collection flags in the modernized config?
- BR-TAX-023 (D-06): preserve dedup-to-first vs sum duplicate-code lines?
- BR-TAX-014: restore a configurable "tax on shipping" flag, or keep unconditional shipping tax under DEFAULT?
- DEFAULT tax class existence is a runtime precondition (getByCode("DEFAULT")); confirm store-agnostic vs store-scoped lookup.
