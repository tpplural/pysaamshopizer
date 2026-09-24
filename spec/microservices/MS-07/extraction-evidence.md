# MS-07 (tax) — Extraction Evidence

**Phase 4 Deep Extraction — Direct Source mode (no CAST).** Legacy: Shopizer 2.0.1 (Java / Spring MVC, JPA/Hibernate, QueryDSL/Mysema). Every rule below was produced by reading the actual `.java` source in THIS session (not repackaged from Phase 1). Source roots exclude `/target/`. Entity `.java` sources live under `sm-core` (the `sm-core-model` tree only holds compiled `.class` + QueryDSL `Q*` metamodels).

## Source Files Processed

| # | File | Lines (approx) | Sections Read | Rules Extracted | Vectors Counted |
|---|------|-------|---------------|-----------------|-----------------|
| 1 | `sm-core/.../tax/service/TaxServiceImpl.java` | 300 | full: getTaxConfiguration (61-77), saveTaxConfiguration (81-94), calculateTax (99-297: guards, basis selection, collection gates, per-class grouping, shipping bucket, rate lookup, piggyback stacking, rounding, consolidation) | BR-TAX-001,002,004,005,006,007,008,009,011,012,013,014,015,016,020,021,022,023,024 | ✅ |
| 2 | `sm-core/.../tax/service/TaxService.java` (iface) | 48 | full: 3 method contracts | (contract only) | ✅ |
| 3 | `sm-core/.../tax/model/TaxConfiguration.java` (POJO/JSON) | 55 | full: field defaults (13-16), toJSONString (20-27) | BR-TAX-002,003,010 | ✅ |
| 4 | `sm-core/.../tax/model/TaxBasisCalculation.java` (enum) | 8 | full: STOREADDRESS/SHIPPINGADDRESS/BILLINGADDRESS | BR-TAX-007 (evidence) | ✅ |
| 5 | `sm-core/.../tax/model/TaxItem.java` (transient) | 32 | full: label, taxRate, extends OrderTotalItem | BR-TAX-020,023 (evidence) | ✅ |
| 6 | `sm-core/.../tax/model/taxrate/TaxRate.java` (entity) | 260 | full: JPA mapping, unique(TAX_CODE,MERCHANT_ID), taxRate precision 7 scale 4, taxPriority default 0, piggyback, parent self-ref, descriptions cascade ALL, audit | BR-TAX-027, INV rows | ✅ |
| 7 | `sm-core/.../tax/model/taxrate/TaxRateDescription.java` (entity) | 55 | full: unique(TAX_RATE_ID,LANGUAGE_ID), extends Description | INV rows | ✅ |
| 8 | `sm-core/.../tax/model/taxclass/TaxClass.java` (entity) | 130 | full: unique(MERCHANT_ID,TAX_CLASS_CODE), code len≤10, title len≤32, DEFAULT constant | BR-TAX-025, INV rows | ✅ |
| 9 | `sm-core/.../tax/dao/taxrate/TaxRateDaoImpl.java` | 190 | full: listByStore ×2, getByCode, getById, listByCountryZoneAndTaxClass (126-152), listByCountryStateProvinceAndTaxClass (156-181) | BR-TAX-016,017,018,019 | ✅ |
| 10 | `sm-core/.../tax/dao/taxclass/TaxClassDaoImpl.java` | 85 | full: listByStore, getByCode (store-agnostic), getByCode(store), getById | BR-TAX-012 (evidence), BR-TAX-025 | ✅ |
| 11 | `sm-core/.../tax/service/TaxRateServiceImpl.java` | 75 | full: delegating; delete re-loads by id | BR-TAX-016 (delegation) | ✅ |
| 12 | `sm-core/.../tax/service/TaxClassServiceImpl.java` | 60 | full: delegating; delete re-loads by id; getByCode ×2 | BR-TAX-012,026 (delegation) | ✅ |
| 13 | `sm-shop/.../admin/controller/tax/TaxClassController.java` | 300 | full: list, paging (hide DEFAULT), save (reject DEFAULT + dup), update (reject DEFAULT + dup diff id), remove (product-assoc guard), edit (store guard) | BR-TAX-025,026, and list/hide/edit rules | ✅ |
| 14 | `sm-shop/.../admin/controller/tax/TaxRatesController.java` | 430 | full: list, page (3dp format), save/update (validateTaxRate), remove, edit (store guard); validateTaxRate (rateText required+parseable, unique code, priority default, resolve zone/country, !piggyback→parent null) | BR-TAX-027,028 | ✅ |
| 15 | `sm-shop/.../admin/controller/tax/TaxConfigurationController.java` | 95 | full: displayTaxConfiguration (edit, null→default), saveTaxConfiguration (save) | BR-TAX-001,003 (write side) | ✅ |
| 16 | `sm-core/.../tax/model/taxrate/QTaxRate.java` / `QTaxClass.java` | (metamodel) | referenced (QueryDSL predicates in DAOs) | — | N/A (generated) |

## Extraction Status
- Files total (in-scope `.java`): 15 (+ generated QueryDSL metamodels referenced but not rule sources)
- Files processed: 15
- Rules extracted: 28 (BR-TAX-001 … BR-TAX-028)
- Source vectors complete: yes (per-component, 8-dimension, in `06-completion-summary.md`)

## Not-Found / Resolution Notes
- Segment brief referenced `sm-core-model/.../tax/model/**`; per the Source File Resolution rule the real `.java` sources were located under `sm-core/.../tax/model/**` (fuzzy search + `find`). All six model types were found and read there. `sm-core-model` holds only compiled `.class` + `Q*` metamodel.
- `TaxConfiguration` and `TaxItem` are plain POJOs (NOT JPA entities): `TaxConfiguration` is persisted as a JSON blob inside `MERCHANT_CONFIGURATION` (key `TAX_CONFIG`); `TaxItem` is a transient computed order-total line.

## Session Log
| Session | Files Processed | Rules Added | Notes |
|---------|-----------------|-------------|-------|
| 1 | files 1-16 | 28 rules | Single-session deep read; calculateTax engine written out explicitly; D-06 preservation items (BR-TAX-007/019/003) flagged, not corrected |
