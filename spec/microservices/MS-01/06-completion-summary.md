# reference-data (MS-01) — Completion Summary

**Status:** 🟢 Extraction complete — pending Validator + human sign-off
**Analysis mode:** Direct Source Read (no CAST)

## Counts (verified against file content)

| Artifact | Count |
|----------|-------|
| Business rules (implementable BR-IDs) | 26 |
| Negative findings (documented, no endpoint) | 1 (BR-REF-SEED-GEO) |
| Total `### BR-REF` headings in 01-business-rules.md | 27 (26 rules + 1 finding) |
| Preservation tables (one per rule) | 26 |
| Tables (DDL) | 8 |
| API endpoints | 14 |
| Source files read (business logic) | 20 (+2 dead-code confirmed, +6 supporting) |

Rule IDs (26): RES-001..004 (4), LST-001..006 (6), CAC-001..002 (2), LNG-001..003 (3),
API-001..003 (3), SEED-001, SEED-002, SEED-003, SEED-004a, SEED-004, SEED-005, SEED-006, SEED-007 (8).
Total implementable = 4+6+2+3+3+8 = **26 BR-IDs**. Of these, SEED-006/SEED-007 are boundary-relocation
records (behavior owned by other services), API-002 covers two endpoints, and CAC-001/002 each span
three services. See Decomposition Rationale.

## Decomposition Rationale (count is an OUTCOME, not a target)

Phase 1 extracted **27 rules (BR-REF-001..027)** at the grouping level. Phase 4 deep re-extraction
produced **26 target BR-IDs**. This is a **net near-parity with restructuring**, driven by behavior,
not a target band:

- **26 target rules = ~15 source procedures/methods decomposed along behavioral seams + merges − relocations + 1 net-new.**
- **Merges (fewer rules than P1):**
  - P1 BR-REF-005 + BR-REF-006 (list query + first-description naming) → one behavior BR-REF-LST-001
    (the naming is inseparable from the localized list — they are one business behavior).
  - P1 BR-REF-008 + BR-REF-010 (app cache + JPA `@Cacheable`) → one caching rule BR-REF-CAC-001
    (both are "reference lists are cached"; the L2 annotation is a sub-detail, not its own business rule).
  - The four per-service swallow-catches → one fail-soft rule BR-REF-CAC-002 (one contract, four sites).
- **Relocations (recorded, not owned):** P1 BR-REF-026 + BR-REF-027 → BR-REF-SEED-006/007, kept as
  explicit MOVED-OUT records so the cross-domain seed behavior is traceable but attributed to
  merchant-store / tax / catalog / system-config (boundary decision R-05). Not dropped, not owned.
- **Splits (more granular than P1):** P1 BR-REF-022 (createCountries) is kept as BR-REF-SEED-004a but
  the currency/zone/language seed steps stay distinct (SEED-003/004/005) because each has a distinct
  skip/dedup behavior worth its own rule + test.
- **New rule from deep read:** BR-REF-API-003 (credit-card-years / months-of-year generation) — P1
  listed these endpoints in its UI inventory but extracted NO rule for them; the deep read of
  `ReferenceController` lines 173-250 turned them into an implementable calculation rule.

### Net-new findings from the deep read (P1 did not have these)
- **NF-1 (defect):** `Currency.getCode()` compares strings with `!=` (reference identity) instead of
  `.equals` (`Currency.java:73-77`). It masks a code/currencyCode mismatch and returns the
  platform-derived code. Not carried into the target model (plain columns).
- **NF-2 (defect, confirms P1 flag with mechanism):** `createCurrencies` sets `name = c.getCurrencyCode()`
  BEFORE `setCurrency` (`InitializationDatabaseImpl.java:106-108`), so `CURRENCY_NAME` persists the code,
  never the human name. Target `currency.name` is NOT NULL and intended for the real name.
- **NF-3 (defect):** `Zone(country,name,code)` constructor calls `setCode(code)` then `setCode(name)`,
  overwriting the code with the name (`Zone.java:49-53`). The constructor is unused (loader uses
  no-arg + setters), so inert — but a real bug. Not reproduced in the target.
- **NF-4:** `Language.sortOrder` exists but is never used for ordering anywhere (`LanguageServiceImpl`
  applies no order-by to the language list). Target should order languages by `sort_order`.
- **NF-5:** the seeded **country set is platform-dependent** — `createCountries` skips any ISO code with
  no JVM locale (`InitializationDatabaseImpl.java:135-137`). The target must pin the catalog explicitly
  for determinism.
- **NF-6 (confirms P1):** `Zone` is NOT `@Cacheable` while Country/Language/Currency are — asymmetry
  confirmed by direct read of all four entities.

## Endpoint Coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /countries | GET | COVERED | BR-REF-LST-001, LST-004, LST-005 |
| /countries/{isoCode} | GET | COVERED | BR-REF-RES-001 |
| /countries/{isoCode}/name | GET | COVERED | BR-REF-API-002 |
| /countries/{isoCode}/zones | GET | COVERED | BR-REF-LST-002 |
| /zones/{code} | GET | COVERED | BR-REF-RES-004 |
| /zones/{code}/name | GET | COVERED | BR-REF-API-002 |
| /provinces | POST | COVERED | BR-REF-API-001, LNG-003 |
| /currencies | GET | COVERED | BR-REF-LST-006 |
| /currencies/{code} | GET | COVERED | BR-REF-RES-003 |
| /languages | GET | COVERED | BR-REF-LST-003 |
| /languages/{code} | GET | COVERED | BR-REF-RES-002 |
| /languages/resolve | GET | COVERED | BR-REF-LNG-001, LNG-002 |
| /credit-card-years | GET | COVERED | BR-REF-API-003 |
| /months-of-year | GET | COVERED | BR-REF-API-003 |

14/14 endpoints COVERED. No CRUD-only, no uncovered endpoints.

## Semantic Preservation Summary

| Source Component | Flagged Dimensions | Status | Notes |
|------------------|--------------------|--------|-------|
| CountryServiceImpl / CountryDaoImpl | none | OK | list+naming+map+subset all preserved |
| CurrencyServiceImpl / CurrencyDaoImpl | none | OK | getByCode + code-sorted list |
| LanguageServiceImpl | none | OK | getByCode, list, toLocale/toLanguage, default fallback |
| ZoneServiceImpl / ZoneDaoImpl | none | OK | getByCode, by-country + by-language lists, cache |
| ReferenceController | none | OK | provinces, name echo, card-year/month generation |
| InitializationDatabaseImpl | none (owned) | OK | guard, atomic order, lang/country/zone/currency seed; cross-domain steps relocated (SEED-006/007) with intentional control/write deltas annotated |
| ZonesLoader | none | OK | dedup + null-country skip preserved |

Every BR-ID carries its 8-dimension preservation table. Owned rules show Source≈Spec (faithful).
The two relocation rules (SEED-006/007) intentionally show control-flow/state/write deltas because that
behavior is owned by another service — annotated OK (boundary relocation), each moved write attributed
to a named target service (no silent loss).

## Layer A / B / C status
- **Layer A (state model):** DB bootstrap Empty→Seeded (closed machine). Reference entities are static
  lookups (no per-row lifecycle). 7 data invariants (INV-REF-001..007); integrity ones are db-tier.
- **Layer B (extensibility):** zone catalog + module catalog are data-driven (config resources); seed
  ISO/currency/language universe is a constant list. Recorded in the domain notes; extensibility model
  compiled in Stage 1.8.
- **Layer C (DB logic objects):** NONE — all app-tier; integrity invariants are DDL constraints.

## Open items for human (Phase 4a)
- BR-REF-SEED-GEO: geo-zone disposition (dead / future / used-elsewhere).
- NF-2 currency name: confirm the target should persist the real currency name (correcting the legacy defect).
- NF-4 language sort_order: confirm languages should order by sort_order.
- NF-5 country catalog: confirm the pinned, deterministic country set for the target seed.
- INV-REF-002: confirm adding a DB unique constraint on language code (legacy had none).
