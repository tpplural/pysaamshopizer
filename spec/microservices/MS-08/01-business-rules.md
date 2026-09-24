# MS-08 Shipping Service — Business Rules

**Service ID**: MS-08
**Version**: 1.0
**Status**: 🟢 Extraction complete
**Analysis mode**: Direct Source Read (no CAST)
**Rule group**: BR-SHIP (single group, BR-SHIP-001 … BR-SHIP-034)

> Scope: shipping-quote orchestration, packaging (box vs item), shipping configuration, free-shipping
> policy, shipping-option price selection, the custom weight-based quote engine, and admin
> configuration authoring. The shipping-quote SPI (`ShippingQuoteModule` / `Packaging`) is modelled as
> an **extension point**: the modernized service hosts pluggable quote providers. External carrier
> gateways (UPS/USPS/CanadaPost) are OUT OF SCOPE (external integrations). All persistent state lives in
> a per-store configuration document store (legacy: JSON blobs in `MERCHANT_CONFIGURATION` /
> `MODULE_CONFIGURATION`).

---

### BR-SHIP-001: Per-store shipping configuration document is loaded, defaulting to a fresh configuration when absent

**Source Reference:** `ShippingServiceImpl.java:getShippingConfiguration:94-115`; constant `ShippingConstants.java:SHIPPING_CONFIGURATION` (value `SHIPPING_CONFIG`)
**Discovery Method:** Direct Source Read
**Statement:** Each store has a single shipping configuration document that governs its shipping behavior. When a store has never saved one, the system behaves as if an empty default configuration were present rather than failing.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
cfg = configurationStore.get(store, key="SHIPPING_CONFIG")
if cfg present:
    shippingConfiguration = deserialize(cfg.value)
    on deserialize failure -> raise "Cannot parse configuration"
else:
    return null   // callers substitute a fresh default ShippingConfiguration
```
**Data Dependencies:**
- Reads: shipping configuration document (store-scoped, key SHIPPING_CONFIG)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (config key) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (config / null) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (parse failure) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/shipping/configuration` (header `x-tenant-id: store-DEFAULT`)
- Success: `200 {"shippingType":"National","shippingOptionPriceType":"All","shippingPackageType":"Item","freeShippingEnabled":false,"taxOnShipping":false}`
- Error Input: a stored configuration document whose body is not valid JSON
- Error Output: `500 {"error":"ConfigurationParseError","message":"Cannot parse shipping configuration"}`

---

### BR-SHIP-002: Delivery country is mandatory for a shipping quote

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:359-372`
**Discovery Method:** Direct Source Read
**Statement:** A shipping quote cannot be produced unless the delivery destination has a country and the store itself has a country of origin. A request without a destination country is rejected.
**Intent:** Validation
**Weight:** High
**Logic:**
```
shipCountry = delivery.country
if shipCountry == null: raise "Delivery country is null"
require store.country != null   // Validate.notNull
```
**Data Dependencies:**
- Reads: delivery.country, store.country
**Side Effects:** none (raises)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[{"productId":"p1","quantity":1}]}`
- Success: quote pipeline proceeds (see downstream rules)
- Error Input: `POST /api/v1/shipping/quotes {"delivery":{},"items":[{"productId":"p1","quantity":1}]}`
- Error Output: `422 {"error":"ValidationError","message":"Delivery country is required"}`

---

### BR-SHIP-003: National shipping — destination country must equal the store country

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:374-381`; enum `ShippingType.java` (NATIONAL, INTERNATIONAL)
**Discovery Method:** Direct Source Read
**Statement:** When a store ships nationally only, it will quote a destination only if that destination is the same country as the store. Any other destination is refused with a "no shipping to selected country" outcome and no options are offered.
**Intent:** Validation
**Weight:** High
**Logic:**
```
shippingType = configuration.shippingType     // configuration default National
if shippingType == National:
    if destination.countryCode != store.countryCode:
        quote.returnCode = "NO_SHIPPING_TO_SELECTED_COUNTRY " + destination.countryCode
        return quote     // early exit, no options
```
**Data Dependencies:**
- Reads: shipping configuration shippingType, destination country code, store country code
**Side Effects:** sets quote return code

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (return code) |
| State transitions | 1 | 1 | OK (quote → refused) |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: store country = CA, configuration shippingType = National
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"CA"},"items":[...]}`
- Success: `200 {"returnCode":null,"options":[...]}`
- Error Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Error Output: `200 {"returnCode":"NO_SHIPPING_TO_SELECTED_COUNTRY US","options":null}`

---

### BR-SHIP-004: International shipping — destination country must be in the supported-countries list

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:382-390`; supported list from `ShippingServiceImpl.java:getSupportedCountries:520-545`
**Discovery Method:** Direct Source Read
**Statement:** When a store ships internationally, it will quote a destination only if that destination appears in the store's list of supported shipping countries. Destinations outside the list are refused with a "no shipping to selected country" outcome.
**Intent:** Validation
**Weight:** High
**Logic:**
```
if shippingType == International:
    supported = getSupportedCountries(store)   // stored list of country codes
    if destination.countryCode not in supported:
        quote.returnCode = "NO_SHIPPING_TO_SELECTED_COUNTRY " + destination.countryCode
        return quote
```
**Data Dependencies:**
- Reads: supported-countries list (store-scoped), destination country code
**Side Effects:** sets quote return code

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (return code) |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: configuration shippingType = International, supported = ["US","GB"]
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"GB"},"items":[...]}`
- Success: `200 {"returnCode":null,"options":[...]}`
- Error Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"FR"},"items":[...]}`
- Error Output: `200 {"returnCode":"NO_SHIPPING_TO_SELECTED_COUNTRY FR","options":null}`

---

### BR-SHIP-006: First active configured module wins (single-module selection, non-deterministic order preserved)

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:401-420`
**Discovery Method:** Direct Source Read
**Statement:** For a given quote, exactly one shipping provider is used: the first provider found that is marked active. If no configured provider is active, the quote reports that no shipping module is configured.
**Intent:** Routing
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — keep first-active provider selection but make ordering deterministic
**Logic:**
```
selectedProvider = null; selectedName = null
for name, config in configuredModules:      // iteration order is unordered-map order
    selectedName = name
    if config.active:
        selectedProvider = providerRegistry[name]
        break
if selectedProvider == null:
    quote.returnCode = "NO_SHIPPING_MODULE_CONFIGURED"; return quote
```
**FLAGGED (D-06 — non-determinism preserved):** iteration is over an unordered map, so when more than one
provider is active the "first active" chosen is order-dependent. Preserved; see clarification CI-08.
**Data Dependencies:**
- Reads: configured-module collection (active flag), provider registry (extension point)
**Side Effects:** none (selects provider reference)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (return code) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (selected / none) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (provider registry) |
| Error paths | 1 | 1 | OK |
**Preservation:** FLAGGED (non-deterministic selection preserved)

**Concrete Example:**
- Context: providers configured = {weightBased: active}
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `weightBased` provider selected, quote proceeds
- Error Input: providers configured = {weightBased: inactive}
- Error Output: `200 {"returnCode":"NO_SHIPPING_MODULE_CONFIGURED","options":null}`

---

### BR-SHIP-007: The selected module must also be a region-eligible shipping method

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:423-437`; `ShippingServiceImpl.java:getShippingMethods:180-196`
**Discovery Method:** Direct Source Read
**Statement:** The chosen shipping provider is only usable if it is registered as available for the store's country (or for all regions). A provider active for the store but not eligible for the store's region cannot produce a quote.
**Intent:** Validation
**Weight:** High
**Logic:**
```
methods = getShippingMethods(store)   // provider is included if its region set contains
                                      // store.countryCode OR the wildcard "*"
selectedMethod = first method whose code == selectedName
if selectedMethod == null:
    quote.returnCode = "NO_SHIPPING_MODULE_CONFIGURED"; return quote
```
**Data Dependencies:**
- Reads: integration-module definitions (region set), store country code
**Side Effects:** sets quote return code

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (return code, wildcard "*") |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: selected provider weightBased, region set = ["US","*"], store country US
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: method eligible, quote proceeds
- Error Input: selected provider region set = ["GB"], store country US
- Error Output: `200 {"returnCode":"NO_SHIPPING_MODULE_CONFIGURED","options":null}`

---

### BR-SHIP-008: Order total for shipping equals the sum of final price times quantity across items

**Source Reference:** `ShippingServiceImpl.java:calculateOrderTotal:659-673`
**Discovery Method:** Direct Source Read
**Statement:** The order value used to evaluate shipping (for example the free-shipping threshold) is the sum, over every shippable line, of that product's final price multiplied by its ordered quantity.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
total = 0
for line in items:
    finalPrice = pricing.finalPrice(line.product)   // catalog/pricing lookup
    total = total + (finalPrice * line.quantity)
return total
```
// computed: total = SUM(line.finalPrice * line.quantity)
**Data Dependencies:**
- Reads: product final price (catalog/pricing service), line quantity
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (pricing service) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: item A finalPrice 20.00 qty 2, item B finalPrice 5.00 qty 1
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[{"productId":"A","quantity":2},{"productId":"B","quantity":1}]}`
- Success: order total computed as 45.00 and used downstream
- Error Input: item references a product the pricing service cannot price
- Error Output: `502 {"error":"PricingUnavailable","message":"Cannot price product A"}`

---

### BR-SHIP-009: Package build strategy is chosen by configuration — box packing or per-item

**Source Reference:** `ShippingServiceImpl.java:getPackagesDetails:697-720`; enum `ShippingPackageType.java` (ITEM, BOX)
**Discovery Method:** Direct Source Read
**Statement:** Before quoting, the cart contents are turned into shippable packages using one of two strategies chosen by store configuration: pack items into boxes, or ship each item as its own package. The default is per-item.
**Intent:** Routing
**Weight:** High
**Logic:**
```
packageType = configuration.shippingPackageType   // default Item
if packageType == Box: packages = packaging.boxPackages(items, store)
else:                  packages = packaging.itemPackages(items, store)
```
**Data Dependencies:**
- Reads: shipping configuration package type
**Side Effects:** delegates to packaging extension (see BR-SHIP-020..025)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (default Item) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (box / item) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (packaging extension) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: configuration shippingPackageType = Box
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[{"productId":"A","quantity":3}]}`
- Success: box packing engine invoked, packages returned
- Error Input: configuration shippingPackageType = Box but box dimensions are zero (see BR-SHIP-023)
- Error Output: `200 {"returnCode":"ERROR","quoteError":"Product configuration exceeds box configuration"}`

---

### BR-SHIP-010: Free-shipping applies when order total is strictly greater than the threshold (double comparison preserved)

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:443-463`
**Discovery Method:** Direct Source Read
**Statement:** When free shipping is enabled and configured with a threshold, an order qualifies for free shipping only when its order total is strictly greater than the threshold. For a national free-shipping scope the destination must match the store country; for the international scope any supported destination qualifies. A qualifying order returns a free-shipping quote with no priced options.
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — free-shipping threshold uses >= and exact decimals
**Logic:**
```
if configuration.freeShippingEnabled:
    threshold = configuration.orderTotalFreeShipping
    if threshold != null AND orderTotal > threshold:        // STRICT >, compared as double
        if configuration.freeShippingType == National:
            if store.countryCode == destination.countryCode:
                quote.freeShipping = true; quote.freeShippingAmount = threshold; return quote
        else:   // international / all
            quote.freeShipping = true; quote.freeShippingAmount = threshold; return quote
```
**FLAGGED (D-06):** comparison is strictly `>` (an order exactly equal to the threshold does NOT qualify)
and is performed on floating-point values rather than exact decimals (precision risk). Free shipping
causes an early return BEFORE the provider is invoked, so no option is produced. Preserved; see CI-01, CI-02.
**Data Dependencies:**
- Reads: configuration freeShippingEnabled, orderTotalFreeShipping, freeShippingType; store & destination country codes
**Side Effects:** sets quote freeShipping + freeShippingAmount; early return

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (National scope) |
| State transitions | 1 | 1 | OK (quote → free) |
| Outcomes | 2 | 2 | OK (national / intl) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: freeShippingEnabled=true, threshold=100.00, scope=International, orderTotal=150.00
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"GB"},"items":[...]}`
- Success: `200 {"freeShipping":true,"freeShippingAmount":100.00,"options":null}`
- Error Input (does not qualify): orderTotal exactly 100.00 (equal to threshold)
- Error Output: `200 {"freeShipping":false,"options":[...]}` (strict `>` — equal amount still pays shipping)

---

### BR-SHIP-011: Handling fee and tax-on-shipping flag are carried from configuration onto the quote

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:466-474`
**Discovery Method:** Direct Source Read
**Statement:** A quote carries the store's flat handling fee (when configured) and a flag indicating whether shipping is taxable, so downstream order totalling can add the handling fee and the tax engine can decide whether to tax shipping.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
if configuration.handlingFees != null: quote.handlingFees = configuration.handlingFees
quote.applyTaxOnShipping = configuration.taxOnShipping
```
**Data Dependencies:**
- Reads: configuration handlingFees, taxOnShipping
**Side Effects:** sets quote handlingFees, applyTaxOnShipping

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: handlingFees=3.50, taxOnShipping=true
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"handlingFees":3.50,"applyTaxOnShipping":true,"options":[...]}`
- Error Input: (no handling fee configured)
- Error Output: `200 {"handlingFees":null,"applyTaxOnShipping":false,"options":[...]}`

---

### BR-SHIP-012: A provider failure is caught, logged to the merchant log, and returns an ERROR quote (non-fatal)

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:480-498`; SPI `ShippingQuoteModule.java:getShippingQuotes`
**Discovery Method:** Direct Source Read
**Statement:** If the selected shipping provider throws while computing quotes, the failure is recorded in the store's operational log and the quote is returned with an ERROR outcome and the error message, rather than aborting the whole checkout.
**Intent:** State Transition
**Weight:** High
**Logic:**
```
try:
    options = provider.getShippingQuotes(packages, orderTotal, delivery, store, config, method, configuration, locale)
catch e:
    merchantLog.save(store, "Can't process " + method.name + " -> " + e.message)
    quote.quoteError = e.message
    quote.returnCode = "ERROR"
    return quote
```
**Data Dependencies:**
- Reads: provider result / exception
- Writes: merchant operational log
**Side Effects:** writes merchant log; sets quote returnCode/quoteError

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (ERROR code) |
| State transitions | 1 | 1 | OK (quote → error) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (merchant log) |
| Integrations | 1 | 1 | OK (provider) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: provider throws while quoting
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: (normal) provider returns options
- Error Input: provider raises an internal error
- Error Output: `200 {"returnCode":"ERROR","quoteError":"<provider message>","options":null}` (and a merchant-log entry is written)

---

### BR-SHIP-013: A null provider result yields a "no shipping to selected country" outcome

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:500-503`
**Discovery Method:** Direct Source Read
**Statement:** When the selected provider returns no options at all (for example the weight-based engine found no matching region or weight bracket), the quote is flagged as "no shipping to selected country".
**Intent:** Routing
**Weight:** High
**Logic:**
```
if options == null:
    quote.returnCode = "NO_SHIPPING_TO_SELECTED_COUNTRY"
// note: moduleCode is still set afterward; option processing is guarded by options != null
```
**Data Dependencies:**
- Reads: provider result
**Side Effects:** sets quote return code

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (return code) |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: weight-based engine finds no bracket ≥ total weight
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[{"productId":"heavy","quantity":50}]}`
- Success: (normal) a matching bracket returns an option
- Error Input: total weight exceeds every configured bracket
- Error Output: `200 {"returnCode":"NO_SHIPPING_TO_SELECTED_COUNTRY","options":null}`

---

### BR-SHIP-014: Each option's displayable price text is formatted in the store currency

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:515-521`
**Discovery Method:** Direct Source Read
**Statement:** Every returned shipping option is given a human-readable price formatted according to the store's currency, so the storefront can display it directly.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
for option in options:
    option.optionPriceText = pricing.displayAmount(option.optionPrice, store)
```
**Data Dependencies:**
- Reads: option price, store currency
**Side Effects:** sets option price text

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (pricing/format) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: option price 12.5, store currency USD
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"options":[{"optionPrice":12.50,"optionPriceText":"$12.50"}]}`
- Error Input: option with an unparseable stored price text
- Error Output: option retains numeric price; text falls back to raw value

---

### BR-SHIP-015: An option with no name defaults to the delivery country name, falling back to its ISO code

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:523-537`
**Discovery Method:** Direct Source Read
**Statement:** When a shipping option has no name, it is labelled with the delivery country's display name; if that name is unavailable, the country's ISO code is used as the label.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
if option.optionName is blank:
    name = destination.country.name
    if name == null:
        countries = countryService.countriesMap(language)
        c = countries[destination.countryCode]
        name = (c != null) ? c.name : destination.countryCode
    option.optionName = name
```
**Data Dependencies:**
- Reads: destination country name / ISO code, country reference data
**Side Effects:** sets option name

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (name / iso) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (country reference) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: option name blank, destination US, country name "United States"
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"options":[{"optionName":"United States"}]}`
- Error Input: destination country has no display name and is not in reference data
- Error Output: `200 {"options":[{"optionName":"US"}]}` (ISO code fallback)

---

### BR-SHIP-016: Highest price selection picks the most expensive option (whole-unit comparison preserved)

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:539-547`; enum `ShippingOptionPriceType.java` (LEAST, HIGHEST, ALL)
**Discovery Method:** Direct Source Read
**Statement:** When the store is configured to present the highest-priced shipping option, the option with the greatest price is selected as the default.
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — option price selection uses exact decimals (no whole-unit truncation)
**Logic:**
```
if priceType == Highest:
    if option.price (whole units) > selected.price (whole units):
        selected = option
```
**FLAGGED (D-06):** the comparison truncates to whole currency units, so the fractional part (cents) is
ignored when comparing options. Preserved; see CI-03.
**Data Dependencies:**
- Reads: configuration price type, option prices
**Side Effects:** sets selected option

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (Highest) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED (whole-unit truncation preserved)

**Concrete Example:**
- Context: priceType=Highest, options priced 5.00, 12.00, 8.00
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"selectedOption":{"optionPrice":12.00},"options":[{"optionPrice":12.00}]}`
- Error Input: two options 12.20 and 12.80 (same whole unit 12)
- Error Output: first-seen retained as selected (cents ignored — flagged quirk)

---

### BR-SHIP-017: Least and All price selection both pick the cheapest option (whole-unit comparison preserved)

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:549-567`; enum `ShippingOptionPriceType.java`
**Discovery Method:** Direct Source Read
**Statement:** When the store is configured for the least-priced option, or to present all options, the cheapest option is chosen as the default selection. (The two configurations differ only in whether the full list is preserved — see BR-SHIP-018.)
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — Least/Highest/All selection uses exact decimals (no whole-unit truncation)
**Logic:**
```
if priceType == Least: if option.price (whole units) < selected.price (whole units): selected = option
if priceType == All:   if option.price (whole units) < selected.price (whole units): selected = option   // identical body
```
**FLAGGED (D-06):** the Least and All selection bodies are identical (both pick cheapest as default), and
both truncate to whole currency units. Preserved; see CI-03, CI-04.
**Data Dependencies:**
- Reads: configuration price type, option prices
**Side Effects:** sets selected option

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (Least, All) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED (Least/All identical + whole-unit truncation preserved)

**Concrete Example:**
- Context: priceType=Least, options priced 5.00, 12.00, 8.00
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"selectedOption":{"optionPrice":5.00}}`
- Error Input: priceType=All with same options
- Error Output: `200 {"selectedOption":{"optionPrice":5.00},"options":[5.00,12.00,8.00]}` (list preserved)

---

### BR-SHIP-018: Non-All price types collapse the offered options to the single selected option

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:570-576`; enum `ShippingOptionPriceType.java`
**Discovery Method:** Direct Source Read
**Statement:** When the store is configured for least or highest pricing, the customer is offered exactly one option (the selected one). When configured to present all options, every returned option is offered, with the cheapest marked as the default selection.
**Intent:** Routing
**Weight:** High
**Logic:**
```
if selected != null AND priceType != All:
    options = [ selected ]     // collapse to one
// priceType == All: keep the full options list, selected marks default
```
**Data Dependencies:**
- Reads: configuration price type, selected option
**Side Effects:** replaces quote options list

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (All) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (collapse / keep) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: priceType=Least, three options
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"options":[{"optionPrice":5.00}]}` (single option)
- Error Input: priceType=All, three options
- Error Output: `200 {"options":[5.00,12.00,8.00],"selectedOption":{"optionPrice":5.00}}`

---

### BR-SHIP-019: Shipping summary is assembled from the customer-selected option (taxOnShipping gap preserved)

**Source Reference:** `ShippingServiceImpl.java:getShippingSummary:328-340`
**Discovery Method:** Direct Source Read
**Statement:** Once the customer has chosen a shipping option, the order's shipping summary records the chosen option's price as the shipping amount, the quote's handling fee, the free-shipping flag, the provider code, and the option description — this summary is what order totalling consumes.
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — propagate taxOnShipping into the summary correctly
**Logic:**
```
summary.freeShipping   = quote.freeShipping
summary.handling       = quote.handlingFees
summary.shipping       = selectedOption.optionPrice
summary.shippingModule = quote.shippingModuleCode
summary.shippingOption = selectedOption.description
// summary.taxOnShipping is NOT set here (remains false)
```
**FLAGGED (D-06):** the summary has a taxOnShipping field but it is never populated in this assembly even
though the quote carries applyTaxOnShipping — potential gap for the tax engine. Preserved; see CI-07.
**Data Dependencies:**
- Reads: quote (freeShipping, handlingFees, moduleCode), selected option (price, description)
**Side Effects:** none (builds summary)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (taxOnShipping gap flagged) |
**Preservation:** FLAGGED (taxOnShipping not propagated — preserved)

**Concrete Example:**
- Context: selectedOption price 8.00, handling 3.50, freeShipping false
- Input: `POST /api/v1/shipping/summary {"selectedOptionId":"CUSTOM_WEIGHT_NA","quote":{...}}`
- Success: `200 {"shipping":8.00,"handling":3.50,"freeShipping":false,"taxOnShipping":false}`
- Error Input: request with no selected option
- Error Output: `422 {"error":"ValidationError","message":"A selected shipping option is required"}`

---

### BR-SHIP-020: Virtual products are excluded from packaging

**Source Reference:** `DefaultPackagingImpl.java:getBoxPackagesDetails:78`; `DefaultPackagingImpl.java:getItemPackagesDetails:290`; SPI `Packaging.java`
**Discovery Method:** Direct Source Read
**Statement:** Virtual (non-physical) products contribute nothing to shipping — they are skipped by both packaging strategies and add no weight or volume to any package.
**Intent:** Validation
**Weight:** High
**Logic:**
```
for line in items:
    if line.product.isVirtual: continue   // skip, contributes no package
```
**Data Dependencies:**
- Reads: product virtual flag (catalog)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (catalog product) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: cart has one physical item and one virtual item
- Input: `POST /api/v1/shipping/packages {"items":[{"productId":"phys","quantity":1,"virtual":false},{"productId":"dl","quantity":1,"virtual":true}]}`
- Success: `200 {"packages":[{"itemName":"phys"}]}` (virtual skipped)
- Error Input: cart of only virtual items
- Error Output: `200 {"packages":[]}` (no packages; item strategy) / `200 {"packages":null}` (box strategy — see BR-SHIP-022 note)

---

### BR-SHIP-021: Product dimensions and weight default when unset, and attribute weight is accumulated (ITEM-path getter mismatch preserved)

**Source Reference:** `DefaultPackagingImpl.java:getBoxPackagesDetails:88-118`; `DefaultPackagingImpl.java:getItemPackagesDetails:296-322`
**Discovery Method:** Direct Source Read
**Statement:** Each product's shipping weight and dimensions are taken from the product; when any is missing, a standard default is used (weight 1, height/length/width 4). Selected product options can add extra weight, which is summed into the product's shipping weight.
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — fix ITEM-path getter mismatch (correct attribute-weight field)
**Logic:**
```
w  = product.weight ?? 1.0
h  = product.height ?? 4.0
l  = product.length ?? 4.0
wd = product.width  ?? 4.0
for attribute in product.attributes:
    // BOX path:
    if attribute.optionWeight != null: w = w + attribute.optionWeight
    // ITEM path (PRESERVED DEFECT): guard tests attributeAdditionalWeight but adds optionWeight
    if attribute.attributeAdditionalWeight != null: w = w + attribute.optionWeight
```
**FLAGGED (D-06 — defect preserved):** in the per-item path the null guard is on one attribute-weight
field but the value added is a different attribute-weight field (mismatched getter). Preserved as-is; see CI-05.
**Data Dependencies:**
- Reads: product weight/height/length/width, product attribute weights (catalog)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 4 | 4 | OK (defaults 1/4/4/4) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (catalog attributes) |
| Error paths | 1 | 1 | OK (getter-mismatch quirk) |
**Preservation:** FLAGGED (ITEM-path getter mismatch preserved)

**Concrete Example:**
- Context: product weight null (→ default 1.0), one attribute adding 0.5
- Input: `POST /api/v1/shipping/packages {"items":[{"productId":"A","quantity":1,"attributes":[{"additionalWeight":0.5}]}]}`
- Success: `200 {"packages":[{"shippingWeight":1.5,"shippingHeight":4,"shippingLength":4,"shippingWidth":4}]}`
- Error Input: product with all dimensions null and no attributes
- Error Output: `200 {"packages":[{"shippingWeight":1,"shippingHeight":4,"shippingLength":4,"shippingWidth":4}]}`

---

### BR-SHIP-022: Per-item packaging explodes each unit of quantity into its own package (quantity field quirk preserved)

**Source Reference:** `DefaultPackagingImpl.java:getItemPackagesDetails:324-370`
**Discovery Method:** Direct Source Read
**Statement:** In the per-item strategy, a line of quantity N becomes N separate packages, each carrying that product's dimensions and weight and a name taken from the product's first description (defaulting to "item").
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — per-package quantity is 1 (not full line quantity)
**Logic:**
```
if line.quantity == 1: emit 1 package { dims, weight, quantity=1, name=firstDescription||"item" }
else if line.quantity > 1:
    for i in 1..quantity: emit 1 package { dims, weight, quantity=<full quantity> }
```
**FLAGGED (D-06):** each emitted package's quantity field is set to the FULL line quantity rather than 1
(a minor inconsistency; downstream weight aggregation sums per-package shippingWeight, so the count of
packages is what matters). Preserved; see CI-11.
**Data Dependencies:**
- Reads: line quantity, product dimensions/weight, product description (catalog)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK ("item" default) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (qty=1 / qty>1) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (catalog) |
| Error paths | 1 | 1 | OK (quantity quirk) |
**Preservation:** FLAGGED (per-package quantity quirk preserved)

**Concrete Example:**
- Context: item strategy, product A quantity 3
- Input: `POST /api/v1/shipping/packages {"items":[{"productId":"A","quantity":3}]}`
- Success: `200 {"packages":[{"itemName":"A"},{"itemName":"A"},{"itemName":"A"}]}` (3 packages)
- Error Input: product A quantity 0
- Error Output: `200 {"packages":[]}` (neither the ==1 nor the >1 branch fires)

---

### BR-SHIP-023: Box packaging requires a valid box configuration (positive volume and max weight)

**Source Reference:** `DefaultPackagingImpl.java:getBoxPackagesDetails:55-75`; `DefaultPackagingImpl.java:getBoxPackagesDetails:148-162`
**Discovery Method:** Direct Source Read
**Statement:** Box packing can only proceed when the store's box is fully configured: a box must exist, and its computed volume (width × length × height) and maximum weight must both be greater than zero. An invalid box configuration is logged to the store's operational log and rejected.
**Intent:** Validation
**Weight:** High
**Logic:**
```
box = store.shippingConfiguration
if box == null: raise "ShippingConfiguration not found"
maxVolume = box.width * box.length * box.height
if maxVolume == 0 OR box.maxWeight == 0:
    merchantLog.save(store, "Check shipping box configuration ... must be greater than 0")
    raise "Product configuration exceeds box configuration"
```
**Data Dependencies:**
- Reads: box width/length/height/weight, max weight (shipping configuration)
- Writes: merchant operational log
**Side Effects:** writes merchant log; raises on invalid box config

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (zero guard) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (merchant log) |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: box 10×10×10, maxWeight 50
- Input: `POST /api/v1/shipping/packages {"strategy":"Box","items":[...]}`
- Success: box packing proceeds
- Error Input: box configured with height 0
- Error Output: `422 {"error":"BoxConfigurationError","message":"Product configuration exceeds box configuration"}` (and merchant-log entry written)

---

### BR-SHIP-024: Box packaging validates each product fits the box by dimension, weight, and volume

**Source Reference:** `DefaultPackagingImpl.java:getBoxPackagesDetails:185-235`
**Discovery Method:** Direct Source Read
**Statement:** For box packing, every product must fit the configured box: no product dimension may exceed the box's corresponding dimension, no product may weigh more than the box maximum, and a product with zero volume or a volume larger than the box is rejected. Fit failures are logged and stop the box quote.
**Intent:** Validation
**Weight:** High
**Logic:**
```
if p.width > boxWidth OR p.height > boxHeight OR p.length > boxLength:
    merchantLog.save(...); raise "exceeds box configuration"
if p.weight > box.maxWeight:
    merchantLog.save(...); raise "exceeds box configuration"
productVolume = p.width * p.height * p.length
if productVolume == 0: merchantLog.save(...); raise "exceeds box configuration"
if productVolume > maxVolume: raise "exceeds box configuration"   // no log on this branch
```
**Data Dependencies:**
- Reads: product dimensions/weight, box dimensions/max weight/volume
- Writes: merchant operational log (three of four failure branches)
**Side Effects:** writes merchant log; raises (caller catches → ERROR quote per BR-SHIP-012)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (zero volume) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (merchant log, 3 of 4) |
| Integrations | 0 | 0 | OK |
| Error paths | 4 | 4 | OK |
**Preservation:** OK

**Concrete Example:**
- Context: box 10×10×10 maxWeight 50; product 5×5×5 weight 10
- Input: `POST /api/v1/shipping/packages {"strategy":"Box","items":[{"productId":"A","quantity":1}]}`
- Success: product fits, packing proceeds
- Error Input: product 20×5×5 (width exceeds box)
- Error Output: `422 {"error":"BoxConfigurationError","message":"Product configuration exceeds box configuration"}` (merchant-log entry written)

---

### BR-SHIP-025: Box bin-packing uses a 75%-volume-fit heuristic and rolls up box weight (stale-box output weight defect preserved)

**Source Reference:** `DefaultPackagingImpl.java:getBoxPackagesDetails:237-320`
**Discovery Method:** Direct Source Read
**Statement:** For box packing, each unit is placed into the first box that can still hold its volume — reserving 25% of each box's volume as slack — and its weight; when no existing box fits, a new box is opened. One package is emitted per box.
**Intent:** Calculation
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — per-box weight/dimensions (fix stale loop-variable reference)
**Logic:**
```
explode each line into individual units (quantity copies)
box0 = { volumeLeft = maxVolume, weightLeft = maxWeight }
for unit in units:
    unitVolume = unit.width * unit.height * unit.length ; unitWeight = unit.weight
    placed = false
    for box in boxes:
        if (box.volumeLeft * 0.75) >= unitVolume AND box.weightLeft >= unitWeight:
            box.volumeLeft -= unitVolume ; box.weightLeft -= unitWeight ; box.weight += unitWeight
            placed = true ; break
    if not placed:
        newBox = { volumeLeft = maxVolume - unitVolume, weightLeft = maxWeight - unitWeight, weight = unitWeight }
        boxes.add(newBox)
// emit: one package per box, shippingWeight = configBoxWeight + <lastBox>.weight  (STALE reference)
```
**FLAGGED (D-06 — defect preserved):** the output loop builds one package per box but sets every package's
shipping weight from the LAST created box's weight (stale loop variable), and uses the configured box
height/length/width for every package rather than per-box values. The 0.75 factor is an intentional 25%
packing-slack reservation. Preserved as-is; see CI-06.
**Data Dependencies:**
- Reads: unit dimensions/weight, box configuration (dims, max weight/volume)
**Side Effects:** none (returns packages)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (0.75 slack, maxBox=100) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (fit / new box) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (stale-weight defect) |
**Preservation:** FLAGGED (stale-box output weight defect preserved)

**Concrete Example:**
- Context: box volume 1000, maxWeight 50; three units each volume 200, weight 10
- Input: `POST /api/v1/shipping/packages {"strategy":"Box","items":[{"productId":"A","quantity":3}]}`
- Success: `200 {"packages":[{"shippingWeight":<configBoxWeight + rolled weight>}]}` (units fit within 75% slack)
- Error Input: a unit whose volume exceeds the box volume
- Error Output: `422 {"error":"BoxConfigurationError","message":"Product configuration exceeds box configuration"}`

---

### BR-SHIP-026: Custom weight-based provider configuration is a per-store document, defaulting to empty

**Source Reference:** `CustomWeightBasedShippingQuote.java:getCustomModuleConfiguration:56-80`; constant `CustomWeightBasedShippingQuote.java:MODULE_CODE` (value `weightBased`)
**Discovery Method:** Direct Source Read
**Statement:** The custom weight-based shipping provider keeps its own per-store configuration document describing its shipping regions and their weight-priced brackets; when a store has none, an empty configuration is used.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
cfg = configurationStore.get(store, key="weightBased")
if cfg present:
    return deserialize(cfg.value)   // regions[], each with countries[] and quoteItems[]
    on failure -> raise "Cannot parse configuration"
else:
    return empty CustomShippingQuotesConfiguration(moduleCode="weightBased")
```
**Data Dependencies:**
- Reads: custom weight-based configuration document (store-scoped, key weightBased)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (module code) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (config / empty) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (parse failure) |
**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/shipping/providers/weightBased/configuration` (header `x-tenant-id: store-1`)
- Success: `200 {"moduleCode":"weightBased","active":true,"regions":[{"customRegionName":"NA","countries":["US","CA"],"quoteItems":[...]}]}`
- Error Input: stored configuration body not valid JSON
- Error Output: `500 {"error":"ConfigurationParseError","message":"Cannot parse weight-based configuration"}`

---

### BR-SHIP-028: Total shipping weight equals the sum of package weights

**Source Reference:** `CustomWeightBasedShippingQuote.java:getShippingQuotes:117-123`
**Discovery Method:** Direct Source Read
**Statement:** The weight used by the custom weight-based provider is the total of the shipping weights of all packages produced for the order.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
totalWeight = 0
for package in packages:
    totalWeight = totalWeight + package.shippingWeight
```
// computed: totalWeight = SUM(package.shippingWeight)
**Data Dependencies:**
- Reads: package shipping weight (from packaging)
**Side Effects:** none

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
- Context: three packages of shipping weight 1.5, 1.5, 2.0
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: total weight computed as 5.0 and used for bracket lookup
- Error Input: no packages produced (all virtual items)
- Error Output: total weight 0 → matches the lowest bracket if one covers 0 (else no option)

---

### BR-SHIP-029: Weight-range price lookup — the first bracket whose maximum weight is at least the total weight sets the price

**Source Reference:** `CustomWeightBasedShippingQuote.java:getShippingQuotes:125-145`; entity `CustomShippingQuoteWeightItem.java` (maximumWeight, price)
**Discovery Method:** Direct Source Read
**Statement:** Within the matched region, the shipping price is the flat price of the first weight bracket (in ascending order of maximum weight) whose maximum weight is at least the order's total weight. If the total weight exceeds every bracket, the provider returns no option. Exactly one option is produced.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
for bracket in region.quoteItems:      // ascending maximumWeight (sorted at authoring time)
    if totalWeight <= bracket.maximumWeight:
        option.optionCode  = "CUSTOM_WEIGHT"
        option.optionId    = "CUSTOM_WEIGHT_" + region.name
        option.optionPrice = bracket.price
        option.optionPriceText = format(store, bracket.price)
        break                           // first (lowest) sufficient bracket wins
return option != null ? [option] : null
```
**Data Dependencies:**
- Reads: bracket maximumWeight and price, total weight, region name
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (CUSTOM_WEIGHT code) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (bracket / null) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (currency format) |
| Error paths | 1 | 1 | OK (no bracket) |
**Preservation:** OK

**Concrete Example:**
- Context: region NA brackets [{maxWeight:5, price:8.00},{maxWeight:20, price:15.00}], total weight 3
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: `200 {"options":[{"optionCode":"CUSTOM_WEIGHT","optionId":"CUSTOM_WEIGHT_NA","optionPrice":8.00}]}`
- Error Input: total weight 25 (exceeds every bracket)
- Error Output: `200 {"returnCode":"NO_SHIPPING_TO_SELECTED_COUNTRY","options":null}`

---

### BR-SHIP-030: Shipping administration actions require the shipping role (one endpoint lacks the guard)

**Source Reference:** `ShippingConfigsController.java:displayShippingConfigs:56` (`@PreAuthorize hasRole('SHIPPING')`); `ShippingOptionsController.java:saveShippingOptions:96`; `ShippingPackagingController.java:saveShippingPackaging:82`; `ShippingMethodsController.java:deleteShippingMethod:161` (NO guard)
**Discovery Method:** Direct Source Read
**Statement:** Every shipping-administration operation (viewing or saving shipping configuration, options, packaging, methods, and custom regions) is restricted to users holding the shipping-management role. One legacy delete-method endpoint is missing this restriction.
**Intent:** Authorization
**Weight:** High
**4a Decision:** Simplify (fix-on-migration) — gate the delete-shipping-method endpoint with the missing role guard
**Logic:**
```
for each shipping admin operation: require caller has role SHIPPING
// EXCEPTION: ShippingMethodsController.deleteShippingMethod has no role guard
```
**FLAGGED (D-06 — authorization gap preserved):** the standard delete-shipping-method endpoint carries no
role annotation while all sibling endpoints do. Modernized service SHOULD gate it, but the gap is recorded
as-is. See CI-12.
**Data Dependencies:**
- Reads: caller role
**Side Effects:** none (guard)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (SHIPPING role) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (allow / deny) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (security) |
| Error paths | 1 | 1 | OK (unguarded endpoint flagged) |
**Preservation:** FLAGGED (authorization gap preserved)

**Concrete Example:**
- Context: caller without shipping role
- Input: `PUT /api/v1/shipping/configuration {...}` (no shipping role)
- Success: (with role) `200 {...}`
- Error Input: `PUT /api/v1/shipping/configuration {...}` without shipping role
- Error Output: `403 {"error":"Forbidden","message":"Requires SHIPPING role"}`

---

### BR-SHIP-031: Saving a shipping-provider configuration validates through the provider, then stores it encrypted

**Source Reference:** `ShippingServiceImpl.java:saveShippingQuoteModuleConfiguration:205-248`; SPI `ShippingQuoteModule.java:validateModuleConfiguration`
**Discovery Method:** Direct Source Read
**Statement:** When a shipping provider's configuration is saved, the target provider must exist and is asked to validate the configuration first; only then is the full set of provider configurations stored, encrypted at rest.
**Intent:** Validation
**Weight:** High
**Logic:**
```
provider = providerRegistry[config.moduleCode]
if provider == null: raise "Shipping quote module <code> does not exist"
provider.validateModuleConfiguration(config, store)   // extension hook (weightBased = no-op)
modules = decrypt(existing configuration document) or new
modules[config.moduleCode] = config
store encrypt(serialize(modules))   // encrypted at rest
```
**Data Dependencies:**
- Reads: provider registry, existing encrypted module document
- Writes: encrypted shipping-module configuration document
**Side Effects:** writes configuration document (encrypted)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (config saved) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (encrypted document) |
| Integrations | 1 | 1 | OK (provider validate hook) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/shipping/providers {"moduleCode":"weightBased","active":true}`
- Success: `200 {"moduleCode":"weightBased","active":true}` (validated + stored encrypted)
- Error Input: `PUT /api/v1/shipping/providers {"moduleCode":"nonexistent"}`
- Error Output: `422 {"error":"UnknownProvider","message":"Shipping quote module nonexistent does not exist"}`

---

### BR-SHIP-032: Custom weight-based authoring — unique region names, unique country-per-region, positive unique weight brackets kept ascending

**Source Reference:** `CustomShippingMethodsController.java:addCustomRegion:87-125`; `CustomShippingMethodsController.java:addCountryToCustomRegion:132-180`; `CustomShippingMethodsController.java:addPrice:445-560`
**Discovery Method:** Direct Source Read
**Statement:** When a merchant builds the custom weight-based configuration: a region name must be non-empty and unique; a country may be added to a region only once; and a price bracket must have a parseable price and a maximum weight greater than zero, with no duplicate maximum weight in that region. Brackets are kept sorted ascending by maximum weight so the cheapest sufficient bracket is chosen at quote time.
**Intent:** Validation
**Weight:** High
**Logic:**
```
addRegion:  reject if region name blank OR name already exists
addCountry: reject if country already present in region; else append
addPrice:   price = parse(priceText); reject if unparseable OR blank
            reject if maximumWeight <= 0
            reject if a bracket with the same maximumWeight already exists
            append bracket; sort region.quoteItems ascending by maximumWeight
```
**Data Dependencies:**
- Reads: existing regions, countries, brackets (custom weight-based document)
- Writes: custom weight-based configuration document
**Side Effects:** writes custom weight-based configuration document

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (weight > 0) |
| State transitions | 1 | 1 | OK (config updated) |
| Outcomes | 2 | 2 | OK (accepted / rejected) |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 4 | 4 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/shipping/providers/weightBased/regions/NA/prices {"maximumWeight":5,"priceText":"8.00"}`
- Success: `201 {"customRegionName":"NA","quoteItems":[{"maximumWeight":5,"price":8.00}]}`
- Error Input: `POST /api/v1/shipping/providers/weightBased/regions/NA/prices {"maximumWeight":0,"priceText":"8.00"}`
- Error Output: `422 {"error":"ValidationError","message":"Maximum weight must be greater than zero"}`

---

### BR-SHIP-033: Saving shipping options parses money text for free-shipping threshold and handling fee, then persists the flags

**Source Reference:** `ShippingOptionsController.java:saveShippingOptions:108-150`
**Discovery Method:** Direct Source Read
**Statement:** When shipping options are saved, any supplied free-shipping threshold and handling fee are parsed from their text values (a malformed money value is a validation error), and the free-shipping-enabled flag, tax-on-shipping flag, free-shipping scope, and price-selection type are stored.
**Intent:** Validation
**Weight:** High
**Logic:**
```
if orderTotalFreeShippingText not blank: threshold = parseMoney(text)  [reject "invalid price" on failure]
if handlingFeesText not blank:           handling  = parseMoney(text)  [reject "invalid price" on failure]
config.freeShippingEnabled = submitted.freeShippingEnabled
config.taxOnShipping       = submitted.taxOnShipping
if submitted.freeShippingScope != null: config.freeShippingScope = submitted.freeShippingScope
config.priceSelectionType  = submitted.priceSelectionType
persist config
```
**Data Dependencies:**
- Reads: submitted option fields
- Writes: shipping configuration document
**Side Effects:** writes shipping configuration document

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (config updated) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK (two parse failures) |
**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/shipping/options {"freeShippingEnabled":true,"orderTotalFreeShippingText":"100.00","handlingFeesText":"3.50","taxOnShipping":true,"priceSelectionType":"LEAST"}`
- Success: `200 {"freeShippingEnabled":true,"orderTotalFreeShipping":100.00,"handlingFees":3.50,"taxOnShipping":true,"shippingOptionPriceType":"LEAST"}`
- Error Input: `PUT /api/v1/shipping/options {"handlingFeesText":"abc"}`
- Error Output: `422 {"error":"ValidationError","message":"Invalid price"}`

---

### BR-SHIP-034: Saving packaging rounds box weight to two decimals and persists box dimensions and package type

**Source Reference:** `ShippingPackagingController.java:saveShippingPackaging:95-115`
**Discovery Method:** Direct Source Read
**Statement:** When box packaging is saved, the box weight is rounded to two decimal places, and the box dimensions and the chosen package strategy (box or per-item) are stored on the shipping configuration.
**Intent:** Calculation
**Weight:** High
**Logic:**
```
weight = round2dp(submitted.boxWeight)
config.boxHeight = submitted.boxHeight
config.boxLength = submitted.boxLength
config.boxWidth  = submitted.boxWidth
config.boxWeight = weight
config.packageType = submitted.packageType   // ITEM | BOX
persist config
```
**Data Dependencies:**
- Reads: submitted box fields
- Writes: shipping configuration document
**Side Effects:** writes shipping configuration document

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (2dp rounding) |
| State transitions | 1 | 1 | OK (config updated) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/shipping/packaging {"boxWidth":10,"boxHeight":10,"boxLength":10,"boxWeight":2.457,"packageType":"BOX"}`
- Success: `200 {"boxWidth":10,"boxHeight":10,"boxLength":10,"boxWeight":2.46,"shippingPackageType":"BOX"}`
- Error Input: `PUT /api/v1/shipping/packaging {"packageType":"CRATE"}`
- Error Output: `422 {"error":"ValidationError","message":"packageType must be ITEM or BOX"}`
