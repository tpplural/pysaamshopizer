# MS-07 (tax) — Business Rules

**Version**: 1.0
**Date**: 2026-02-14
**Status**: 🟢 100% COMPLETE
**Service ID**: MS-07
**Analysis mode**: Direct Source Read (no CAST)
**Rule group**: `BR-TAX` (single group) — BR-TAX-001 … BR-TAX-028 (28 rules, contiguous)

> **Preservation decision D-06 (applies to BR-TAX-007, BR-TAX-019, BR-TAX-003, BR-TAX-023):** These four rules
> capture behavior of the legacy engine that is either dead code or a latent defect. Per D-06 the
> modernized service PRESERVES the current behavior EXACTLY and FLAGS it — it does NOT silently correct
> it. Each carries `Preservation: FLAGGED` and a `[D-06 PRESERVED-AS-IS]` note carried to Phase 4a for a
> BA decision. The single most important is **BR-TAX-007**: the tax-basis comparison is always false, so
> the shipping/billing/store basis-override branches are dead code and tax is ALWAYS computed on the
> seeded billing address, regardless of configured basis.

> **Statement discipline:** Statements use business-domain terms only (no legacy table/column/method
> names). Legacy mechanics live in the Logic and Source Reference fields for traceability.

---

### BR-TAX-001: Tax configuration is per-store, stored as a JSON document

**Source Reference:** `TaxServiceImpl.java:getTaxConfiguration:61-77`; `TaxServiceImpl.java:saveTaxConfiguration:81-94`; `TaxConfigurationController.java:saveTaxConfiguration:54-66`
**Discovery Method:** Direct Source Read
**Statement:** Each store owns exactly one tax configuration that controls how tax is calculated. It is retrieved and saved per store; when a store has never saved a configuration, none exists yet.
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
cfg = merchantConfiguration.get(key="TAX_CONFIG", store)
if cfg != null: taxConfiguration = deserializeJson(cfg.value -> TaxConfiguration)
               else null
save: value = taxConfiguration.toJSONString(); upsert merchantConfiguration(key="TAX_CONFIG", store, value)
```
**Data Dependencies:**
- Reads: tax_configuration (store-scoped JSON document; legacy `MERCHANT_CONFIGURATION` key `TAX_CONFIG`)
- Writes: tax_configuration (upsert on save)
**Side Effects:** Save creates or updates the store's tax configuration document.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (config key TAX_CONFIG) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (found / absent) |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (JSON serialization) |
| Error paths | 1 | 1 | OK (parse failure) |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/tax/configuration` (header `x-store-id: STORE-1`)
- Success: `200 {"taxBasisCalculation": "SHIPPINGADDRESS", "collectTaxIfDifferentProvinceOfStoreCountry": true, "collectTaxIfDifferentCountryOfStoreCountry": false}`
- Error Input: `PUT /api/v1/tax/configuration {"taxBasisCalculation": "MOON"}`
- Error Output: `422 {"error": "ValidationError", "message": "taxBasisCalculation must be one of StoreAddress, ShippingAddress, BillingAddress"}`

---

### BR-TAX-002: Absent tax configuration defaults tax basis to the shipping address

**Source Reference:** `TaxServiceImpl.java:calculateTax:116-120`; `TaxConfiguration.java:13`
**Discovery Method:** Direct Source Read
**Statement:** When a store has no saved tax configuration, tax is calculated using the shipping-address basis by default.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
if taxConfiguration == null:
    taxConfiguration = new TaxConfiguration()   // field default basis = SHIPPINGADDRESS
    taxConfiguration.taxBasisCalculation = SHIPPINGADDRESS
```
**Data Dependencies:**
- Reads: in-memory tax configuration (defaulted)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (SHIPPINGADDRESS default) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate` for a store with no saved configuration
- Success: `200` — calculation proceeds with basis `ShippingAddress` (subject to BR-TAX-007)
- Error Input: (n/a — defaulting cannot be triggered to fail; absence always yields the default)
- Error Output: (n/a)

---

### BR-TAX-003: Only the tax basis is persisted; collection-scope flags are not serialized

**Source Reference:** `TaxConfiguration.java:toJSONString:20-27`; `TaxConfiguration.java:15-16`; `TaxServiceImpl.java:saveTaxConfiguration:90-92`
**Discovery Method:** Direct Source Read
**Statement:** When a store's tax configuration is saved, only the tax basis is stored. The two collection-scope preferences (whether to collect tax across provinces of the store's country, and whether to collect across countries) are not stored, so after a reload they always revert to their built-in defaults (collect-across-provinces on, collect-across-countries off) regardless of what was chosen.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
toJSONString():
    data = { "taxBasisCalculation": basis.name() }   // ONLY the basis
    // collectTaxIfDifferentProvinceOfStoreCountry NOT written
    // collectTaxIfDifferentCountryOfStoreCountry   NOT written
    return json(data)
// on reload, the two flags are not present -> revert to field defaults (true / false)
```
**Data Dependencies:**
- Reads: tax_configuration fields
- Writes: tax_configuration (basis only)
**Side Effects:** Persisted document silently omits the two collection flags.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 3 | 3 | OK (3 config fields; 2 dropped on write) |
| Constants | 2 | 2 | OK (default true / false) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (JSON) |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED — **[D-06 PRESERVED-AS-IS]** The collection-scope flags are not persisted; they revert to defaults on every reload. Preserve this behavior exactly; do NOT start persisting the flags. Carry to Phase 4a: "Should the modernized config persist the two collection flags? (BA decision.)"
**Concrete Example:**
- Input: `PUT /api/v1/tax/configuration {"taxBasisCalculation": "BillingAddress", "collectTaxIfDifferentCountryOfStoreCountry": true}` then `GET /api/v1/tax/configuration`
- Success: `200 {"taxBasisCalculation": "BillingAddress", "collectTaxIfDifferentProvinceOfStoreCountry": true, "collectTaxIfDifferentCountryOfStoreCountry": false}` — the saved `collectTaxIfDifferentCountryOfStoreCountry=true` was NOT persisted and reverted to `false` (preserved defect)
- Error Input: `PUT /api/v1/tax/configuration {}` (missing basis)
- Error Output: `422 {"error": "ValidationError", "message": "taxBasisCalculation is required"}`

---

### BR-TAX-004: Shipping-address basis resolves to the customer delivery address

**Source Reference:** `TaxServiceImpl.java:calculateTax:122-132`
**Discovery Method:** Direct Source Read
**Statement:** When the configured tax basis is the shipping address and the customer has a delivery address, tax jurisdiction (country, zone, state/province) is taken from the delivery address. (Note: the branch that applies this is unreachable at runtime — see BR-TAX-007.)
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
country/zone/stateProvince = customer.billing.*     // seed
if basis == SHIPPINGADDRESS and customer.delivery != null:
    country = delivery.country; zone = delivery.zone; stateProvince = delivery.state
```
**Data Dependencies:**
- Reads: customer delivery address (external — order context), customer billing address
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK (country/zone/state) |
| Constants | 1 | 1 | OK (SHIPPINGADDRESS) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (customer/order context) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK (branch semantics captured; reachability defect tracked in BR-TAX-007)
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"taxBasis": "ShippingAddress", "customer": {"delivery": {"countryId": 124, "zoneId": 40}, "billing": {"countryId": 840}}, "items": [...]}`
- Success: `200` — jurisdiction intended to resolve to delivery (country 124); in preserved behavior it stays on billing (country 840) per BR-TAX-007
- Error Input: `POST /api/v1/tax/calculate {"taxBasis": "ShippingAddress", "customer": null, "items": [...]}`
- Error Output: `200 null` (no tax — null customer, BR-TAX-024)

---

### BR-TAX-005: Billing-address basis resolves to the customer billing address

**Source Reference:** `TaxServiceImpl.java:calculateTax:133-139`
**Discovery Method:** Direct Source Read
**Statement:** When the configured tax basis is the billing address and the customer has a billing address, tax jurisdiction is taken from the billing address. (Note: the branch that applies this is unreachable at runtime — see BR-TAX-007 — but the seeded jurisdiction is already the billing address, so billing-based taxation is what actually occurs.)
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
if basis == BILLINGADDRESS and customer.billing != null:
    country = billing.country; zone = billing.zone; stateProvince = billing.state
```
**Data Dependencies:**
- Reads: customer billing address (external — order context)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (BILLINGADDRESS) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"taxBasis": "BillingAddress", "customer": {"billing": {"countryId": 840, "zoneId": 60}}, "items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}]}`
- Success: `200 {"taxLines": [{"label": "State Tax", "rate": 5.0, "amount": 5.00, "code": "STATE"}]}`
- Error Input: `POST /api/v1/tax/calculate {"taxBasis": "BillingAddress", "customer": {"billing": {"countryId": 840}}, "items": []}` (empty items but non-null list)
- Error Output: `200 null` (no applicable tax lines, BR-TAX-024)

---

### BR-TAX-006: Store-address basis resolves to the merchant store address

**Source Reference:** `TaxServiceImpl.java:calculateTax:140-146`
**Discovery Method:** Direct Source Read
**Statement:** When the configured tax basis is the store address, tax jurisdiction is taken from the merchant store's own country, zone, and state/province. (Note: the branch that applies this is unreachable at runtime — see BR-TAX-007.)
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
if basis == STOREADDRESS:
    country = store.country; zone = store.zone; stateProvince = store.storeStateProvince
```
**Data Dependencies:**
- Reads: merchant store address (external — MS-01/MS-03 reference/store data)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (STOREADDRESS) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (store data) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"taxBasis": "StoreAddress", "store": {"countryId": 124, "zoneId": 40}, "customer": {"billing": {"countryId": 840}}, "items": [...]}`
- Success: `200` — jurisdiction intended to resolve to store (country 124); preserved behavior stays on billing (country 840) per BR-TAX-007
- Error Input: `POST /api/v1/tax/calculate {"taxBasis": "StoreAddress", "customer": null}`
- Error Output: `200 null` (null customer, BR-TAX-024)

---

### BR-TAX-007: Tax-basis selection is never applied — jurisdiction is always the billing address

**Source Reference:** `TaxServiceImpl.java:calculateTax:126,133,140`; `TaxBasisCalculation.java:1-8`
**Discovery Method:** Direct Source Read
**Statement:** The configured tax basis is compared incorrectly, so none of the basis-override branches ever take effect. As a result, tax jurisdiction is always determined from the customer's billing address, regardless of whether the store configured shipping-address, billing-address, or store-address basis.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
// seed: country/zone/stateProvince = customer.billing.*   (:122-124)
if taxBasisCalculation.name().equals(SHIPPINGADDRESS_ENUM): ...   // String.equals(Enum) -> ALWAYS false
else if taxBasisCalculation.name().equals(BILLINGADDRESS_ENUM): ... // ALWAYS false
else if taxBasisCalculation.name().equals(STOREADDRESS_ENUM): ...   // ALWAYS false
// net: no branch executes -> jurisdiction stays at the seeded billing address for every order
```
**Data Dependencies:**
- Reads: customer billing address (external — order context)
- Writes: none
**Side Effects:** None. Behavioral impact: configured basis has no effect; billing address is always used.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (three always-false branches preserved) |
| Data-flow | 3 | 3 | OK (seed billing country/zone/state) |
| Constants | 3 | 3 | OK (3 enum constants) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (always billing) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED — **[D-06 PRESERVED-AS-IS]** The always-false basis comparison is preserved exactly: the modernized engine MUST use the billing address for jurisdiction regardless of configured basis, and the shipping/billing/store override branches remain effectively dead. Do NOT "fix" this to honor the configured basis. Carry to Phase 4a: "Known latent bug preserved as-is; modernized system may later honor configured basis — BA decision (high business impact)."
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"taxBasis": "ShippingAddress", "customer": {"billing": {"countryId": 840, "zoneId": 60}, "delivery": {"countryId": 124, "zoneId": 40}}, "items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}]}`
- Success: `200` — despite `ShippingAddress` basis and a different delivery country, tax is computed on the BILLING jurisdiction (country 840, zone 60). Preserved behavior.
- Error Input: `POST /api/v1/tax/calculate {"taxBasis": "ShippingAddress", "customer": {"billing": null}, "items": [...]}`
- Error Output: `200 null` or downstream jurisdiction-empty → no tax (BR-TAX-024); a missing billing jurisdiction yields no rate match

---

### BR-TAX-008: Do not collect tax across provinces of the store's country when the province flag is off

**Source Reference:** `TaxServiceImpl.java:calculateTax:148-166`
**Discovery Method:** Direct Source Read
**Statement:** When the store is configured NOT to collect tax across provinces of its own country, an order whose jurisdiction is in a different province than the store's is not taxed at all. If the buyer's zone differs from the store's zone, or the buyer's state/province name does not match the store's zone/state, tax calculation is aborted and no tax lines are produced.
**Intent:** Validation
**Weight:** Critical
**Logic:**
```
if not collectTaxIfDifferentProvinceOfStoreCountry:
    if zone != null and store.zone != null and zone.id != store.zone.id: return null
    if stateProvince not blank:
        if store.zone != null and store.zone.name != stateProvince: return null
        else if store.storeStateProvince not blank and store.storeStateProvince != stateProvince: return null
```
**Data Dependencies:**
- Reads: resolved jurisdiction zone/state, store zone, store state/province (external store data)
- Writes: none
**Side Effects:** Returning null aborts the entire calculation (no tax lines).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (taxed / aborted) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (store data) |
| Error paths | 1 | 1 | OK (abort → null) |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"collectTaxIfDifferentProvinceOfStoreCountry": false, "store": {"zoneId": 40}, "customer": {"billing": {"zoneId": 41}}, "items": [...]}`
- Success: `200 null` — buyer zone 41 differs from store zone 40, collection off → no tax
- Error Input: same but `"customer": {"billing": {"zoneId": 40}}`
- Error Output: `200 {"taxLines": [...]}` — same zone, tax is collected (not an error; contrast case)

---

### BR-TAX-009: Collecting tax across countries forces the store address as the jurisdiction

**Source Reference:** `TaxServiceImpl.java:calculateTax:168-172`
**Discovery Method:** Direct Source Read
**Statement:** When the store is configured to collect tax across countries, the tax jurisdiction is overridden to the store's own country, zone, and state/province, superseding any previously resolved jurisdiction.
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
if collectTaxIfDifferentCountryOfStoreCountry:
    country = store.country; zone = store.zone; stateProvince = store.storeStateProvince
```
**Data Dependencies:**
- Reads: store address (external store data)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"collectTaxIfDifferentCountryOfStoreCountry": true, "store": {"countryId": 124, "zoneId": 40}, "customer": {"billing": {"countryId": 840}}, "items": [...]}`
- Success: `200` — jurisdiction overridden to store country 124 / zone 40
- Error Input: `POST /api/v1/tax/calculate {"collectTaxIfDifferentCountryOfStoreCountry": true, "store": null, ...}`
- Error Output: `422 {"error": "ValidationError", "message": "store is required for tax calculation"}`

---

### BR-TAX-010: Default collection scope collects within province, not across countries

**Source Reference:** `TaxConfiguration.java:15-16`; `TaxServiceImpl.java:calculateTax:148,168`
**Discovery Method:** Direct Source Read
**Statement:** By default a store collects tax across provinces of its own country (province collection on) and does not collect tax across countries (cross-country collection off). Because these two preferences are never persisted (see BR-TAX-003), these defaults are the values actually used at calculation time for every order.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
collectTaxIfDifferentProvinceOfStoreCountry = true   // default
collectTaxIfDifferentCountryOfStoreCountry   = false  // default
// combined with BR-TAX-003, these are the effective runtime values (flags never deserialized)
```
**Data Dependencies:**
- Reads: tax configuration defaults
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (true / false) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate` with no explicit collection flags supplied
- Success: `200` — province collection treated as on, cross-country as off (defaults applied)
- Error Input: `POST /api/v1/tax/calculate {"collectTaxIfDifferentProvinceOfStoreCountry": "maybe"}`
- Error Output: `422 {"error": "ValidationError", "message": "collectTaxIfDifferentProvinceOfStoreCountry must be a boolean"}`

---

### BR-TAX-011: Cart items are grouped into taxable subtotals by product tax class

**Source Reference:** `TaxServiceImpl.java:calculateTax:178-197`
**Discovery Method:** Direct Source Read
**Statement:** Items in an order are grouped by their product's tax class, and for each tax class a taxable subtotal is accumulated as the sum of item unit price times quantity. Item prices are tax-exclusive, so each subtotal is the pre-tax taxable base for that class.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
taxClassAmountMap: Map<taxClassId, subtotal>
for each item:
    lineTotal = item.unitPrice * item.quantity
    taxClass  = item.product.taxClass (if null -> DEFAULT, see BR-TAX-012)
    taxClassAmountMap[taxClass.id] += lineTotal
```
**Data Dependencies:**
- Reads: order item unit price/quantity, product tax class (external — MS-04 catalog read), tax_class
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (loop + null-class branch) |
| Data-flow | 3 | 3 | OK (price, quantity, taxClass) |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (catalog read) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 50.00, "quantity": 2, "taxClassCode": "DEFAULT"}, {"unitPrice": 30.00, "quantity": 1, "taxClassCode": "REDUCED"}]}`
- Success: `200` — DEFAULT taxable base = 100.00, REDUCED taxable base = 30.00
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": -5.00, "quantity": 1, "taxClassCode": "DEFAULT"}]}`
- Error Output: `422 {"error": "ValidationError", "message": "item unitPrice must be non-negative"}`

---

### BR-TAX-012: Items with no product tax class fall back to the DEFAULT tax class

**Source Reference:** `TaxServiceImpl.java:calculateTax:185-187`; `TaxClassDaoImpl.java:getByCode:42-52`; `TaxClass.java:33`
**Discovery Method:** Direct Source Read
**Statement:** When an item's product has no assigned tax class, it is taxed under the store's DEFAULT tax class. The DEFAULT tax class is a reserved, always-present class used as the fallback.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
if item.product.taxClass == null:
    taxClass = taxClassService.getByCode("DEFAULT")   // store-agnostic lookup (see BR-TAX-024 note)
```
**Data Dependencies:**
- Reads: product tax class (external — MS-04), tax_class where code = 'DEFAULT'
- Writes: none
**Side Effects:** None. Runtime precondition: a DEFAULT tax class must exist (its absence is a fatal error).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK ("DEFAULT") |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (catalog + tax_class) |
| Error paths | 1 | 1 | OK (missing DEFAULT → error) |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 20.00, "quantity": 1, "taxClassCode": null}]}`
- Success: `200` — the item is bucketed under DEFAULT and taxed at DEFAULT-class rates
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 20.00, "quantity": 1, "taxClassCode": null}]}` when no DEFAULT tax class is configured for the store
- Error Output: `409 {"error": "ConfigurationError", "message": "DEFAULT tax class is not configured"}`

---

### BR-TAX-013: Intermediate scaling of accumulators is a no-op; only per-line rounding applies

**Source Reference:** `TaxServiceImpl.java:calculateTax:189-192,210-212,243-244`
**Discovery Method:** Direct Source Read
**Statement:** The intermediate step that would round the running taxable-subtotal accumulators to two decimal places has no effect, because the scaling result is discarded. Rounding of tax amounts therefore happens only per emitted tax line (see BR-TAX-022), not on the intermediate accumulators.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
subTotal = 0
subTotal.setScale(2, HALF_UP)   // result discarded (immutable value) -> scale stays 0
// same pattern on the shipping bucket and the totalTaxedItemValue accumulator
// net: accumulators are not scaled; final per-line rounding still occurs (BR-TAX-022)
```
**Data Dependencies:**
- Reads: in-memory accumulators
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (scale 2) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK (behavior: no intermediate scaling; per-line rounding is authoritative — preserve exactly)
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 33.333, "quantity": 3, "taxClassCode": "DEFAULT"}]}` (subtotal 99.999, not intermediate-rounded)
- Success: `200` — the taxable base is not pre-rounded; each emitted tax line is rounded to 2dp
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": "abc", "quantity": 1}]}`
- Error Output: `422 {"error": "ValidationError", "message": "item unitPrice must be a number"}`

---

### BR-TAX-014: Shipping and handling are always added to the DEFAULT tax-class taxable base

**Source Reference:** `TaxServiceImpl.java:calculateTax:199-222`
**Discovery Method:** Direct Source Read
**Statement:** Shipping and handling charges are always taxed and are added into the DEFAULT tax class's taxable base. When shipping is greater than zero it is added, and when handling is greater than zero it is added as well. There is no configurable "tax on shipping" toggle — shipping is taxed unconditionally.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
defaultTaxClass = getByCode("DEFAULT")
amnt = taxClassAmountMap[defaultTaxClass.id] (null -> 0)
// legacy "if shippingConfiguration.isTaxOnShipping()" guard is commented out -> always tax shipping
if shippingSummary != null and shippingSummary.shipping > 0:
    amnt += shippingSummary.shipping
    if shippingSummary.handling != null and shippingSummary.handling > 0:
        amnt += shippingSummary.handling
taxClassAmountMap[defaultTaxClass.id] = amnt
```
**Data Dependencies:**
- Reads: shipping + handling amounts (external — order/shipping context), tax_class 'DEFAULT'
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK (default class, shipping, handling) |
| Constants | 1 | 1 | OK ("DEFAULT") |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (shipping context) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK — note: the legacy `applyTaxOnShipping` shipping-config flag is intentionally ignored (guard commented out); shipping is taxed unconditionally under DEFAULT. Preserve as-is (carried as a Phase 4a confirm item, not a D-06 defect).
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}], "shipping": {"shipping": 10.00, "handling": 2.00}}`
- Success: `200` — DEFAULT taxable base = 112.00 (100 + 10 + 2), taxed at DEFAULT-class rates
- Error Input: `POST /api/v1/tax/calculate {"items": [...], "shipping": {"shipping": -10.00}}`
- Error Output: `422 {"error": "ValidationError", "message": "shipping amount must be non-negative"}`

---

### BR-TAX-015: Shipping is taxed at the DEFAULT tax class's rates only

**Source Reference:** `TaxServiceImpl.java:calculateTax:207-221,229-237`
**Discovery Method:** Direct Source Read
**Statement:** Because shipping and handling are folded into the DEFAULT tax class's taxable base, they are taxed at exactly the rates configured for the DEFAULT tax class. If the DEFAULT class has no rate matching the buyer's jurisdiction, shipping is not taxed.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
// shipping+handling live in the DEFAULT-class bucket (BR-TAX-014)
// rate lookup runs per tax class (BR-TAX-016); the DEFAULT bucket is matched
// against DEFAULT-class rates for the jurisdiction -> shipping tax = DEFAULT-class rates
```
**Data Dependencies:**
- Reads: tax_rate for the DEFAULT tax class + jurisdiction, tax_class 'DEFAULT'
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK ("DEFAULT") |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (taxed / untaxed if no rate) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}], "shipping": {"shipping": 10.00}}` where DEFAULT class has a 5% state rate
- Success: `200 {"taxLines": [{"label": "State Tax", "rate": 5.0, "amount": 5.50, "code": "STATE"}]}` (5% of 110.00)
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}], "shipping": {"shipping": 10.00}}` where DEFAULT class has NO rate for the jurisdiction
- Error Output: `200 null` — no matching rate, shipping untaxed (BR-TAX-024)

---

### BR-TAX-016: Rate lookup selects the zone-based or state-based path

**Source Reference:** `TaxServiceImpl.java:calculateTax:229-237`; `TaxRateServiceImpl.java:listByCountryZoneAndTaxClass:50-52`; `TaxRateServiceImpl.java:listByCountryStateProvinceAndTaxClass:55-57`
**Discovery Method:** Direct Source Read
**Statement:** For each tax class, applicable tax rates are looked up for the buyer's jurisdiction. When the jurisdiction has a free-text state/province but no structured zone, rates are matched by country + state/province; otherwise rates are matched by country + zone. Structured zone takes precedence over free-text state.
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
for each taxClassId in taxClassAmountMap:
    if stateProvince not blank and zone == null:
        taxRates = listByCountryStateProvinceAndTaxClass(country, stateProvince, taxClass, store, language)
    else:
        taxRates = listByCountryZoneAndTaxClass(country, zone, taxClass, store, language)
```
**Data Dependencies:**
- Reads: tax_rate, tax_rate_description; jurisdiction country/zone/state (external), store, language (external MS-01)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (loop + 2 branch) |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (zone path / state path) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (reference data) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"customer": {"billing": {"countryId": 840, "zoneId": null, "state": "Texas"}}, "items": [...]}`
- Success: `200` — state-based path used (zone null, state present)
- Error Input: `POST /api/v1/tax/calculate {"customer": {"billing": {"countryId": null}}, "items": [...]}`
- Error Output: `422 {"error": "ValidationError", "message": "billing country is required for tax calculation"}`

---

### BR-TAX-017: Zone-based rates are matched by store, country, and zone, ordered by priority ascending

**Source Reference:** `TaxRateDaoImpl.java:listByCountryZoneAndTaxClass:126-152`
**Discovery Method:** Direct Source Read
**Statement:** Zone-based tax rates are selected for the store, filtered to the matching country and zone, restricted to the requested language for their descriptions, and returned ordered by tax priority ascending. Priority order determines the sequence in which rates are applied (relevant to compound stacking).
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
select taxRate
where taxRate.store = store
  and taxRate.zone = zone            // (subject to the zone predicate quirk, BR-TAX-019)
  and taxRate.country = country
  and taxRate.description.language = language
order by taxRate.taxPriority asc
```
**Data Dependencies:**
- Reads: tax_rate (merchant_id, country_id, zone_id, tax_priority), tax_rate_description (language_id)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (ordered list) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"customer": {"billing": {"countryId": 124, "zoneId": 40}}, "items": [...], "languageId": 1}`
- Success: `200 {"taxLines": [{"label": "GST", "rate": 5.0, "amount": 5.00}, {"label": "PST", "rate": 8.0, "amount": 8.00}]}` (priority-ordered)
- Error Input: `POST /api/v1/tax/calculate {"customer": {"billing": {"countryId": 124, "zoneId": 40}}, "items": [...], "languageId": 9999}`
- Error Output: `200 null` — no descriptions in that language → no matching rates (BR-TAX-024)

---

### BR-TAX-018: State/province rates are matched by exact state string, without a zone

**Source Reference:** `TaxRateDaoImpl.java:listByCountryStateProvinceAndTaxClass:156-181`
**Discovery Method:** Direct Source Read
**Statement:** State/province-based tax rates are selected for the store, filtered to the matching country and an exact state/province string match, restricted to the requested description language, and returned ordered by tax priority ascending.
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
select taxRate
where taxRate.store = store
  and taxRate.stateProvince = stateProvince   // exact string equality
  and taxRate.country = country
  and taxRate.description.language = language
order by taxRate.taxPriority asc
```
**Data Dependencies:**
- Reads: tax_rate (merchant_id, country_id, store_state_prov, tax_priority), tax_rate_description (language_id)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"customer": {"billing": {"countryId": 840, "zoneId": null, "state": "California"}}, "items": [...]}`
- Success: `200 {"taxLines": [{"label": "CA Sales Tax", "rate": 7.25, "amount": 7.25}]}`
- Error Input: same with `"state": "californa"` (typo, no exact match)
- Error Output: `200 null` — no exact state match → no tax (BR-TAX-024)

---

### BR-TAX-019: The tax-class argument does not filter the rate query — every store rate applies to every class

**Source Reference:** `TaxRateDaoImpl.java:listByCountryZoneAndTaxClass:126-152`; `TaxRateDaoImpl.java:listByCountryStateProvinceAndTaxClass:156-181`
**Discovery Method:** Direct Source Read
**Statement:** Although rate lookup is invoked per tax class, the tax class is not actually used to filter which rates are returned. Every rate configured for the store and jurisdiction is applied to every tax-class taxable bucket. A product's tax class therefore does not restrict which rates hit its items.
**Intent:** Routing
**Weight:** Critical
**Logic:**
```
listByCountryZoneAndTaxClass(country, zone, taxClass, store, language):
    // taxClass parameter is accepted but NEVER referenced in the where-clause
    where store = store and country = country and <zone predicate> and language = language
    // no predicate on taxRate.taxClass -> rates not scoped by class
// same in the state/province variant
```
**Data Dependencies:**
- Reads: tax_rate, tax_rate_description
- Writes: none
**Side Effects:** None. Behavioral impact: per-tax-class rate isolation intended by BR-TAX-011/012 is not enforced at the query layer.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (unused-arg branch preserved) |
| Data-flow | 4 | 4 | OK (taxClass arg present-but-unused) |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (all rates apply) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED — **[D-06 PRESERVED-AS-IS]** The tax-class argument is accepted but not applied; every store+jurisdiction rate applies to every class bucket. Preserve this behavior exactly; do NOT add a tax-class filter. Carry to Phase 4a: "Intended (all rates apply globally) or a defect (rates should be scoped to the product's tax class)? — BA decision."
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "REDUCED"}]}` where the store has one rate (5% STATE) configured against the DEFAULT class only
- Success: `200 {"taxLines": [{"label": "State Tax", "rate": 5.0, "amount": 5.00, "code": "STATE"}]}` — the DEFAULT-class rate still applies to the REDUCED bucket (preserved behavior)
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "UNKNOWN"}]}`
- Error Output: `422 {"error": "ValidationError", "message": "unknown taxClassCode: UNKNOWN"}`

---

### BR-TAX-020: Each tax rate applies its percentage to the taxable base for its class

**Source Reference:** `TaxServiceImpl.java:calculateTax:243-268`; `TaxItem.java:1-32`
**Discovery Method:** Direct Source Read
**Statement:** For each tax class bucket, every matched rate is applied as a percentage of the taxable base to produce a tax amount. For non-compound rates the base is the original pre-tax subtotal, so multiple non-compound rates in the same class each apply to the same pre-tax base (combined taxing). Each rate produces one tax line labelled with the rate's description.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
beforeTaxeAmount   = taxClassAmountMap[taxClassId]     // pre-tax taxable base
totalTaxedItemValue = 0
for each taxRate in rates (priority asc):
    rate = taxRate.taxRate            // percent, e.g. 5.0000
    if taxRate.piggyback and totalTaxedItemValue > 0:   // compound (BR-TAX-021)
        beforeTaxeAmount = totalTaxedItemValue
    value        = (beforeTaxeAmount * rate) / 100
    roundedValue = round(value, 2, HALF_UP)             // BR-TAX-022
    totalTaxedItemValue = beforeTaxeAmount + roundedValue
    emit TaxItem{ amount = roundedValue, label = rate.description.name, taxRate = taxRate }
```
**Data Dependencies:**
- Reads: tax_rate (tax_rate, piggyback, tax_priority), tax_rate_description (name)
- Writes: none (produces transient tax lines)
**Side Effects:** Produces transient tax-line results returned to the caller (order service, MS-09).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (loop + piggyback branch + running total) |
| Data-flow | 3 | 3 | OK (base, rate, description) |
| Constants | 1 | 1 | OK (÷100) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (tax line per rate) |
| Data writes | 1 | 1 | OK (emit tax line) |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}]}` where DEFAULT has rate STATE 5% (non-piggyback) and rate CITY 2% (non-piggyback)
- Success: `200 {"taxLines": [{"code": "STATE", "rate": 5.0, "amount": 5.00}, {"code": "CITY", "rate": 2.0, "amount": 2.00}]}` — both applied to the 100.00 base
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 0, "taxClassCode": "DEFAULT"}]}`
- Error Output: `422 {"error": "ValidationError", "message": "item quantity must be at least 1"}`

---

### BR-TAX-021: Piggyback (compound) tax stacks on top of the running taxed total

**Source Reference:** `TaxServiceImpl.java:calculateTax:251-260`
**Discovery Method:** Direct Source Read
**Statement:** A rate marked as piggyback is a tax-on-tax: when there is already an accumulated taxed total for the class, the piggyback rate applies to the running total (base plus previously accumulated tax) rather than to the original pre-tax subtotal. Because rates are applied in ascending priority order, a piggyback rate must be ordered after the base rate it stacks on.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
if taxRate.piggyback:
    if totalTaxedItemValue > 0:
        beforeTaxeAmount = totalTaxedItemValue      // base = subtotal + accumulated tax
compoundTax = round(beforeTaxeAmount * rate / 100, 2, HALF_UP)
totalTaxedItemValue = beforeTaxeAmount + compoundTax
// worked: subtotal 100; A=5% (non-piggyback) -> tax 5.00, running 105.00;
//         B=8% (piggyback) -> base 105.00 -> tax 8.40, running 113.40; total tax = 13.40
```
**Data Dependencies:**
- Reads: tax_rate (piggyback, tax_priority, tax_rate)
- Writes: none
**Side Effects:** None (transient lines).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (÷100) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (compound tax line) |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}]}` where DEFAULT has GST 5% (priority 1, non-piggyback) and QST 8% (priority 2, piggyback)
- Success: `200 {"taxLines": [{"code": "GST", "rate": 5.0, "amount": 5.00}, {"code": "QST", "rate": 8.0, "amount": 8.40}]}` — QST computed on 105.00
- Error Input: `POST /api/v1/tax/calculate {"items": [...]}` with a piggyback rate but no preceding base rate (running total 0)
- Error Output: `200 {"taxLines": [{"code": "QST", "rate": 8.0, "amount": 8.00}]}` — piggyback with zero running total falls back to the pre-tax base (not an error; contrast case)

---

### BR-TAX-022: Each emitted tax line is rounded to two decimal places, half-up

**Source Reference:** `TaxServiceImpl.java:calculateTax:257-259`
**Discovery Method:** Direct Source Read
**Statement:** Each rate's computed tax amount is rounded to two decimal places using half-up rounding before it becomes a tax line. Rounding is applied per line, not on the aggregated total.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
value        = (beforeTaxeAmount * rate) / 100        // computed in double
roundedValue = round(value, 2, HALF_UP)
taxLineAmount = roundedValue (scale 2, HALF_UP)
```
**Data Dependencies:**
- Reads: computed tax value
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (scale 2, HALF_UP) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK — note: legacy computes the percentage in primitive double then rounds per line; preserve half-up 2dp per-line rounding (aggregate is the sum of already-rounded lines).
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 19.99, "quantity": 1, "taxClassCode": "DEFAULT"}]}` where DEFAULT has a 7.25% rate → 19.99 × 7.25 / 100 = 1.449275
- Success: `200 {"taxLines": [{"rate": 7.25, "amount": 1.45}]}` (rounded half-up to 2dp)
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 19.99, "quantity": 1, "taxClassCode": "DEFAULT"}], "roundingMode": "CEILING"}`
- Error Output: `422 {"error": "ValidationError", "message": "roundingMode is not configurable; engine uses HALF_UP"}`

---

### BR-TAX-023: Tax lines are consolidated by rate code, keeping the first line per code

**Source Reference:** `TaxServiceImpl.java:calculateTax:274-297`
**Discovery Method:** Direct Source Read
**Statement:** Emitted tax lines are consolidated by their rate code and returned sorted by code. When two tax lines share the same code, the engine computes a combined amount but does not store it back, so only the first line for a given code is retained — duplicate-code lines are effectively deduplicated to the first, not summed.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
taxItemsMap = TreeMap<code, TaxItem>   // sorted by code
for each taxItem:
    if code not in map: map[code] = taxItem
    existing = map[code]
    amount = existing.amount + taxItem.amount   // computed
    // NOTE: amount is NOT written back to the map entry -> discarded (defect)
if map is empty: return null
return map.values()   // one line per distinct code (first wins)
```
**Data Dependencies:**
- Reads: emitted tax lines (rate code)
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (deduped list / empty) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED — **[D-06 PRESERVED-AS-IS]** The summed amount for duplicate codes is computed but discarded; only the first line per code survives (dedup, not sum). Preserve this behavior exactly; do NOT change it to sum. Carry to Phase 4a: "Preserve dedup-to-first or fix to sum duplicate-code lines? — BA decision."
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"items": [...]}` producing two lines with the same code STATE (5.00 and 3.00)
- Success: `200 {"taxLines": [{"code": "STATE", "amount": 5.00}]}` — first line kept; the 3.00 line dropped (preserved defect), sorted by code
- Error Input: (n/a — consolidation cannot be triggered to fail; it always returns the deduped set or null)
- Error Output: (n/a)

---

### BR-TAX-024: No applicable tax yields a null result, not an empty list

**Source Reference:** `TaxServiceImpl.java:calculateTax:102-104,106-113,150-166,289-290`
**Discovery Method:** Direct Source Read
**Statement:** The tax calculation returns "no tax" (a null result) when there is no customer, when the collection-scope gates abort calculation, or when no tax lines result. It returns an empty list only when the order has a null products collection. Callers must treat a null result as "no tax applies."
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
if customer == null: return null
if items == null: return []              // empty list (distinct from null)
if province/country gate aborts: return null   (BR-TAX-008)
... calculate ...
if consolidated map is empty: return null
```
**Data Dependencies:**
- Reads: customer, order items
- Writes: none
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK (null / empty / lines) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK — preserve the null-vs-empty-list distinction exactly (null = no tax; empty list = null products collection).
**Concrete Example:**
- Input: `POST /api/v1/tax/calculate {"customer": null, "items": [...]}`
- Success: `200 null` (no tax — null customer)
- Error Input: `POST /api/v1/tax/calculate {"items": [{"unitPrice": 100.00, "quantity": 1, "taxClassCode": "DEFAULT"}]}` with no matching rate for the jurisdiction
- Error Output: `200 null` — no tax lines → null (no error; contrast case)

---

### BR-TAX-025: A tax class code is unique per store, and DEFAULT is reserved

**Source Reference:** `TaxClassController.java:saveTaxClass:99-127`; `TaxClassController.java:updateTaxClass:143-171`; `TaxClass.java:26-28`; `TaxClassDaoImpl.java:getByCode:54-63`
**Discovery Method:** Direct Source Read
**Statement:** Within a store, each tax class must have a code that is unique among that store's tax classes, and the code "DEFAULT" is reserved and may not be assigned to a user-created class. On create, a duplicate code (or the reserved DEFAULT) is rejected. On update, a duplicate code is rejected only when it belongs to a different class. A tax class requires a non-empty code (max 10 characters) and a non-empty title (max 32 characters).
**Intent:** Validation
**Weight:** Critical
**Logic:**
```
if code == "DEFAULT": reject "message.taxclass.alreadyexist"
existing = getByCode(code, store)
create:  if existing != null: reject
update:  if existing != null and existing.id != this.id: reject
// DB unique constraint: (store, taxClassCode); code NotEmpty len<=10; title NotEmpty len<=32
```
**Data Dependencies:**
- Reads: tax_class (code, merchant_id)
- Writes: tax_class (on successful create/update)
**Side Effects:** On success, creates or updates a tax_class row.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (DEFAULT + create-dup + update-dup) |
| Data-flow | 2 | 2 | OK |
| Constants | 3 | 3 | OK (DEFAULT, len 10, len 32) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (accept / reject) |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/tax-classes {"code": "REDUCED", "title": "Reduced Rate"}`
- Success: `201 {"id": "550e8400-e29b-41d4-a716-446655440000", "code": "REDUCED", "title": "Reduced Rate"}`
- Error Input: `POST /api/v1/tax/tax-classes {"code": "DEFAULT", "title": "My Default"}`
- Error Output: `409 {"error": "Conflict", "message": "tax class code already exists or is reserved: DEFAULT"}`

---

### BR-TAX-026: A tax class cannot be deleted while products reference it

**Source Reference:** `TaxClassController.java:removeTaxClass:187-238`; `TaxClassServiceImpl.java:delete:39-44`
**Discovery Method:** Direct Source Read
**Statement:** A tax class may only be deleted when no products are assigned to it. If any product references the tax class, deletion is rejected; otherwise the tax class is removed.
**Intent:** Validation
**Weight:** Critical
**Logic:**
```
products = catalog.listByTaxClass(taxClass)     // external MS-04 read
if products != null and products.size() > 0: reject "message.product.association"
else: delete taxClass
```
**Data Dependencies:**
- Reads: product tax-class association (external — MS-04 catalog), tax_class
- Writes: tax_class (delete on success)
**Side Effects:** On success, deletes the tax_class row.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (deleted / blocked) |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (catalog read) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `DELETE /api/v1/tax/tax-classes/550e8400-e29b-41d4-a716-446655440000` (no products reference it)
- Success: `204` (deleted)
- Error Input: `DELETE /api/v1/tax/tax-classes/550e8400-e29b-41d4-a716-446655440000` (2 products reference it)
- Error Output: `409 {"error": "Conflict", "message": "tax class is referenced by products and cannot be deleted"}`

---

### BR-TAX-027: A tax rate requires a parseable rate and a store-unique code; piggyback controls the parent link

**Source Reference:** `TaxRatesController.java:validateTaxRate:244-307`; `TaxRatesController.java:saveTaxRate:171-200`; `TaxRatesController.java:updateTaxRate:208-236`; `TaxRate.java:53-73`
**Discovery Method:** Direct Source Read
**Statement:** A tax rate must have a rate value that is present and parseable as a decimal, and a code that is unique among the store's tax rates. When no priority is supplied it defaults to zero. The rate's zone and country are resolved to existing reference entities. A rate is a compound (piggyback) rate only when explicitly marked; when it is not piggyback, its parent link is cleared. The rate value is stored with precision 7 and scale 4.
**Intent:** Validation
**Weight:** Critical
**Logic:**
```
if rateText blank: reject "NotEmpty.taxRate.rateText"
try taxRate = decimal(rateText) catch: reject "message.invalid.rate"
existing = getByCode(code, store)
if existing != null and existing.id != this.id: reject "NotEmpty.taxRate.unique.code"
if taxPriority == null: taxPriority = 0
if zone provided: zone = reference.zoneById(zone.id)
country = reference.countryByIso(country.isoCode)
for each description: description.taxRate = this
if not piggyback: parent = null
// DB: TAX_RATE precision 7 scale 4; unique (code, store)
```
**Data Dependencies:**
- Reads: tax_rate (code, merchant_id), country (external MS-01), zone (external MS-01)
- Writes: tax_rate, tax_rate_description (cascade) on success
**Side Effects:** On success, creates/updates a tax_rate row and its descriptions.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK (rate blank, parse, unique, priority default, zone resolve, piggyback→parent) |
| Data-flow | 5 | 5 | OK |
| Constants | 2 | 2 | OK (priority default 0, precision 7 scale 4) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (accept / reject) |
| Data writes | 2 | 2 | OK (rate + descriptions) |
| Integrations | 1 | 1 | OK (reference data) |
| Error paths | 3 | 3 | OK (rate blank, parse fail, dup code) |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/tax/tax-rates {"code": "GST", "rateText": "5.0000", "taxClassId": "...", "countryIsoCode": "CA", "zoneId": 40, "piggyback": false, "descriptions": [{"languageId": 1, "name": "GST"}]}`
- Success: `201 {"id": "...", "code": "GST", "rate": 5.0000, "taxPriority": 0, "piggyback": false, "parentId": null}`
- Error Input: `POST /api/v1/tax/tax-rates {"code": "GST", "rateText": "five percent", "countryIsoCode": "CA", "descriptions": [...]}`
- Error Output: `422 {"error": "ValidationError", "message": "rateText is not a valid rate"}`

---

### BR-TAX-028: The admin surface displays and edits tax rates with three decimal places

**Source Reference:** `TaxRatesController.java:DECIMALCOUNT:48`; `TaxRatesController.java:pageTaxRates:110-165`; `TaxRatesController.java:editTaxRate:387-420`
**Discovery Method:** Direct Source Read
**Statement:** In the administrative tax-rate list and edit views, the rate value is displayed and edited formatted to three decimal places (US locale). This is a presentation format only; the stored rate retains its full precision (scale 4) and the calculation engine uses the raw stored value.
**Intent:** Calculation
**Weight:** Critical
**Logic:**
```
DECIMALCOUNT = 3
formatter = NumberFormat(Locale.US); formatter.min = formatter.max = 3 fraction digits
grid/edit: display formatter.format(taxRate.rate)   // display-only; persisted scale is 4
```
**Data Dependencies:**
- Reads: tax_rate (rate)
- Writes: none
**Side Effects:** None (presentation only).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (3 decimals) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK — presentation constant (3dp display) preserved; storage precision is scale 4, engine uses raw value.
**Concrete Example:**
- Input: `GET /api/v1/tax/tax-rates/550e8400-e29b-41d4-a716-446655440000` (stored rate 5.0000)
- Success: `200 {"id": "...", "code": "GST", "rate": 5.0000, "rateDisplay": "5.000"}` — display formatted to 3dp, raw value preserved
- Error Input: `GET /api/v1/tax/tax-rates/not-a-uuid`
- Error Output: `404 {"error": "NotFound", "message": "tax rate not found"}`
