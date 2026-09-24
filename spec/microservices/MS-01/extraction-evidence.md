# reference-data (MS-01) — Extraction Evidence

**Analysis mode:** Direct Source Read. All files read in full (all ≤ 269 LOC → single-pass tier).
Root: `initial-source/shopizer/`.

## Source Files Processed

| # | File | LOC | Sections read | Rules extracted |
|---|------|-----|---------------|-----------------|
| 1 | sm-core-model/.../reference/country/model/Country.java | 130 | full: id/table-gen, descriptions/zones/geoZone relations, supported+isoCode cols, transient name, ctors | domain model + BR-REF-RES-001 |
| 2 | sm-core-model/.../reference/country/model/CountryDescription.java | 43 | full: unique(COUNTRY_ID,LANGUAGE_ID), ctor(lang,name) | domain model (country_description) |
| 3 | sm-core-model/.../reference/currency/model/Currency.java | 90 | full: cols, setCurrency derives code, **getCode() `!=` defect (NF-1)** | BR-REF-RES-003 + NF-1 |
| 4 | sm-core-model/.../reference/language/model/Language.java | 114 | full: CODE not-null no-unique, sortOrder, audit, equals-on-id | BR-REF-RES-002 + INV-REF-002 + NF-4 |
| 5 | sm-core-model/.../reference/zone/model/Zone.java | 102 | full: ZONE_CODE unique, COUNTRY_ID not-null, transient name, **3-arg ctor code/name overwrite (NF-3)** | BR-REF-RES-004 + NF-3 |
| 6 | sm-core-model/.../reference/zone/model/ZoneDescription.java | 43 | full: unique(ZONE_ID,LANGUAGE_ID), ctor(zone,lang,name) | domain model (zone_description) |
| 7 | sm-core-model/.../reference/geozone/model/GeoZone.java | 92 | full: `// TODO create DAO/Service`, countries OneToMany, descriptions | BR-REF-SEED-GEO (inert) |
| 8 | sm-core-model/.../reference/geozone/model/GeoZoneDescription.java | 36 | full: unique(GEOZONE_ID,LANGUAGE_ID) | domain model (geozone_description) |
| 9 | sm-core/.../reference/country/service/CountryServiceImpl.java | 125 | full: getByCode, addCountryDescription(update), getCountriesMap, getCountries(subset), getCountries(lang) cache-miss + name .get(0) + swallow-catch | RES-001, LST-001, LST-004, LST-005, CAC-001, CAC-002 |
| 10 | sm-core/.../reference/country/dao/CountryDaoImpl.java | 36 | full: listByLanguage join-fetch + order-by name | LST-001 |
| 11 | sm-core/.../reference/currency/service/CurrencyServiceImpl.java | 25 | full: getByCode (no cache) | RES-003 |
| 12 | sm-core/.../reference/currency/dao/CurrencyDaoImpl.java | 35 | full: list() order-by code | LST-006 |
| 13 | sm-core/.../reference/language/service/LanguageServiceImpl.java | 108 | full: getByCode, toLocale, toLanguage(null-on-miss), getLanguagesMap, getLanguages cache | RES-002, LST-003, LNG-001, LNG-002, CAC-001, CAC-002 |
| 14 | sm-core/.../reference/language/dao/LanguageDaoImpl.java | 10 | full: empty (inherits generic) | — (ACCOUNTED) |
| 15 | sm-core/.../reference/zone/service/ZoneServiceImpl.java | 132 | full: getByCode, addDescription branch, getZones(country,lang) cache-miss+name, getZones(lang) map | RES-004, LST-002, CAC-001, CAC-002 |
| 16 | sm-core/.../reference/zone/dao/ZoneDaoImpl.java | 54 | full: listByLanguageAndCountry, listByLanguage (join-fetch + order) | LST-002 |
| 17 | sm-core/.../reference/init/service/InitializationDatabaseImpl.java | 269 | full: isEmpty, @Transactional populate order, createCurrencies (skip IllegalArg, **name=code NF-2**), createCountries (locale-skip NF-5, chatty update), createZones, createLanguages, createMerchant (CA/CAD/en/QC), createModules, createSubReferences | SEED-001..007 + NF-2 + NF-5 |
| 18 | sm-core/.../utils/reference/ZonesLoader.java | 142 | full: loadZones — lang×zone loops, null-country skip, per-(lang,zone) dedup, description accumulation | SEED-004 |
| 19 | sm-shop/.../web/reference/ReferenceController.java | 257 | full: getProvinces (lang precedence + fail-soft), countryName/zoneName echo, getCreditCardDates (10 yrs), getMonthsOfYear (01..12) | API-001, API-002, LNG-003, API-003 |
| 20 | Interfaces: CountryService, CurrencyService, LanguageService, ZoneService, ZoneDao, InitializationDatabase | ~90 (combined) | signatures only | — (contracts) |

## Dead code confirmed (SKIP)
| File | LOC | Evidence |
|------|-----|----------|
| sm-core/.../reference/zone/imports/ZoneLoader.java | 31 | No caller; seed uses `utils/reference/ZonesLoader` (different class). Confirmed via directory listing + import graph in InitializationDatabaseImpl. |
| sm-core/.../reference/zone/imports/ZoneTransient.java | 28 | Only referenced by the dead ZoneLoader. |

## Supporting files (read for evidence, not owned)
`SchemaConstant` (COUNTRY_ISO_CODE / CURRENCY_MAP / LANGUAGE_ISO_CODE / LOCALES — seed constants),
`InitializationLoader` (@PostConstruct trigger, sm-shop), `SalesManagerEntityServiceImpl` /
`SalesManagerEntityDaoImpl` (generic getByField/count/list/create), `CacheUtils` (EhCache wrapper),
`IntegrationModulesLoader` (cross-domain module loader). Not this segment's owned logic.

## Files NOT found / not accessible
None. Every source file listed in the extraction brief was located and read in full.

## Extraction Status
- Files total (in-scope business logic): 20 read + 2 dead-code confirmed
- Rules extracted: 26 BR-IDs + 1 negative finding
- Source vectors: counted per-rule (8-dimension tables in 01-business-rules.md); consistent with the
  Phase 1 per-component vectors, refined by this read.

## Session Log
| Session | Files | Rules added | Notes |
|---------|-------|-------------|-------|
| 1 | 1-20 (all) | 26 BR-IDs + GEO finding | Single session; files small (≤269 LOC), full reads. 6 net-new findings recorded. |
