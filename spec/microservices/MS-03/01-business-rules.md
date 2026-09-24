# MS-03 merchant-store — Business Rules

**Service:** MS-03 merchant-store · **Port:** 8003 · **Schema:** `merchant_store`
**Analysis mode:** Direct Source Read (no CAST) · **Legacy:** Shopizer 2.0.1 (Java / Spring MVC, JPA/Hibernate, QueryDSL).
**Scope:** the multi-tenant STORE record — identity/code, required config, per-store defaults, supported languages, persistence, lifecycle (create notification, decommission saga, delete/edit authorization), and branding/landing metadata (content bytes delegated to MS-11).

BR-ID scheme: `BR-MS-<GROUP>-<NNN>` where GROUP ∈ {IDENT, FIELD, DFLT, PERS, LIFE, BRAND, LAND}. Phase 1 ids (`BR-MERCH-*`) cross-referenced per rule.

---

## BR-MS-IDENT: Store identity & code

### BR-MS-IDENT-001: Store code is a unique alphanumeric-underscore business key

**Source Reference:** `MerchantStore.java:55-58`
**Cross-Reference (Phase 1):** BR-MERCH-001
**Discovery Method:** Direct Source Read

**Statement:** Every store is identified by a store code that must be present, must contain only letters, digits, and underscores, and must be unique across all stores. This code is the tenant's public business key — the storefront, file namespaces, and every downstream service resolve a store by it.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```pseudocode
code REQUIRED (non-empty)
code MUST match regex ^[a-zA-Z0-9_]*$   // @Pattern on STORE_CODE
code UNIQUE across MERCHANT_STORE        // @Column(unique=true)
reject on empty, on pattern mismatch, or on duplicate
```
**Data Dependencies:**
- Reads: merchant_store.store_code
- Writes: merchant_store.store_code

**Side Effects:**
- Unique-constraint violation on collision (surfaced as 409)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (empty / pattern / unique) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (regex `^[a-zA-Z0-9_]*$`) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (accept / reject) |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK (pattern, duplicate) |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "acme_store", "name": "Acme Retail", "phone": "+1-514-555-0100", "city": "Montreal", "postalCode": "H2X1Y4", "email": "ops@acme.example", "countryIso": "CA", "defaultLanguageCode": "en", "currencyCode": "CAD", "languageCodes": ["en","fr"]}`
- Success Output: `201 {"id": 42, "code": "acme_store", ...}`
- Error Input: `POST /api/v1/stores {"code": "acme store!", ...}`
- Error Output: `422 {"error": "ValidationError", "message": "code must match ^[a-zA-Z0-9_]*$", "statusCode": 422}`

---

### BR-MS-IDENT-002: Store-code availability is checked before creation

**Source Reference:** `MerchantStoreController.java:checkStoreCode:373-411`
**Cross-Reference (Phase 1):** BR-MERCH-002
**Discovery Method:** Direct Source Read

**Statement:** Before a store code is committed, the system reports whether the code is available. A blank code and a code already taken by an existing store are both reported as unavailable; only a non-blank, unused code is available.
**Intent:** Validation
**Weight:** Low

**Logic:**
```pseudocode
IF blank(code) THEN return UNAVAILABLE (treated as "already exists")
existing = getByCode(code)
IF existing != null THEN return UNAVAILABLE
ELSE return AVAILABLE
```
**Data Dependencies:**
- Reads: merchant_store.store_code
- Writes: (none)

**Side Effects:**
- None (read-only pre-check)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (blank / exists) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (available / unavailable) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK (blank folds into unavailable, not an error) |

**Preservation:** OK

**Concrete Example:**
- API Input: `GET /api/v1/stores/code-availability?code=new_shop`
- Success Output: `200 {"code": "new_shop", "available": true}`
- Error Input: `GET /api/v1/stores/code-availability?code=acme_store` (already exists)
- Error Output: `200 {"code": "acme_store", "available": false}`

---

### BR-MS-IDENT-003: The reserved DEFAULT store is hidden from store listings

**Source Reference:** `MerchantStore.java:40`; `MerchantStoreController.java:pageStores:113-130`
**Cross-Reference (Phase 1):** BR-MERCH-003
**Discovery Method:** Direct Source Read

**Statement:** One store, identified by the reserved code DEFAULT, is a system seed store. It is never shown in the administrative list of stores, so operators only ever see real merchant stores.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```pseudocode
stores = listAll()
FOR each store IN stores:
   IF store.code != "DEFAULT" THEN include in listing
   ELSE skip
```
**Data Dependencies:**
- Reads: merchant_store.store_code, merchant_store.store_name, merchant_store.store_email
- Writes: (none)

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (skip DEFAULT) |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK ("DEFAULT") |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (filtered list) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- API Input: `GET /api/v1/stores?page=1&pageSize=20`
- Success Output: `200 {"items": [{"code": "acme_store", ...}], "pagination": {"totalItems": 1, ...}}` (DEFAULT absent even though it exists)
- Error Input: `GET /api/v1/stores/DEFAULT`
- Error Output: `404 {"error": "NotFound", "message": "store DEFAULT is a reserved system store and is not exposed", "statusCode": 404}`

---

## BR-MS-FIELD: Required fields & location resolvability

### BR-MS-FIELD-001: A store requires a complete identity, contact, locale, and currency set

**Source Reference:** `MerchantStore.java:50-130`
**Cross-Reference (Phase 1):** BR-MERCH-004
**Discovery Method:** Direct Source Read

**Statement:** A store cannot be saved unless it has a name, a code, a phone number, a city, a postal code, a valid email address, a country, a default language, a currency, and at least one supported language. These are the minimum facts required to operate a storefront and bill in a currency.
**Intent:** Validation
**Weight:** Low

**Logic:**
```pseudocode
REQUIRE non-empty: storename, code, storephone, storecity, storepostalcode
REQUIRE storeEmailAddress non-empty AND valid email format
REQUIRE country present (COUNTRY_ID nullable=false)
REQUIRE defaultLanguage present (LANGUAGE_ID nullable=false)
REQUIRE currency present (CURRENCY_ID nullable=false)
REQUIRE languages non-empty (@NotEmpty on M2M)
any failure -> validation error, redisplay (no persistence)
```
**Data Dependencies:**
- Reads: merchant_store.store_name, .store_code, .store_phone, .store_city, .store_postal_code, .store_email, .country_iso, .default_language_code, .currency_code; merchant_language.language_code
- Writes: (none until valid)

**Side Effects:**
- Validation errors block persistence

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 10 | 10 | OK (one check per mandatory field) |
| Data-flow | 10 | 10 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (accept / reject) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (aggregated validation failure) |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "acme_store", "name": "Acme Retail", "phone": "+1-514-555-0100", "city": "Montreal", "postalCode": "H2X1Y4", "email": "ops@acme.example", "countryIso": "CA", "defaultLanguageCode": "en", "currencyCode": "CAD", "languageCodes": ["en","fr"]}`
- Success Output: `201 {"id": 42, "code": "acme_store", "currencyCode": "CAD"}`
- Error Input: `POST /api/v1/stores {"code": "acme_store", "name": "Acme Retail", "countryIso": "CA", "currencyCode": "CAD", "languageCodes": []}`
- Error Output: `422 {"error": "ValidationError", "message": "phone, city, postalCode, email, defaultLanguageCode required; at least one language required", "statusCode": 422}`

---

### BR-MS-FIELD-002: A store's state/province must be resolvable — a zone for the country or a free-text state

**Source Reference:** `MerchantStoreController.java:saveMerchantStore:264-270`
**Cross-Reference (Phase 1):** BR-MERCH-005
**Discovery Method:** Direct Source Read

**Statement:** A store must have a resolvable state or province. If the store's country has predefined administrative zones, the store selects one of them; if the country has no zones, the store must supply a free-text state/province instead. A store may not be saved with neither.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```pseudocode
zones = referenceData.getZones(country, language)
IF (zones is empty) AND blank(storestateprovince) THEN
   error "merchant.zone.invalid"
// when zones exist, the selected zone code satisfies location;
// when zones absent, the free-text state satisfies it
```
**Data Dependencies:**
- Reads: (xref MS-01) zones-by-country; merchant_store.zone_code, merchant_store.store_state_province, merchant_store.country_iso
- Writes: (none)

**Side Effects:**
- Cross-service read to MS-01 reference-data (zones for country)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (zones-empty AND blank-state) |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (accept / reject) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-01 zones lookup) |
| Error paths | 1 | 1 | OK (zone.invalid) |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "de_shop", "countryIso": "DE", "zoneCode": null, "stateProvince": "Bavaria", ...}` (DE has no zones → free-text used)
- Success Output: `201 {"id": 43, "stateProvince": "Bavaria"}`
- Error Input: `POST /api/v1/stores {"code": "de_shop", "countryIso": "DE", "zoneCode": null, "stateProvince": "", ...}`
- Error Output: `422 {"error": "ValidationError", "message": "a zone or a state/province is required for this country", "statusCode": 422}`

---

## BR-MS-DFLT: Per-store defaults

### BR-MS-DFLT-001: Measurement units default to pounds (weight) and inches (dimension)

**Source Reference:** `MerchantStore.java:83-87`; `MeasureUnit.java:3-5`
**Cross-Reference (Phase 1):** BR-MERCH-006
**Discovery Method:** Direct Source Read

**Statement:** A new store measures weight in pounds and dimensions in inches by default. An operator may switch weight to kilograms or dimension to centimetres, but only those two options per unit are offered.
**Intent:** Calculation (defaulting)
**Weight:** Medium

**Logic:**
```pseudocode
new store: weightUnit = "LB", dimensionUnit = "IN"
allowed weightUnit ∈ {LB, KG}
allowed dimensionUnit ∈ {CM, IN}
// legacy field "seizeunitcode" is a misspelling of "size"; modeled as dimensionUnit
```
**Data Dependencies:**
- Reads: merchant_store.weight_unit, merchant_store.dimension_unit
- Writes: merchant_store.weight_unit, merchant_store.dimension_unit

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK (pure defaulting) |
| Data-flow | 2 | 2 | OK |
| Constants | 4 | 4 | OK (LB, KG, CM, IN) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (reject unit outside enum) |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "acme_store", ... (no weightUnit/dimensionUnit)}`
- Success Output: `201 {"id": 42, "weightUnit": "LB", "dimensionUnit": "IN"}`
- Error Input: `PUT /api/v1/stores/acme_store {"weightUnit": "STONE"}`
- Error Output: `422 {"error": "ValidationError", "message": "weightUnit must be one of LB, KG", "statusCode": 422}`

---

### BR-MS-DFLT-002: "In business since" defaults to today and is parsed from a formatted date

**Source Reference:** `MerchantStore.java:89-96`; `MerchantStoreController.java:saveMerchantStore:225-234`, `displayMerchantStore:170-174`
**Cross-Reference (Phase 1):** BR-MERCH-007
**Discovery Method:** Direct Source Read

**Statement:** A new store's "in business since" date defaults to the day it is created. When an operator supplies a date, it must be a well-formed date; an unparseable date is rejected. When no date has been recorded, the store presents today's date.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```pseudocode
new store: inBusinessSince = today
ON save: IF dateBusinessSince provided THEN
            try parse(dateBusinessSince) -> inBusinessSince
            on parse failure -> error "message.invalid.date"
ON display: IF inBusinessSince == null THEN show today
```
**Data Dependencies:**
- Reads: merchant_store.in_business_since
- Writes: merchant_store.in_business_since

**Side Effects:**
- Validation error on unparseable date

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (provided / parse-ok / parse-fail) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (parsed / rejected) |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (invalid date) |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "acme_store", "inBusinessSince": "2019-06-01", ...}`
- Success Output: `201 {"id": 42, "inBusinessSince": "2019-06-01"}`
- Error Input: `POST /api/v1/stores {"code": "acme_store", "inBusinessSince": "31/31/2019", ...}`
- Error Output: `422 {"error": "ValidationError", "message": "inBusinessSince is not a valid date", "statusCode": 422}`

---

### BR-MS-DFLT-003: Caching and national currency formatting are off by default

**Source Reference:** `MerchantStore.java:110`, `:132-134`
**Cross-Reference (Phase 1):** BR-MERCH-008
**Discovery Method:** Direct Source Read

**Statement:** A new store has response caching disabled and formats currency in a generic (non-national) style by default. An operator can opt into either behavior explicitly.
**Intent:** Calculation (defaulting)
**Weight:** Medium

**Logic:**
```pseudocode
new store: useCache = false
new store: currencyFormatNational = false
```
**Data Dependencies:**
- Reads: merchant_store.use_cache, merchant_store.currency_format_national
- Writes: merchant_store.use_cache, merchant_store.currency_format_national

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (false, false) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "acme_store", ... (no useCache/currencyFormatNational)}`
- Success Output: `201 {"id": 42, "useCache": false, "currencyFormatNational": false}`
- Error Input: `PUT /api/v1/stores/acme_store {"useCache": "maybe"}`
- Error Output: `422 {"error": "ValidationError", "message": "useCache must be a boolean", "statusCode": 422}`

---

### BR-MS-DFLT-004: A store id is allocated from a shared sequence at creation

**Source Reference:** `MerchantStore.java:43-48`
**Cross-Reference (Phase 1):** BR-MERCH-009
**Discovery Method:** Direct Source Read

**Statement:** Each store receives a system-generated numeric identifier from a shared allocator when it is first created. The identifier is stable and is the internal handle other services use to scope tenant data.
**Intent:** State Transition (id assignment)
**Weight:** Medium

**Logic:**
```pseudocode
ON insert only: id = nextval(store sequence)  // legacy SM_SEQUENCER / STORE_SEQ_NEXT_VAL
id is immutable thereafter
```
**Data Dependencies:**
- Reads: (sequence allocator)
- Writes: merchant_store.id

**Side Effects:**
- Advances the id allocator on insert

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (insert-only) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (null id -> assigned) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK (sequence local to service DB) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "acme_store", ...}`
- Success Output: `201 {"id": 42, "code": "acme_store"}` (id assigned by allocator, not the client)
- Error Input: `POST /api/v1/stores {"id": 999, "code": "acme_store", ...}` (client attempts to set id)
- Error Output: `201 {"id": 42, "code": "acme_store"}` (client-supplied id ignored; allocator wins)

---

## BR-MS-PERS: Persistence & retrieval

### BR-MS-PERS-001: Save routes to insert or update by presence of an identifier

**Source Reference:** `MerchantStoreServiceImpl.java:saveOrUpdate:76-84`
**Cross-Reference (Phase 1):** BR-MERCH-010
**Discovery Method:** Direct Source Read

**Statement:** Saving a store creates a new store when it has no identifier yet, and updates the existing store when it already has one. There is no separate create/update mode flag — the presence of an identifier decides it.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```pseudocode
IF store.id == null THEN insert(store)
ELSE update(store)
```
**Data Dependencies:**
- Reads: merchant_store.id
- Writes: merchant_store (row insert or update)

**Side Effects:**
- INSERT or UPDATE of the store row

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (id null?) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (transient -> persistent) |
| Outcomes | 2 | 2 | OK (created / updated) |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- API Input: `PUT /api/v1/stores/acme_store {"name": "Acme Retail Group"}`
- Success Output: `200 {"id": 42, "code": "acme_store", "name": "Acme Retail Group"}` (update path)
- Error Input: `PUT /api/v1/stores/ghost_store {"name": "x"}` (no such store)
- Error Output: `404 {"error": "NotFound", "message": "store ghost_store not found", "statusCode": 404}`

---

### BR-MS-PERS-002: A store is loaded fully resolved with its locale, currency, and location

**Source Reference:** `MerchantStoreDaoImpl.java:getById:77-95`, `getMerchantStore(String):97-121`; `MerchantStoreController.java:saveMerchantStore:277-315`
**Cross-Reference (Phase 1):** BR-MERCH-011
**Discovery Method:** Direct Source Read

**Statement:** When a store is loaded for editing or storefront use, its default language, currency, country, zone, and supported languages are resolved and returned together in a single load, so callers get a complete, ready-to-use store record without follow-up lookups.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```pseudocode
load store WITH default_language (required) AND
   currency, country, zone, languages (optional)
resolved eagerly in one fetch  // legacy innerJoin(defaultLanguage).fetch + leftJoin(...).fetch
on save, reference codes are re-resolved to canonical reference-data records before persist
```
**Data Dependencies:**
- Reads: merchant_store.*, merchant_language.language_code; (xref MS-01) language/currency/country/zone by code
- Writes: (none on read)

**Side Effects:**
- Cross-service reads to MS-01 to resolve/validate codes on save

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (required vs optional joins) |
| Data-flow | 5 | 5 | OK (lang, currency, country, zone, languages) |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (fully-loaded store) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-01 code resolution) |
| Error paths | 1 | 1 | OK (unknown reference code) |

**Preservation:** OK

**Concrete Example:**
- API Input: `GET /api/v1/stores/acme_store`
- Success Output: `200 {"id": 42, "code": "acme_store", "defaultLanguageCode": "en", "currencyCode": "CAD", "countryIso": "CA", "zoneCode": "QC", "languageCodes": ["en","fr"]}`
- Error Input: `PUT /api/v1/stores/acme_store {"currencyCode": "ZZZ"}` (unknown currency)
- Error Output: `422 {"error": "ValidationError", "message": "currencyCode ZZZ is not a known currency", "statusCode": 422}`

---

### BR-MS-PERS-003: A store code resolves to exactly one store

**Source Reference:** `MerchantStoreServiceImpl.java:getMerchantStore:72-74`, `getByCode:94-97`; `MerchantStoreDaoImpl.java:getMerchantStore(String):97-121`
**Cross-Reference (Phase 1):** BR-MERCH-012
**Discovery Method:** Direct Source Read

**Statement:** Looking a store up by its code returns a single store or nothing — a code never maps to more than one store. This is the guarantee that makes the store code a safe tenant key.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```pseudocode
getByCode(code) == getMerchantStore(code) -> unique-result lookup by store_code
returns the one store, or null if none
```
**Data Dependencies:**
- Reads: merchant_store.store_code
- Writes: (none)

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (found / none) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (one store / null) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (not found) |

**Preservation:** OK

**Concrete Example:**
- API Input: `GET /api/v1/stores/acme_store`
- Success Output: `200 {"id": 42, "code": "acme_store"}`
- Error Input: `GET /api/v1/stores/nonexistent`
- Error Output: `404 {"error": "NotFound", "message": "store nonexistent not found", "statusCode": 404}`

---

## BR-MS-LIFE: Store lifecycle

### BR-MS-LIFE-001: Creating a store sends a new-store notification

**Source Reference:** `MerchantStoreController.java:saveMerchantStore:331-360`
**Cross-Reference (Phase 1):** BR-MERCH-013
**Discovery Method:** Direct Source Read

**Statement:** When a store is created (as opposed to an existing store being edited), the system sends a notification announcing the new store, addressed to the store's own contact email with an administration link. Editing an existing store sends no such notification. A failure to send the notification does not undo the store creation.
**Intent:** Integration
**Weight:** Medium

**Logic:**
```pseudocode
after saveOrUpdate:
IF savedStore.code != currentContextStore.code THEN   // treated as a "create"
   build new-store notification (admin URL + store info tokens)
   send notification to store.email  // legacy sets both from AND to to store's own email
   on send failure: log and continue (non-fatal)
```
Observation (net-new, carried from Phase 1 and confirmed in source at `:349-353`): the notification's *from* and *to* are both the store's own email address — a self-addressed email. Flagged for the 4a review as a likely defect to correct on reimplementation (notification should target the platform operator / newly-provisioned admin, not loop back to the store address).

**Data Dependencies:**
- Reads: merchant_store.store_email, merchant_store.store_name, merchant_store.store_code
- Writes: (none)

**Side Effects:**
- Publishes `store.created` (target: notification consumer) — replaces the in-process email send
- Non-fatal on delivery failure

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (create-detect, send-failure catch) |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (template name) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (sent / logged-failure) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (email/event) |
| Error paths | 1 | 1 | OK (send failure non-fatal) |

**Preservation:** OK

**Concrete Example:**
- API Input: `POST /api/v1/stores {"code": "newshop", "name": "New Shop", "email": "owner@newshop.example", ...}`
- Success Output: `201 {"id": 44, "code": "newshop"}` (and `store.created` event emitted)
- Error Input: `PUT /api/v1/stores/newshop {"name": "New Shop Renamed"}` (edit, not create)
- Error Output: `200 {"id": 44, "code": "newshop", "name": "New Shop Renamed"}` (no notification emitted)

---

### BR-MS-LIFE-002: Deleting a store decommissions all of its tenant data (orchestrated saga)

**Source Reference:** `MerchantStoreServiceImpl.java:delete:99-155`
**Cross-Reference (Phase 1):** BR-MERCH-014, roadmap R-06
**Discovery Method:** Direct Source Read

**Statement:** Deleting a store removes all data that belongs to that store — its manufacturers, store configuration, tax classes, stored files, categories and products, back-office users, customers, and orders — before the store record itself is removed. Nothing store-scoped is left orphaned.
**Intent:** State Transition (cascade delete)
**Weight:** Medium

**Logic:**
```pseudocode
reload store by id
// legacy did an in-process row-by-row cascade in this order:
//   manufacturers, merchant configurations, tax classes, CMS files,
//   categories/products, users, customers, orders, then the store
TARGET (modernized): publish merchant.deleted{merchantId, code}
   each owning service deletes its own store-scoped data on consuming the event
   store record removed after fan-out acknowledgements (decommission saga)
```
**Data Dependencies:**
- Reads: merchant_store.id, merchant_store.store_code
- Writes: merchant_store (row delete)

**Side Effects:**
- Publishes `merchant.deleted` (consumers: MS-04 catalog, MS-05 customer, MS-07 tax, MS-09 order, MS-10 payment, MS-11 content-cms, MS-08 shipping, MS-02 identity-admin)
- Cross-service cascade deletion of all store-scoped aggregates

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 8 | 8 | OK (one loop per aggregate collection) |
| Data-flow | 9 | 9 | OK (8 aggregates + store) |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (persistent -> deleted) |
| Outcomes | 1 | 1 | OK (decommissioned) |
| Data writes | 9 | 9 | OK (8 cascades via event + own row) |
| Integrations | 8 | 8 | OK (one event, 8 consumer services) |
| Error paths | 1 | 1 | OK (partial-failure / compensation) |

**Preservation:** OK — legacy in-process cascade re-expressed as an event-driven saga (R-06); the 8 delete targets are preserved as consumer responsibilities.

**Concrete Example:**
- API Input: `DELETE /api/v1/stores/acme_store` (caller is superadmin — see BR-MS-LIFE-003)
- Success Output: `202 {"status": "Decommissioning", "merchantId": 42, "event": "merchant.deleted"}` (saga started; owners purge their data)
- Error Input: `DELETE /api/v1/stores/DEFAULT`
- Error Output: `409 {"error": "Conflict", "message": "the reserved DEFAULT store cannot be deleted", "statusCode": 409}`

---

### BR-MS-LIFE-003: Only a super administrator may delete a store

**Source Reference:** `MerchantStoreController.java:removeMerchantStore:415-461`
**Cross-Reference (Phase 1):** BR-MERCH-015
**Discovery Method:** Direct Source Read

**Statement:** A store may only be deleted by a super administrator. A store administrator who lacks super-administrator standing is refused, and no data is removed. Store deletion is the highest-blast-radius operation in the platform, so it is gated to the most privileged role.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```pseudocode
require caller has store-admin authority   // legacy @PreAuthorize STORE_ADMIN
require caller is in the SUPERADMIN group   // in-body UserUtils.userInGroup check
IF not superadmin THEN reject "cannot remove — superadmin required" (no delete)
ELSE proceed to decommission (BR-MS-LIFE-002)
```
**Data Dependencies:**
- Reads: caller identity/group membership; merchant_store.id
- Writes: (none unless authorized, then delegates to BR-MS-LIFE-002)

**Side Effects:**
- Authorization gate on the decommission saga

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (role check + group check) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (SUPERADMIN group) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (proceed / refuse) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-02 token/role) |
| Error paths | 1 | 1 | OK (not superadmin) |

**Preservation:** OK

**Concrete Example:**
- API Input: `DELETE /api/v1/stores/acme_store` with a super-administrator token
- Success Output: `202 {"status": "Decommissioning", "merchantId": 42}`
- Error Input: `DELETE /api/v1/stores/acme_store` with a plain store-admin token
- Error Output: `403 {"error": "Forbidden", "message": "store deletion requires a super administrator", "statusCode": 403}`

---

### BR-MS-LIFE-004: A store administrator may only edit the store they are bound to

**Source Reference:** `MerchantStoreController.java:saveMerchantStore:219-223`
**Cross-Reference (Phase 1):** BR-MERCH-016
**Discovery Method:** Direct Source Read

**Statement:** When editing an existing store, an administrator may only save changes to the store their session is bound to; an attempt to edit a different store is refused without changing anything. This keeps one tenant's operator from mutating another tenant's store.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```pseudocode
IF submitted store has an id AND submitted.id != contextStore.id THEN
   reject (redirect, no persistence)
// legacy guard only fires when submitted.id != null; a create (no id) bypasses it
```
Observation (net-new, carried from Phase 1 and confirmed at `:219`): the guard is skipped entirely when the submitted store has no id (create path). In the modernized service, tenant binding must also be enforced on create — a store-admin should only be able to create within their own tenancy scope. Flagged for 4a as a guard-gap to close.

**Data Dependencies:**
- Reads: caller's bound store id; submitted store id
- Writes: (none when refused)

**Side Effects:**
- Refusal blocks persistence

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (id present AND id mismatch) |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (allow / refuse) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (cross-store edit refused) |

**Preservation:** OK

**Concrete Example:**
- API Input: `PUT /api/v1/stores/acme_store {"name": "Acme"}` by an admin bound to acme_store
- Success Output: `200 {"id": 42, "code": "acme_store", "name": "Acme"}`
- Error Input: `PUT /api/v1/stores/rival_store {"name": "Sabotage"}` by an admin bound to acme_store
- Error Output: `403 {"error": "Forbidden", "message": "you may only edit your own store", "statusCode": 403}`

---

## BR-MS-BRAND: Store branding metadata

### BR-MS-BRAND-001: A store records its logo by filename while the image bytes live in content storage

**Source Reference:** `StoreBrandingController.java:saveStoreBranding:88-115`, `removeImage:159-181`
**Cross-Reference (Phase 1):** BR-MERCH (branding, BR-CMS-020 boundary)
**Discovery Method:** Direct Source Read

**Statement:** A store keeps a reference to its logo as a filename on the store record; the actual image bytes are held by the content service. Uploading a logo stores the image in content storage under the store's namespace and records its filename on the store; removing the logo deletes it from content storage and clears the filename.
**Intent:** State Transition / Integration
**Weight:** Medium

**Logic:**
```pseudocode
UPLOAD: send image bytes to content-cms (namespace = store code, type = LOGO)
        set store.storeLogo = uploaded filename
        update store
REMOVE: ask content-cms to delete (store code, LOGO, current filename)
        set store.storeLogo = null
        update store
// only the filename is owned here; the bytes are MS-11's responsibility (xref)
```
**Data Dependencies:**
- Reads: merchant_store.store_code, merchant_store.store_logo
- Writes: merchant_store.store_logo

**Side Effects:**
- Cross-service call to MS-11 content-cms to store/delete logo bytes (xref)
- UPDATE of the store row (logo filename)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (upload-present / remove) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (LOGO content type) |
| State transitions | 2 | 2 | OK (set filename / clear filename) |
| Outcomes | 2 | 2 | OK (logo set / cleared) |
| Data writes | 1 | 1 | OK (store_logo) |
| Integrations | 2 | 2 | OK (put + delete in MS-11) |
| Error paths | 1 | 1 | OK (content-storage failure) |

**Preservation:** OK — image byte storage delegated to MS-11 (xref); only the filename metadata is owned here.

**Concrete Example:**
- API Input: `PUT /api/v1/stores/acme_store/logo` (multipart, file=logo.png)
- Success Output: `200 {"code": "acme_store", "storeLogo": "logo.png"}` (bytes stored in content-cms under `acme_store`)
- Error Input: `DELETE /api/v1/stores/acme_store/logo` when no logo is set
- Error Output: `404 {"error": "NotFound", "message": "no logo is set for this store", "statusCode": 404}`

---

### BR-MS-BRAND-002: A store selects a presentation template

**Source Reference:** `StoreBrandingController.java:saveTemplate:129-150`; `MerchantStoreController.java:saveMerchantStore:318`
**Cross-Reference (Phase 1):** BR-MERCH (template), BR-CMS-023
**Discovery Method:** Direct Source Read

**Statement:** A store chooses a presentation template that themes its storefront pages. The template is set only through the branding screen — the general store-edit screen never changes it — so a store's theme is not accidentally reset while other configuration is edited.
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```pseudocode
saveTemplate: set contextStore.storeTemplate = submitted template; persist
store-edit save: force store.storeTemplate = contextStore.storeTemplate  // preserved, not editable here
```
Note (source evidence at `StoreBrandingController.java:143-148`): `saveTemplate` reads the template from the submitted body but applies it to the *session/context* store, then persists that context store — the two must be the same store, reinforcing BR-MS-LIFE-004.

**Data Dependencies:**
- Reads: merchant_store.store_template
- Writes: merchant_store.store_template

**Side Effects:**
- UPDATE of the store row (template)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (template set only via branding) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (template change) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (unknown template) |

**Preservation:** OK

**Concrete Example:**
- API Input: `PUT /api/v1/stores/acme_store/template {"template": "december"}`
- Success Output: `200 {"code": "acme_store", "storeTemplate": "december"}`
- Error Input: `PUT /api/v1/stores/acme_store {"name": "Acme", "storeTemplate": "hacked"}` (attempt to change template via store edit)
- Error Output: `200 {"code": "acme_store", "storeTemplate": "december", "name": "Acme"}` (template unchanged — edit screen cannot set it)

---

## BR-MS-LAND: Landing content orchestration (store side)

### BR-MS-LAND-001: A store's landing content is created and addressed via a reserved landing section

**Source Reference:** `StoreLandingController.java:saveStoreLanding:98-200`, `displayStoreLanding:52-95`
**Cross-Reference (Phase 1):** BR-MERCH (landing orchestration), BR-CMS-009/024 (content body owned by MS-11)
**Discovery Method:** Direct Source Read

**Statement:** Each store has a single landing area identified by a reserved landing code. When an operator first edits the landing area for a store that has none, the store provisions the landing area (visible by default) and then hands its localized content over to the content service to store; the store side owns only the fact that the landing area exists and which store it belongs to.
**Intent:** State Transition / Integration
**Weight:** Medium

**Logic:**
```pseudocode
landing = content-cms.getByCode("LANDING_PAGE", store)   // xref to MS-11
IF landing == null THEN
   provision landing section {visible=true, type=SECTION, code="LANDING_PAGE", store}
delegate localized description upsert + persistence to content-cms (per-language body/title/meta)
// MS-03 orchestrates & anchors to the store; the content body/descriptions are MS-11's data
```
**Data Dependencies:**
- Reads: merchant_store.id, merchant_store.store_code, merchant_store.default_language_code; (xref MS-11) landing content by code
- Writes: (none in this service — content persisted by MS-11)

**Side Effects:**
- Cross-service call to MS-11 content-cms to provision/update the landing section and its localized bodies (xref)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (exists? / per-language upsert) |
| Data-flow | 2 | 2 | OK (store-side fields) |
| Constants | 2 | 2 | OK (LANDING_PAGE, SECTION) |
| State transitions | 1 | 1 | OK (provision landing) |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK (content owned by MS-11) |
| Integrations | 1 | 1 | OK (MS-11 content call) |
| Error paths | 1 | 1 | OK (content service unavailable) |

**Preservation:** OK — content body/descriptions are MS-11 (xref); only the store-side orchestration and store anchoring are owned here.

**Concrete Example:**
- API Input: `PUT /api/v1/stores/acme_store/landing {"descriptions": [{"languageCode": "en", "title": "Welcome", "homePageContent": "<h1>Welcome to Acme</h1>"}]}`
- Success Output: `200 {"code": "acme_store", "landingCode": "LANDING_PAGE", "provisioned": true}` (content persisted by content-cms)
- Error Input: `PUT /api/v1/stores/ghost_store/landing {...}` (no such store)
- Error Output: `404 {"error": "NotFound", "message": "store ghost_store not found", "statusCode": 404}`
