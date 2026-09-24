# reference-data (MS-01) — Business Rules

**Version:** 1.0 · **Status:** 🟢 Extraction complete
**Domain code:** REF · **Groups:** RES (code resolution), LST (localized lists), CAC (caching),
LNG (language/locale), API (reference endpoints), SEED (bootstrap).
**Analysis mode:** Direct Source Read.

> **Statement discipline:** every `Statement` below is a business-domain sentence. Legacy
> table/column/class names appear ONLY in `Logic` (evidence for traceability). Source vector counts in
> each Semantic Preservation table are honest counts from the deep read; where a source dimension is
> pure infrastructure (retry/logging/transaction) it is intentionally NOT carried into the spec and the
> gap is annotated as infra-noise (acceptable), not condensation.

---

## Group RES — Code / ISO resolution

### BR-REF-RES-001: Country is resolved by its ISO code

**Cross-Reference (Phase 1):** BR-REF-001
**Source Reference:** `sm-core/.../reference/country/service/CountryServiceImpl.java` : `getByCode` : lines 40-42; entity `Country.java` : 50-51 (COUNTRY_ISOCODE unique, not null)
**Discovery Method:** Direct Source Read

**Statement:** A country is uniquely identified and retrieved by its ISO country code. Looking up an unknown code returns no country rather than an error.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getByCode(code) -> countryDao.getByField(Country_.isoCode, code)
// COUNTRY_ISOCODE is unique + not null at the DB level; returns the single Country or null
```
**Data Dependencies:**
- Reads: `COUNTRY.COUNTRY_ISOCODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (found / not-found) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries/CA`
- Success: `200 {"isoCode":"CA","supported":true,"name":"Canada"}`
- Error Input: `GET /api/v1/reference/countries/ZZ`
- Error Output: `404 {"error":"NotFound","message":"No country for ISO code ZZ","statusCode":404}`

---

### BR-REF-RES-002: Language is resolved by its language code

**Cross-Reference (Phase 1):** BR-REF-002
**Source Reference:** `sm-core/.../reference/language/service/LanguageServiceImpl.java` : `getByCode` : lines 33-35; entity `Language.java` : 43-44 (CODE not null)
**Discovery Method:** Direct Source Read

**Statement:** A language is retrieved by its language code (for example "en" or "fr"). An unknown code yields no language. Note: the legacy system enforces language-code distinctness only through the seed, not a database uniqueness constraint — the target must add the constraint (see INV-REF-002).
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getByCode(code) -> getByField(Language_.code, code)
// LANGUAGE.CODE is nullable=false but has NO unique constraint on the entity;
// distinctness is guaranteed only by createLanguages() at seed time
```
**Data Dependencies:**
- Reads: `LANGUAGE.CODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/languages/en`
- Success: `200 {"code":"en","sortOrder":null}`
- Error Input: `GET /api/v1/reference/languages/xx`
- Error Output: `404 {"error":"NotFound","message":"No language for code xx","statusCode":404}`

---

### BR-REF-RES-003: Currency is resolved by its currency code (uncached)

**Cross-Reference (Phase 1):** BR-REF-003
**Source Reference:** `sm-core/.../reference/currency/service/CurrencyServiceImpl.java` : `getByCode` : lines 19-21; entity `Currency.java` : 36-38 (CURRENCY_CODE unique)
**Discovery Method:** Direct Source Read

**Statement:** A currency is retrieved by its ISO-4217 currency code (for example "CAD"). Unlike countries, languages and zones, currency lookups are not memoized in the application cache. An unknown code yields no currency.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getByCode(code) -> getByField(Currency_.code, code)
// no CacheUtils wrapper here (contrast CountryServiceImpl / ZoneServiceImpl / LanguageServiceImpl)
```
**Data Dependencies:**
- Reads: `CURRENCY.CURRENCY_CODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/currencies/CAD`
- Success: `200 {"code":"CAD","name":"CAD","supported":true}`
- Error Input: `GET /api/v1/reference/currencies/ABC`
- Error Output: `404 {"error":"NotFound","message":"No currency for code ABC","statusCode":404}`

---

### BR-REF-RES-004: Zone is resolved by its globally-unique zone code

**Cross-Reference (Phase 1):** BR-REF-004
**Source Reference:** `sm-core/.../reference/zone/service/ZoneServiceImpl.java` : `getByCode` : lines 42-44; entity `Zone.java` : 44-45 (ZONE_CODE unique, not null)
**Discovery Method:** Direct Source Read

**Statement:** A zone (state or province) is retrieved by its zone code, which is globally unique across all countries — not scoped per country. An unknown code yields no zone.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getByCode(code) -> getByField(Zone_.code, code)
// ZONE_CODE unique across the whole table (not per-country)
```
**Data Dependencies:**
- Reads: `ZONE.ZONE_CODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/zones/QC`
- Success: `200 {"code":"QC","countryIsoCode":"CA","name":"Quebec"}`
- Error Input: `GET /api/v1/reference/zones/ZZ`
- Error Output: `404 {"error":"NotFound","message":"No zone for code ZZ","statusCode":404}`

---

## Group LST — Localized, name-sorted reference lists

### BR-REF-LST-001: Countries are listed in one language, name-sorted, each named by its localized description

**Cross-Reference (Phase 1):** BR-REF-005, BR-REF-006
**Source Reference:** `sm-core/.../reference/country/dao/CountryDaoImpl.java` : `listByLanguage` : lines 19-33; naming applied `CountryServiceImpl.java : getCountries` : 100-108
**Discovery Method:** Direct Source Read

**Statement:** When countries are requested for a given language, only countries that have a name in that language are returned, ordered alphabetically by that localized name, and each country carries its localized name for display. If a returned country has no name in the requested language the list cannot be built and the caller receives no list (see BR-REF-CAC-002) — the target must guarantee every supported country has a name in every supported language (see INV-REF-004).
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
listByLanguage(language):
  from Country c left join fetch c.descriptions d
  where d.language.id = :language.id            // description filter => effectively inner-filters countries
  order by d.name asc
then in getCountries(language):
  for each country: country.name = country.getDescriptions().get(0).name   // .get(0) unguarded
  // if descriptions empty => IndexOutOfBoundsException, swallowed by BR-REF-CAC-002 => null list
```
**Data Dependencies:**
- Reads: `COUNTRY`, `COUNTRY_DESCRIPTION.LANGUAGE_ID`, `COUNTRY_DESCRIPTION.name`
- Writes: — (mutates transient display name only)

**Side Effects:** None (transient field set).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (join filter + per-row name loop) |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (list / empty-or-null) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (unguarded first-description → null list) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries?language=en`
- Success: `200 {"items":[{"isoCode":"AF","name":"Afghanistan","supported":true}, {"isoCode":"AL","name":"Albania","supported":true}]}`  (alphabetical by localized name)
- Error Input: `GET /api/v1/reference/countries?language=zz`  (no descriptions exist for zz)
- Error Output: `200 {"items":[]}`  (fail-soft empty; legacy returns null — target normalizes to empty list)

---

### BR-REF-LST-002: Zones are listed by country and language, name-sorted, each named by its localized description

**Cross-Reference (Phase 1):** BR-REF-007
**Source Reference:** `sm-core/.../reference/zone/dao/ZoneDaoImpl.java` : `listByLanguageAndCountry` : 19-36, `listByLanguage` : 38-53; naming applied `ZoneServiceImpl.java` : 76-83, 105-116
**Discovery Method:** Direct Source Read

**Statement:** The zones of a country are returned for a given language — only zones that have a name in that language, ordered alphabetically by that localized name, each carrying its localized name. Zones belong to a country, so requesting a country's zones returns exactly that country's zones. A language-only request (no country) returns every zone that has a name in that language, keyed by zone code.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
listByLanguageAndCountry(country, language):
  from Zone z left join fetch z.descriptions d
  where d.language.id = :language.id AND z.country.isoCode = :country.isoCode
  order by d.name asc
listByLanguage(language): same, without the country predicate
then: for each zone: zone.name = zone.getDescriptions().get(0).name
  // language-only variant collects into Map<zoneCode, Zone>
```
**Data Dependencies:**
- Reads: `ZONE`, `ZONE_DESCRIPTION.LANGUAGE_ID`, `ZONE_DESCRIPTION.name`, `ZONE.COUNTRY_ID` → `COUNTRY.COUNTRY_ISOCODE`
- Writes: —

**Side Effects:** None (transient name set).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (2 query shapes + naming loop) |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (unguarded first-description → null, swallowed) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries/CA/zones?language=en`
- Success: `200 {"items":[{"code":"AB","name":"Alberta","countryIsoCode":"CA"}, {"code":"QC","name":"Quebec","countryIsoCode":"CA"}]}`
- Error Input: `GET /api/v1/reference/countries/CA/zones?language=zz`
- Error Output: `200 {"items":[]}`

---

### BR-REF-LST-003: All seeded languages are listed (code-keyed)

**Cross-Reference (Phase 1):** BR-REF-016
**Source Reference:** `sm-core/.../reference/language/service/LanguageServiceImpl.java` : `getLanguages` : 76-100, `getLanguagesMap` : 57-71
**Discovery Method:** Direct Source Read

**Statement:** All configured languages are returned as a list (and as a code-keyed map). The legacy system does not apply any explicit ordering to this list and does not honor the language display-order field, even though one exists — the target should order by that field so language pickers are deterministic (see net-new finding NF-4).
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getLanguages() -> cached list() of all Language rows (no filter, no explicit order-by in code)
getLanguagesMap() -> LinkedHashMap<code, Language> over getLanguages()
// Language.sortOrder column exists but is never used in any order-by (flagged)
```
**Data Dependencies:**
- Reads: `LANGUAGE` (all rows), `LANGUAGE.CODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (map build loop) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK (caching error path covered by BR-REF-CAC-002) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/languages`
- Success: `200 {"items":[{"code":"en","sortOrder":null},{"code":"fr","sortOrder":null}]}`
- Error Input: `GET /api/v1/reference/languages?limit=-1`
- Error Output: `400 {"error":"BadRequest","message":"limit must be >= 0","statusCode":400}`

---

### BR-REF-LST-004: Country map is insertion-ordered by ISO code (preserving name-sort)

**Cross-Reference (Phase 1):** BR-REF-011
**Source Reference:** `sm-core/.../reference/country/service/CountryServiceImpl.java` : `getCountriesMap` : 50-62
**Discovery Method:** Direct Source Read

**Statement:** Countries can be requested as an ISO-code-keyed map for a language; the map preserves the alphabetical-by-localized-name order of the underlying list. This map is how a posted country code is resolved to its full country for the province lookup.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
getCountriesMap(language):
  for each country in getCountries(language):  // already name-sorted
    map.put(country.isoCode, country)          // LinkedHashMap preserves order
```
**Data Dependencies:**
- Reads: `COUNTRY.COUNTRY_ISOCODE` (via BR-REF-LST-001)
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries?language=en&as=map`
- Success: `200 {"AF":{"isoCode":"AF","name":"Afghanistan"},"AL":{"isoCode":"AL","name":"Albania"}}`
- Error Input: `GET /api/v1/reference/countries?language=en&as=tree`
- Error Output: `400 {"error":"BadRequest","message":"Unsupported 'as' value: tree","statusCode":400}`

---

### BR-REF-LST-005: Countries can be filtered to a requested subset of ISO codes

**Cross-Reference (Phase 1):** BR-REF-012
**Source Reference:** `sm-core/.../reference/country/service/CountryServiceImpl.java` : `getCountries(List,Language)` : 65-77
**Discovery Method:** Direct Source Read

**Statement:** A caller can request the localized country list narrowed to a specific set of ISO codes — only the requested countries are returned, in the same localized order. This backs "supported countries" style selections. An empty or unresolved base list yields an empty result.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getCountries(isoCodes, language):
  countryList = getCountries(language)
  if countryList not empty:
    for each c in countryList: if isoCodes.contains(c.isoCode): keep c
  return kept (empty if base list null/empty)
```
**Data Dependencies:**
- Reads: `COUNTRY.COUNTRY_ISOCODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (empty guard + filter loop) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (subset / empty) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries?language=en&isoCodes=CA,US,MX`
- Success: `200 {"items":[{"isoCode":"CA","name":"Canada"},{"isoCode":"MX","name":"Mexico"},{"isoCode":"US","name":"United States"}]}`
- Error Input: `GET /api/v1/reference/countries?language=en&isoCodes=`
- Error Output: `200 {"items":[]}`

---

### BR-REF-LST-006: Currencies are listed ordered by currency code

**Cross-Reference (Phase 1):** BR-REF-003 (list variant)
**Source Reference:** `sm-core/.../reference/currency/dao/CurrencyDaoImpl.java` : `list` : 17-31
**Discovery Method:** Direct Source Read

**Statement:** All currencies are returned ordered alphabetically by currency code. This is a plain, uncached listing.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
list():
  from Currency c order by c.code asc
```
**Data Dependencies:**
- Reads: `CURRENCY.CURRENCY_CODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (order-by) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/currencies`
- Success: `200 {"items":[{"code":"AED","name":"AED"},{"code":"CAD","name":"CAD"},{"code":"USD","name":"USD"}]}`
- Error Input: `GET /api/v1/reference/currencies?page=abc`
- Error Output: `400 {"error":"BadRequest","message":"page must be an integer","statusCode":400}`

---

## Group CAC — Caching behavior

### BR-REF-CAC-001: Reference lists are memoized in an application cache with derived keys

**Cross-Reference (Phase 1):** BR-REF-008, BR-REF-010
**Source Reference:** `CountryServiceImpl.java` : 95-110; `LanguageServiceImpl.java` : 76-100; `ZoneServiceImpl.java` : 63-88, 100-116
**Discovery Method:** Direct Source Read

**Statement:** Reference lists are read-through cached and treated as effectively immutable after the initial seed: countries are cached per language, zones per country-and-language (and per language for the map), languages under a single key. On a cache miss the data is loaded and stored; there is no eviction of reference entries anywhere, so an edit to reference data would not be visible until the process restarts. The target should keep these lists cached but provide an explicit invalidation hook, since a real edit path may exist in the modernized system.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
Countries key   = "COUNTRIES_" + language.code
Zones key       = "ZONES_" + country.isoCode + "_" + language.code   (list)
Zones-map key   = "ZONES_" + language.code                            (Map<zoneCode,Zone>)
Languages key   = "LANGUAGES"
read-through: v = cache.getFromCache(key); if v==null { v = dao...; cache.putInCache(v,key) }
// no removeFromCache for these keys anywhere in the segment (CacheUtils.removeAllFromCache only
//   evicts numeric store-id-prefixed keys, which these are not)
// Country/Language/Currency entities are ALSO JPA @Cacheable (Hibernate L2 — a distinct layer);
//   Zone is NOT @Cacheable
```
**Data Dependencies:**
- Reads: `COUNTRY`, `LANGUAGE`, `ZONE` (+ descriptions) via their list rules
- Writes: in-memory cache only

**Side Effects:** Writes derived lists into the application cache.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (miss branch × 3 services) |
| Data-flow | 4 | 4 | OK (4 cache keys) |
| Constants | 1 | 1 | OK (ZONES_ prefix / key templates) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (hit / miss-then-load) |
| Data writes | 1 | 1 | OK (putInCache) |
| Integrations | 1 | 1 | OK (application cache) |
| Error paths | 0 | 0 | OK (failure path is BR-REF-CAC-002) |
**Preservation:** OK

**Concrete Example:**
- Input: two successive `GET /api/v1/reference/countries?language=en`
- Success: first call loads from store and caches; second call returns the cached list (same payload, no store read)
- Error Input: cache backend unavailable on read
- Error Output: falls through to a store load (fail-soft — see BR-REF-CAC-002); response still `200` with the list

---

### BR-REF-CAC-002: Reference list/lookup failures are swallowed and yield an empty result, never a thrown error

**Cross-Reference (Phase 1):** BR-REF-009
**Source Reference:** `CountryServiceImpl.java` : 111-114; `LanguageServiceImpl.java` : 45-53, 98-100; `ZoneServiceImpl.java` : 85-87, 114-116
**Discovery Method:** Direct Source Read

**Statement:** Any failure while building a reference list — a cache error, a missing localized name, or a data-access error — is logged and results in no list being returned rather than an error surfaced to the caller. Callers therefore always treat a missing reference list as "empty", never as a failure. The target normalizes the legacy null to an empty collection with a 200 response, preserving the fail-soft contract.
**Intent:** Validation (error path)
**Weight:** Medium

**Logic:**
```
each list method body wrapped in: try { ...load... } catch (Exception e) { LOGGER.error(...) }
return (possibly null) localVar
// declared 'throws ServiceException' is never actually thrown by these read methods
```
**Data Dependencies:**
- Reads: —
- Writes: —

**Side Effects:** Logs the error; returns null (target: empty collection).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK (catch × 4 sites) |
| Data-flow | 0 | 0 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (null/empty return) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 4 | 4 | OK (one swallow per list site) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries?language=en` while the underlying store errors
- Success (fail-soft): `200 {"items":[]}` with a server-side error logged
- Error Input: same request, store errors AND strict mode is off (default)
- Error Output: `200 {"items":[]}` — never a 5xx from the read path (legacy contract preserved)

---

## Group LNG — Language / locale conversion and defaulting

### BR-REF-LNG-001: A language converts to a locale using its code as the language tag

**Cross-Reference (Phase 1):** BR-REF-013
**Source Reference:** `sm-core/.../reference/language/service/LanguageServiceImpl.java` : `toLocale` : 37-39
**Discovery Method:** Direct Source Read

**Statement:** A language is converted to a locale using only its two-letter code as the language part, with no country or variant. This locale is what drives localized country/zone name generation at seed time.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
toLocale(language) -> new Locale(language.code)   // e.g. "en" -> Locale("en")
```
**Data Dependencies:**
- Reads: `LANGUAGE.CODE`
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: language `{"code":"fr"}`
- Success: locale language tag `"fr"`
- Error Input: language `{"code":null}`
- Error Output: `400 {"error":"BadRequest","message":"Language code required to build locale","statusCode":400}`

---

### BR-REF-LNG-002: A locale maps back to a configured language, or nothing if unsupported

**Cross-Reference (Phase 1):** BR-REF-014
**Source Reference:** `sm-core/.../reference/language/service/LanguageServiceImpl.java` : `toLanguage` : 41-54
**Discovery Method:** Direct Source Read

**Statement:** A locale is mapped back to a configured language by matching its language part against the configured language set. If the locale's language is not configured (only English and French ship by default), no language is returned and the caller is responsible for choosing a fallback.
**Intent:** Calculation (fallback)
**Weight:** Medium

**Logic:**
```
toLanguage(locale):
  try { return getLanguagesMap().get(locale.getLanguage()) }   // null on miss
  catch (Exception) { LOGGER.error(...); return null }
```
**Data Dependencies:**
- Reads: `LANGUAGE.CODE`
- Writes: —

**Side Effects:** Logs on exception; returns null on miss.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (map lookup) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (match / null) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (swallowed exception → null) |
**Preservation:** OK

**Concrete Example:**
- Input: locale `en_US` → resolve language
- Success: `200 {"code":"en"}`
- Error Input: locale `de_DE` (German not configured)
- Error Output: `204 No Content` (no language matched — caller applies default per BR-REF-LNG-003)

---

### BR-REF-LNG-003: Storefront language defaults to English when none can be resolved

**Cross-Reference (Phase 1):** BR-REF-015
**Source Reference:** `sm-shop/.../web/reference/ReferenceController.java` : `getProvinces` : 75-96 (language precedence); `Constants.DEFAULT_LANGUAGE = "en"`
**Discovery Method:** Direct Source Read

**Statement:** When resolving the language for a reference request, an explicitly supplied language code wins; failing that, the request's ambient language is used; failing that, the system falls back to English. English is the system-wide default language.
**Intent:** Routing (defaulting)
**Weight:** Medium

**Logic:**
```
resolveLanguage(request):
  if request.lang not blank:      language = languageService.getByCode(request.lang)
  if language == null:            language = request attribute "LANGUAGE"
  if language == null:            language = languageService.getByCode(Constants.DEFAULT_LANGUAGE)  // "en"
```
**Data Dependencies:**
- Reads: `LANGUAGE.CODE` (including the literal `'en'`)
- Writes: —

**Side Effects:** None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (3-step precedence) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (DEFAULT_LANGUAGE="en") |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (resolved explicit/ambient / defaulted) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/reference/provinces` body `{"countryCode":"CA"}` with no language anywhere
- Success: resolves to English; `200 {"status":"SUCCESS","items":[{"name":"Quebec","code":"QC","id":123}]}`
- Error Input: `POST /api/v1/reference/provinces` body `{"countryCode":"CA","lang":"zz"}` (zz not configured, no ambient) → still falls back to "en"
- Error Output: `200 {"status":"SUCCESS","items":[...]}` (defaulting never errors; unknown lang silently becomes "en")

---

## Group API — Reference endpoints (storefront/admin AJAX)

### BR-REF-API-001: The provinces endpoint returns a country's localized zones for address forms, fail-soft

**Cross-Reference (Phase 1):** BR-REF-017
**Source Reference:** `sm-shop/.../web/reference/ReferenceController.java` : `getProvinces` : 71-127
**Discovery Method:** Direct Source Read

**Statement:** Given a country code (and an optional language), the provinces endpoint returns that country's zones as a list of display-name / code / id entries for populating an address-form province dropdown. It resolves the language by the standard precedence, and always returns a well-formed response: a success payload with the zones, an empty success payload if the country has no zones, or a failure status if anything goes wrong — never an unhandled error.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
getProvinces(countryCode, lang):
  language = resolveLanguage(...)                       // BR-REF-LNG-003
  country  = countryService.getCountriesMap(language).get(countryCode)
  zones    = zoneService.getZones(country, language)    // BR-REF-LST-002
  if zones not empty: for each zone emit {name, code, id}; status = SUCCESS
  catch (Exception): status = FAILURE
  return JSON
```
**Data Dependencies:**
- Reads: `COUNTRY`, `ZONE` (+ descriptions) via services
- Writes: —

**Side Effects:** None (read + serialize). Note: legacy maps this at both `/admin/...` and `/shop/...`.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (lang chain folded to LNG-003 + zones-present + catch) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (SUCCESS/FAILURE status) |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK (zones / empty / failure) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (country + zone services) |
| Error paths | 1 | 1 | OK (catch → FAILURE) |
**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/reference/provinces` body `{"countryCode":"CA","lang":"en"}`
- Success: `200 {"status":"SUCCESS","items":[{"name":"Alberta","code":"AB","id":101},{"name":"Quebec","code":"QC","id":110}]}`
- Error Input: `POST /api/v1/reference/provinces` body `{"countryCode":"ZZ"}` (unknown country → null country → zones lookup fails)
- Error Output: `200 {"status":"FAILURE","items":[]}` (fail-soft — legacy never 5xx here)

---

### BR-REF-API-002: Country and zone name lookups echo the code when a display name cannot be resolved

**Cross-Reference (Phase 1):** BR-REF-018
**Source Reference:** `sm-shop/.../web/reference/ReferenceController.java` : `countryName` : 129-149, `zoneName` : 151-171
**Discovery Method:** Direct Source Read

**Statement:** Resolving a country code or zone code to a localized display name always yields a usable string: the localized name when it can be resolved, otherwise the input code itself. A missing language, a missing map, a missing entry, or a lookup error all degrade gracefully to returning the raw code rather than failing.
**Intent:** Routing (fallback)
**Weight:** Medium

**Logic:**
```
countryName(countryCode, request):
  language = languageUtils.getRequestLanguage(request); if language == null: return countryCode
  map = countryService.getCountriesMap(language)
  if map != null and map.get(countryCode) != null: return that.name
  catch (ServiceException): log
  return countryCode
// zoneName is identical over zoneService.getZones(language) map
```
**Data Dependencies:**
- Reads: `COUNTRY`/`ZONE` display names
- Writes: —

**Side Effects:** Logs on error.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK (null-lang, null-map, null-entry, catch — × 2 endpoints share the shape) |
| Data-flow | 2 | 2 | OK (country + zone names) |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (name / echoed code) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (services) |
| Error paths | 2 | 2 | OK (ServiceException per endpoint → echo code) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/countries/CA/name?language=en`
- Success: `200 "Canada"`
- Error Input: `GET /api/v1/reference/countries/ZZ/name?language=en` (no such country)
- Error Output: `200 "ZZ"` (echoes the code — never 404 for this endpoint)

---

### BR-REF-API-003: Credit-card expiry option lists (years and months) are generated and cached

**Cross-Reference (Phase 1):** (net-new detail on ReferenceController credit-card/months endpoints — P1 listed them but extracted no rule)
**Source Reference:** `sm-shop/.../web/reference/ReferenceController.java` : `getCreditCardDates` : 173-217, `getMonthsOfYear` : 220-250
**Discovery Method:** Direct Source Read

**Statement:** The reference service supplies the option lists that populate card-expiry pickers: a rolling list of ten years starting at the current year, and the twelve months of the year as two-digit strings. Both lists are computed once and cached, since they change at most once per year.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
getCreditCardDates():
  years = cache["CREDIT_CARD_YEARS"]
  if null: years = [ formatYear(now + i) for i in 0..9 ]  // current year .. current+9 (10 entries)
           cache.put(years, "CREDIT_CARD_YEARS")
  return years
getMonthsOfYear():
  months = cache["MONTHS_OF_YEAR"]
  if null: months = [ String.format("%02d", i) for i in 1..12 ]  // "01".."12"
           cache.put(months, "MONTHS_OF_YEAR")
```
**Data Dependencies:**
- Reads: system clock (current year); no database
- Writes: application cache

**Side Effects:** Writes the year/month lists into the application cache.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (miss branch × 2) |
| Data-flow | 0 | 0 | OK (no DB) |
| Constants | 3 | 3 | OK (10-year span, months 1..12, "%02d") |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (years / months) |
| Data writes | 1 | 1 | OK (cache put) |
| Integrations | 1 | 1 | OK (cache) |
| Error paths | 1 | 1 | OK (catch swallows → null serialized) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/reference/credit-card-years` in year 2025
- Success: `200 ["2025","2026","2027","2028","2029","2030","2031","2032","2033","2034"]`
- Error Input: `GET /api/v1/reference/months-of-year` (no params needed)
- Error Output (bad accept negotiation): `406 {"error":"NotAcceptable","message":"Only application/json","statusCode":406}`

---

## Group SEED — One-time database bootstrap

### BR-REF-SEED-001: The reference data is seeded only when the database is empty

**Cross-Reference (Phase 1):** BR-REF-019
**Source Reference:** `sm-core/.../reference/init/service/InitializationDatabaseImpl.java` : `isEmpty` : 74-76; caller `InitializationLoader.java` : ~63 (sm-shop, `@PostConstruct`)
**Discovery Method:** Direct Source Read

**Statement:** On application startup the reference data is populated only if it has never been populated. "Never populated" is determined by there being no configured languages. Because languages are created first during the seed, a completed seed permanently disables any re-seed on later startups. This is the single guard against duplicate seeding.
**Intent:** Validation (guard)
**Weight:** Medium

**Logic:**
```
isEmpty() <=> languageService.count() == 0
InitializationLoader.init() @PostConstruct:
  if initializationDatabase.isEmpty(): initializationDatabase.populate(contextName)
// createLanguages() runs first in populate(), so after a successful seed count()>0 forever
```
**Data Dependencies:**
- Reads: `LANGUAGE` (row count)
- Writes: —

**Side Effects:** None (read-only check).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (if-empty) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (count == 0) |
| State transitions | 1 | 1 | OK (references the Empty→Seeded gate) |
| Outcomes | 2 | 2 | OK (seed / skip) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (startup lifecycle trigger) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: application starts against an empty schema (zero languages)
- Success: the seed runs; afterward the reference tables are populated and the seed will not run again
- Error Input: application starts against an already-seeded schema
- Error Output: seed is skipped (no-op); startup proceeds — no error, no duplicate rows

---

### BR-REF-SEED-002: The full seed is one ordered, all-or-nothing transaction

**Cross-Reference (Phase 1):** BR-REF-020
**Source Reference:** `sm-core/.../reference/init/service/InitializationDatabaseImpl.java` : `populate` : 78-90 (`@Transactional`)
**Discovery Method:** Direct Source Read

**Statement:** The bootstrap runs as a single atomic transaction in a fixed order: languages, then countries, then zones, then currencies, then dependent references, then the default store. The order is required because later steps depend on earlier ones (countries need languages for their names; zones need countries; the default store needs specific language, country, currency and zone to already exist). If any step fails the entire seed rolls back, so a partial, half-seeded database can never satisfy the "already seeded" guard.
**Intent:** State Transition (bootstrap)
**Weight:** Medium

**Logic:**
```
@Transactional populate(contextName):
  createLanguages()      // BR-REF-SEED-003
  createCountries()      // BR-REF-SEED-004a
  createZones()          // BR-REF-SEED-004
  createCurrencies()     // BR-REF-SEED-005
  createSubReferences()  // cross-domain (moved out — SEED-007)
  createModules()        // cross-domain (moved out — SEED-007)
  createMerchant()       // cross-domain (moved out — SEED-006)
// any exception rolls the whole transaction back
```
**Data Dependencies:**
- Reads: — · Writes: all reference tables (+ cross-domain, see SEED-006/007)

**Side Effects:** Inserts across LANGUAGE, COUNTRY(+desc), ZONE(+desc), CURRENCY (+ cross-domain in legacy).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (sequential composition) |
| Data-flow | 4 | 4 | OK (owned reference tables) |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (Empty→Seeded) |
| Outcomes | 2 | 2 | OK (committed / rolled back) |
| Data writes | 4 | 4 | OK (owned writes; cross-domain writes accounted in SEED-006/007) |
| Integrations | 1 | 1 | OK (transaction manager) |
| Error paths | 1 | 1 | OK (rollback on any failure) |
**Preservation:** OK

**Concrete Example:**
- Input: seed invoked on an empty database
- Success: all reference tables populated in one commit; database transitions Empty→Seeded
- Error Input: the zone step fails (e.g. malformed zone config)
- Error Output: entire seed rolls back; database stays Empty; seed will retry on next startup

---

### BR-REF-SEED-003: The out-of-the-box languages are English and French

**Cross-Reference (Phase 1):** BR-REF-021
**Source Reference:** `InitializationDatabaseImpl.java` : `createLanguages` : 189-195; `SchemaConstant.LANGUAGE_ISO_CODE = {"en","fr"}`
**Discovery Method:** Direct Source Read

**Statement:** The system ships with exactly two languages, English and French. Their display-order is left unset at seed time.
**Intent:** Calculation (seed content)
**Weight:** Medium

**Logic:**
```
for code in LANGUAGE_ISO_CODE {"en","fr"}:
  languageService.create(new Language(code))   // sortOrder left null
```
**Data Dependencies:**
- Reads: `SchemaConstant.LANGUAGE_ISO_CODE`
- Writes: `LANGUAGE.CODE`

**Side Effects:** Inserts 2 language rows.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (loop) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK ({en, fr}) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: seed a fresh database
- Success: `LANGUAGE` contains `en` and `fr`
- Error Input: (config attempts a null language code)
- Error Output: seed aborts with a rollback (SEED-002); no partial language set persists

---

### BR-REF-SEED-004a: Countries are seeded from a fixed ISO list, but only those the platform can localize

**Cross-Reference (Phase 1):** BR-REF-022
**Source Reference:** `InitializationDatabaseImpl.java` : `createCountries` : 132-149; `SchemaConstant.COUNTRY_ISO_CODE` (246 entries), `SchemaConstant.LOCALES`
**Discovery Method:** Direct Source Read

**Statement:** Countries are created from a fixed catalog of ISO codes, but a country is created only if the platform can produce a localized name for it; codes with no platform locale are silently skipped. Each created country gets a localized name in every configured language. Because the createable set depends on the running platform's available locales, the seeded country set is platform-dependent — the target must pin the country catalog explicitly so it is deterministic (see net-new finding NF-5).
**Intent:** Calculation (seed content)
**Weight:** Medium

**Logic:**
```
languages = languageService.list()
for iso in COUNTRY_ISO_CODE (246):
  locale = LOCALES.get(iso)                 // JVM available-locales table
  if locale != null:                        // no locale => country SKIPPED
    country = new Country(iso); countryService.create(country)      // COUNTRY_SUPPORTED default true
    for language in languages:
      name = locale.getDisplayCountry(new Locale(language.code))
      countryService.addCountryDescription(country, new CountryDescription(language, name))  // one update() each
```
**Data Dependencies:**
- Reads: `SchemaConstant.COUNTRY_ISO_CODE`, platform locales, `LANGUAGE`
- Writes: `COUNTRY.COUNTRY_ISOCODE/COUNTRY_SUPPORTED`, `COUNTRY_DESCRIPTION.LANGUAGE_ID/name`

**Side Effects:** Inserts one country + one description per configured language; each description triggers a separate country update (chatty — Layer C candidate).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (iso loop, locale guard, language loop) |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK (246-code list, per-language localization) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (created / skipped) |
| Data writes | 2 | 2 | OK (country + description) |
| Integrations | 1 | 1 | OK (platform locale API) |
| Error paths | 1 | 1 | OK (no-locale skip) |
**Preservation:** OK

**Concrete Example:**
- Input: seed with languages {en, fr}, ISO "CA" present in the catalog and localizable
- Success: `COUNTRY` gets `CA` with descriptions "Canada" (en) and "Canada" (fr)
- Error Input: an ISO code with no platform locale (e.g. a deprecated code)
- Error Output: that code is skipped — no country row, no error, seed continues

---

### BR-REF-SEED-004: Zones are seeded from a country/language zone catalog, skipping unknown countries and duplicates

**Cross-Reference (Phase 1):** BR-REF-024
**Source Reference:** `InitializationDatabaseImpl.java` : `createZones` : 151-176; `sm-core/.../utils/reference/ZonesLoader.java` : `loadZones` : 33-135
**Discovery Method:** Direct Source Read

**Statement:** Zones (states/provinces) are created from a configurable zone catalog organized by language, where each entry names a zone, its display name, and the country it belongs to. A zone is created once per zone code and linked to its country; an entry whose country is not known is skipped with a warning, and a duplicate zone/language entry is skipped with a warning. Each created zone receives its localized names. A zone that ends up with no names is skipped. Because the catalog is a data file, an instance can ship a different set of zones without code change.
**Intent:** Calculation (seed content)
**Weight:** Medium

**Logic:**
```
loadZones(zoneCatalog):
  languages = languageService.list(); countriesByIso = map of countryService.list()
  for language l in languages:
    for entry in catalog[l.code]:
      if zoneCode not seen: zone = new Zone(); country = countriesByIso[entry.countryCode]
                            if country == null: warn + skip
                            zone.country = country; zone.code = zoneCode
      if (l.code + "_" + zoneCode) already marked: warn + skip   // per-(lang,zone) de-dup
      accumulate ZoneDescription(l, entry.zoneName) under zoneCode
  attach accumulated descriptions to each zone; return zonesByCode
createZones():
  for each zone in zonesByCode:
    if zone.descriptions == null: warn + skip
    detach descriptions; zoneService.create(zone); then addDescription per description
  // whole createZones wrapped: any exception -> ServiceException (aborts seed)
```
**Data Dependencies:**
- Reads: zone catalog resource, `LANGUAGE`, `COUNTRY`
- Writes: `ZONE.ZONE_CODE/COUNTRY_ID`, `ZONE_DESCRIPTION.LANGUAGE_ID/name`

**Side Effects:** Inserts zones and zone descriptions; aborts the seed transaction on any loader error.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK (lang loop, zone loop, new-zone guard, null-country skip, dup guard, null-desc skip) |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (catalog resource path) |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK (created / country-skip / dup-skip) |
| Data writes | 2 | 2 | OK (zone + description) |
| Integrations | 2 | 2 | OK (JSON resource + services) |
| Error paths | 2 | 2 | OK (null-country warn+skip, loader exception→abort) |
**Preservation:** OK

**Concrete Example:**
- Input: seed with a zone catalog entry `{"zoneCode":"QC","zoneName":"Quebec","countryCode":"CA"}` under "en"
- Success: `ZONE` gets `QC` linked to `CA`, with description "Quebec" (en)
- Error Input: a catalog entry `{"zoneCode":"XX","zoneName":"Nowhere","countryCode":"ZZ"}` where ZZ was never created
- Error Output: the XX entry is skipped with a warning; the rest of the catalog still seeds

---

### BR-REF-SEED-005: Currencies are seeded from a currency catalog, skipping codes the platform rejects

**Cross-Reference (Phase 1):** BR-REF-023
**Source Reference:** `InitializationDatabaseImpl.java` : `createCurrencies` : 93-130; `SchemaConstant.CURRENCY_MAP`
**Discovery Method:** Direct Source Read

**Statement:** Currencies are created from a currency catalog; each code is validated against the platform's ISO-4217 currency registry and any code the platform does not recognize is skipped. A created currency is marked supported. Note: the legacy seed stores the currency's code as its display name (never the human-readable name from the catalog) — a latent defect the target should correct by persisting the real name (see net-new finding NF-1/NF-2).
**Intent:** Calculation (seed content)
**Weight:** Medium

**Logic:**
```
for code in CURRENCY_MAP.keySet():        // HashMap => duplicate keys collapse, order unspecified
  try:
    c = java.util.Currency.getInstance(code)      // platform ISO-4217 lookup
    currency = new Currency()
    currency.setName(c.getCurrencyCode())         // NAME = the code, not the human name (defect)
    currency.setCurrency(c)                        // also re-derives code = c.getCurrencyCode()
    currencyService.create(currency)               // CURRENCY_SUPPORTED default true
  except IllegalArgumentException:                 // unknown code => log + skip
    continue
```
**Data Dependencies:**
- Reads: `SchemaConstant.CURRENCY_MAP`, platform currency registry
- Writes: `CURRENCY.CURRENCY_CODE/CURRENCY_CURRENCY_CODE/CURRENCY_NAME/CURRENCY_SUPPORTED`

**Side Effects:** Inserts one currency per resolvable distinct code.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (loop + try/catch) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (currency catalog) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (created / skipped) |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (platform currency API) |
| Error paths | 1 | 1 | OK (IllegalArgumentException skip) |
**Preservation:** OK

**Concrete Example:**
- Input: seed with catalog code "CAD"
- Success: `CURRENCY` gets a row `{code:"CAD", currencyCode:"CAD", name:"CAD", supported:true}`
- Error Input: catalog contains a bogus code "XYZ"
- Error Output: the platform rejects "XYZ"; it is logged and skipped; seeding continues

---

### BR-REF-SEED-006: Legacy seed also created the default store and its tax class — moved out of this service

**Cross-Reference (Phase 1):** BR-REF-026
**Source Reference:** `InitializationDatabaseImpl.java` : `createMerchant` : 213-247
**Discovery Method:** Direct Source Read

**Statement:** In the legacy system the same reference bootstrap also created a hardcoded default Canadian store (English, Canada, CAD, Quebec) and that store's default tax class, coupling reference-data seeding to the merchant and tax domains. In the target architecture this responsibility does NOT belong to reference-data: the default store is owned by the merchant-store service and the default tax class by the tax service (boundary decision, risk R-05). It is recorded here only for traceability — reference-data seeds ONLY geo/currency/language data.
**Intent:** State Transition (bootstrap) — **disposition: MOVED OUT of MS-01**
**Weight:** Medium

**Logic:**
```
// LEGACY (not reimplemented in MS-01):
en = getByCode("en"); ca = getByCode("CA"); cad = getByCode("CAD"); qc = getByCode("QC")
store = new MerchantStore(code=DEFAULT_STORE, country=CA, currency=CAD, defaultLanguage=en, zone=QC, ...)
merchantService.create(store)
taxClassService.create(new TaxClass(DEFAULT_TAX_CLASS) for store)
// if any of en/CA/CAD/QC is missing this NPEs and rolls back the whole seed
```
**Data Dependencies:**
- Reads (legacy): `LANGUAGE`, `COUNTRY`, `CURRENCY`, `ZONE` by code
- Writes (legacy, now other services): `MERCHANT_STORE`, `MERCHANT_LANGUAGE`, `TAX_CLASS`

**Side Effects:** In target MS-01: NONE. Reference-data may expose the resolved en/CA/CAD/QC values via its read API so merchant-store can seed its own default store.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 0 | OK (moved out — control lives in merchant-store) |
| Data-flow | 4 | 4 | OK (the 4 reads remain reference-data reads other services make) |
| Constants | 1 | 1 | OK (CA/CAD/en/QC defaults — now owned by merchant-store) |
| State transitions | 1 | 0 | OK (store bootstrap moved out) |
| Outcomes | 1 | 0 | OK (moved out) |
| Data writes | 2 | 0 | OK (writes belong to merchant-store + tax) |
| Integrations | 2 | 2 | OK (cross-service reads preserved) |
| Error paths | 1 | 0 | OK (NPE-on-missing moved out) |
**Preservation:** OK (intentional boundary relocation, not a loss — every moved write is owned by a named target service)

**Concrete Example:**
- Input: merchant-store service bootstraps its default store and calls `GET /api/v1/reference/countries/CA`, `.../currencies/CAD`, `.../zones/QC`, `.../languages/en`
- Success: reference-data returns each resolved entity; merchant-store creates its own default store
- Error Input: merchant-store requests zone `QC` before zones are seeded
- Error Output: `404` from reference-data; merchant-store handles its own bootstrap ordering (reference-data no longer NPEs the geo seed)

---

### BR-REF-SEED-007: Legacy seed also loaded a product type and integration modules — moved out of this service

**Cross-Reference (Phase 1):** BR-REF-027
**Source Reference:** `InitializationDatabaseImpl.java` : `createSubReferences` : 250-261, `createModules` : 249-266
**Discovery Method:** Direct Source Read

**Statement:** In the legacy system the reference bootstrap also created a general product type (catalog domain) and loaded the integration-module catalog (system domain) inside the same transaction. In the target architecture neither belongs to reference-data: the general product type is owned by the catalog service and integration modules by their owning system/config service. Recorded here for traceability only.
**Intent:** State Transition (bootstrap) — **disposition: MOVED OUT of MS-01**
**Weight:** Medium

**Logic:**
```
// LEGACY (not reimplemented in MS-01):
createSubReferences(): productTypeService.create(new ProductType(GENERAL_TYPE))   // catalog domain
createModules():       modules = modulesLoader.loadIntegrationModules("reference/integrationmodules.json")
                       for m in modules: moduleConfigurationService.create(m)      // system domain
```
**Data Dependencies:**
- Reads (legacy): `reference/integrationmodules.json`
- Writes (legacy, now other services): `PRODUCT_TYPE`, `MODULE_CONFIGURATION`

**Side Effects:** In target MS-01: NONE (each destination service seeds its own defaults).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 0 | OK (moved out) |
| Data-flow | 1 | 0 | OK (module JSON read moves to owner) |
| Constants | 1 | 1 | OK (GENERAL_TYPE — now catalog's constant) |
| State transitions | 1 | 0 | OK (moved out) |
| Outcomes | 1 | 0 | OK (moved out) |
| Data writes | 2 | 0 | OK (writes belong to catalog + system-config) |
| Integrations | 1 | 0 | OK (module loader moves to owner) |
| Error paths | 1 | 0 | OK (moved out) |
**Preservation:** OK (intentional boundary relocation — writes owned by catalog / system-config services, not dropped)

**Concrete Example:**
- Input: catalog service bootstraps its own `GENERAL` product type at its first startup
- Success: catalog owns and creates the product type; reference-data is uninvolved
- Error Input: a caller expects reference-data to expose integration modules
- Error Output: `404` — integration modules are not a reference-data resource in the target (owned by system-config)

---

## Negative finding (documented, not a rule with an endpoint)

### BR-REF-SEED-GEO (finding): Geo-zones are modeled but never populated and have no service

**Cross-Reference (Phase 1):** BR-REF-025
**Source Reference:** `GeoZone.java` : 20 (`// TODO : create DAO / Service`), 33-34 (`countries`); `Country.java` : 44-46 (`geoZone`)
**Discovery Method:** Direct Source Read

**Statement (finding):** The system models a grouping of countries into geo-zones, but that grouping is never populated: there is no seed step, no data-access layer, no service, and no reader. Consequently every country's geo-zone is empty in the legacy system. The target retains the tables (see 02-domain-model) so the feature can be built later, but ships them empty and exposes no geo-zone endpoints until the capability is genuinely implemented. **Human disposition required** (dead / future-feature / used-elsewhere) — carried into the Capability Absence Register for Phase 4a.

*(This is a NEGATIVE finding, not an implementable rule; it has no Concrete Example / preservation table because there is no legacy behavior to preserve. It is listed so the absence is explicit and traceable, per the "absence of signal → unknown, never a silent exclusion" discipline.)*
