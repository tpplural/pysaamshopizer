# MS-01 reference-data — Component Inventory

**Analysis mode:** Direct Source Read. All paths relative to
`initial-source/shopizer/`. Vectors (where cited) are the 8-dimension source vectors
from the Phase 1 summary, confirmed/corrected by this deep read.

## In-scope components (business logic — READ in full)

### Entities (sm-core-model)
| Component                                             | LOC | Classification | Disposition              | Notes                                                                                                  |
| ----------------------------------------------------- | --- | -------------- | ------------------------ | ------------------------------------------------------------------------------------------------------ |
| `.../reference/country/model/Country.java`            | 130 | Entity         | EXTRACTED (domain model) | ISO unique/not-null; transient `name`; `geoZone` ManyToOne; `supported` default true                   |
| `.../reference/country/model/CountryDescription.java` | 43  | Entity         | EXTRACTED                | unique(COUNTRY_ID, LANGUAGE_ID)                                                                        |
| `.../reference/currency/model/Currency.java`          | 90  | Entity         | EXTRACTED                | code/currencyCode/name unique; **`getCode()` uses `!=` ref-compare (defect, NEW)**                     |
| `.../reference/language/model/Language.java`          | 114 | Entity         | EXTRACTED                | CODE not-null, **no unique constraint**; `sortOrder` unused; audited; `equals` on id                   |
| `.../reference/zone/model/Zone.java`                  | 102 | Entity         | EXTRACTED                | ZONE_CODE unique/not-null; COUNTRY_ID not-null; **3-arg ctor overwrites code with name (defect, NEW)** |
| `.../reference/zone/model/ZoneDescription.java`       | 43  | Entity         | EXTRACTED                | unique(ZONE_ID, LANGUAGE_ID)                                                                           |
| `.../reference/geozone/model/GeoZone.java`            | 92  | Entity         | EXTRACTED (inert)        | `// TODO : create DAO / Service` — no DAO/service/seed/reader; ships empty                             |
| `.../reference/geozone/model/GeoZoneDescription.java` | 36  | Entity         | EXTRACTED (inert)        | unique(GEOZONE_ID, LANGUAGE_ID)                                                                        |

### Services + DAOs (sm-core)
| Component | LOC | Classification | Disposition | Rules |
|-----------|-----|----------------|-------------|-------|
| `.../reference/country/service/CountryServiceImpl.java` | 125 | Service | EXTRACTED | BR-REF-RES-001, LST-001, LST-002, CAC-001, CAC-002, LST-004, LST-005 |
| `.../reference/country/dao/CountryDaoImpl.java` | 36 | DAO | EXTRACTED | BR-REF-LST-001 |
| `.../reference/currency/service/CurrencyServiceImpl.java` | 25 | Service | EXTRACTED | BR-REF-RES-003 |
| `.../reference/currency/dao/CurrencyDaoImpl.java` | 35 | DAO | EXTRACTED | BR-REF-LST-006 |
| `.../reference/language/service/LanguageServiceImpl.java` | 108 | Service | EXTRACTED | BR-REF-RES-002, LST-003, LNG-001, LNG-002, CAC-001 |
| `.../reference/language/dao/LanguageDaoImpl.java` | 10 | DAO (empty) | ACCOUNTED | inherits generic `list()`/`count()`; no own logic |
| `.../reference/zone/service/ZoneServiceImpl.java` | 132 | Service | EXTRACTED | BR-REF-RES-004, LST-002, CAC-001, CAC-002 |
| `.../reference/zone/dao/ZoneDaoImpl.java` | 54 | DAO | EXTRACTED | BR-REF-LST-002 |
| `.../reference/init/service/InitializationDatabaseImpl.java` | 269 | Seed | EXTRACTED | BR-REF-SEED-001..007 |
| `.../utils/reference/ZonesLoader.java` | 142 | Seed helper | EXTRACTED | BR-REF-SEED-004 |
| `.../web/reference/ReferenceController.java` | 257 | Controller (AJAX) | EXTRACTED | BR-REF-API-001, API-002, LNG-003, API-003 |

### Interfaces (declaration-only — skimmed for signatures)
`CountryService`, `CurrencyService`, `LanguageService`, `ZoneService`, `InitializationDatabase`,
`CountryDao`, `CurrencyDao` (empty), `LanguageDao` (empty), `ZoneDao`. No rules — contracts only.

## Out-of-scope / supporting (read for evidence, not owned here)
| Component | Reason |
|-----------|--------|
| `SchemaConstant` | Seed constants (COUNTRY_ISO_CODE, CURRENCY_MAP, LANGUAGE_ISO_CODE, LOCALES). Evidence for seed content; owned as config data, not a rule subject. |
| `InitializationLoader` (sm-shop) | `@PostConstruct` — the sole caller of `populate()`. Trigger only; lives in bootstrap, out of segment. |
| `SalesManagerEntityServiceImpl` / `...DaoImpl` | Generic base `getByField`/`count`/`list`/`create`. Cross-cutting infrastructure. |
| `CacheUtils` | Application EhCache wrapper. Infrastructure — described by BR-REF-CAC-001. |
| `IntegrationModulesLoader` (190 LOC) | Loads `integrationmodules.json`; cross-domain (system module config). Seed touches it; NOT reference-data's owned logic — see BR-REF-SEED-007 boundary note. |

## Dead code (SKIP — confirmed no caller)
| Component | LOC | Evidence |
|-----------|-----|----------|
| `.../reference/zone/imports/ZoneLoader.java` | 31 | Not referenced by any caller; the seed uses `utils/reference/ZonesLoader` (different class). |
| `.../reference/zone/imports/ZoneTransient.java` | 28 | Only used by the dead `ZoneLoader`. |

## Cross-domain seed coupling (broken in target — per services-composition.md)
The legacy seed transaction also writes MERCHANT_STORE, MERCHANT_LANGUAGE, TAX_CLASS, PRODUCT_TYPE,
MODULE_CONFIGURATION. These are **NOT** owned by MS-01 in the target — each destination service seeds
its own defaults (boundary decision, risk R-05). Captured here as BR-REF-SEED-006 / SEED-007 with an
explicit "moved out of this service" disposition so the behavior is traceable, not silently dropped.
