# MS-08 (shipping) — Obsolete Rules Appendix (Phase 4a)

These rules were classified **Obsolete** during Phase 4a BA review (Mode A, human-approved 2026-09-20) and are NOT implemented in the modernized service. They captured dead / unreachable legacy code whose real behavior is provided by another rule.

| BR-ID | Drop rationale | Real behavior lives in |
|-------|----------------|------------------------|
| BR-SHIP-005 | Dead null-branch: the module loader always returns an empty collection (never null), so the null guard is unreachable. | BR-SHIP-006 (no-active-provider guard) |
| BR-SHIP-027 | Dead read: the provider reads the shipping-basis type into a local and never uses it. | n/a (no behavioral effect) |

---

## Dropped rule blocks (preserved for traceability)

### BR-SHIP-005: A shipping quote requires at least one configured shipping module (dead null-branch preserved)

**Source Reference:** `ShippingServiceImpl.java:getShippingQuote:392-398`; `ShippingServiceImpl.java:getShippingModulesConfigured:295-315`
**Discovery Method:** Direct Source Read
**Statement:** A store must have at least one shipping provider configured before a quote can be produced; otherwise the quote reports that no shipping module is configured.
**Intent:** Validation
**Logic:**
```
modules = getShippingModulesConfigured(store)   // returns empty collection, never null
if modules == null:                              // PRESERVED DEAD BRANCH
    quote.returnCode = "NO_SHIPPING_MODULE_CONFIGURED"
    return quote
```
**FLAGGED (D-06 — dead code preserved):** the loader always returns an empty collection (never null) when no
providers are configured, so this null guard is effectively unreachable for the empty case. The real
"no active provider" guard is BR-SHIP-006. Preserved as-is, not silently removed. See clarification item CI-10.
**Data Dependencies:**
- Reads: configured shipping-module collection (store-scoped, encrypted at rest)
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
| Error paths | 1 | 1 | OK (dead branch, flagged) |
**Preservation:** FLAGGED (dead-code branch preserved)

**Concrete Example:**
- Context: store with a corrupt/absent module collection
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"US"},"items":[...]}`
- Success: (normal path) quote proceeds when a module collection exists
- Error Input: (no active module — see BR-SHIP-006) `POST /api/v1/shipping/quotes {...}`
- Error Output: `200 {"returnCode":"NO_SHIPPING_MODULE_CONFIGURED","options":null}`

---

---

### BR-SHIP-027: Custom weight-based region eligibility — the destination country must map to a configured region (dead shippingBasisType read preserved)

**Source Reference:** `CustomWeightBasedShippingQuote.java:getShippingQuotes:97-115`; SPI `ShippingQuoteModule.java:getShippingQuotes`
**Discovery Method:** Direct Source Read
**Statement:** The custom weight-based provider will only quote a destination whose country belongs to one of the store's configured shipping regions. If no configured region contains the destination country, the provider returns no option.
**Intent:** Validation
**Logic:**
```
basisType = shippingConfiguration.shippingBasisType   // READ but never used (dead)
for region in configuration.regions:
    for countryCode in region.countries:
        if countryCode == destination.countryCode:
            <compute weight & price for this region>   // BR-SHIP-028/029
if no region matched: return null   // → NO_SHIPPING_TO_SELECTED_COUNTRY upstream (BR-SHIP-013)
```
**FLAGGED (D-06 — dead read preserved):** the provider reads the shipping basis type but never uses it.
Preserved; see CI-09.
**Data Dependencies:**
- Reads: region country lists, destination country code, (dead) shipping basis type
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (matched / null) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (dead read flagged) |
**Preservation:** FLAGGED (unused basis-type read preserved)

**Concrete Example:**
- Context: region NA covers ["US","CA"]
- Input: `POST /api/v1/shipping/quotes {"delivery":{"countryCode":"CA"},"items":[...]}`
- Success: region NA matched, weight/price computed
- Error Input: destination FR, no region covers FR
- Error Output: provider returns no option → `200 {"returnCode":"NO_SHIPPING_TO_SELECTED_COUNTRY"}`

---

---

