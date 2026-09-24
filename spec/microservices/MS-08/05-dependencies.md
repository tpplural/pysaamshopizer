# Dependencies: shipping (MS-08)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-08 is the SOURCE + documented domain events.
> All request/response shapes below are copied from the provider's `04-api-contract.yaml`.

## Services Consumed

### catalog (MS-04) — sync REST

The quote / packaging pipeline needs each shippable line's price and physical attributes, and must
skip virtual products. The product's final price and its `virtual`/`shippable` flags are catalog reads.

#### Call: Read a product's final price
- **Triggered by:** BR-SHIP-013 (order-total weight/price computation — `final_price = pricing.final_price(line.product)`)
- **Method:** GET
- **Path:** `/api/v1/catalog/products/{id}/final-price`
- **Provider operationId:** `getFinalPrice`
- **Headers:**
  - x-tenant-id: {propagated from request context}
  - x-correlation-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Success response:** `200`
  ```json
  { "final_price": 13.00, "original_price": 15.00, "discounted_price": 13.00,
    "default_price": true, "discounted": true, "discount_percent": 13 }
  ```
  shipping uses `final_price` as the line value for free-shipping-threshold and price-based options.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Product not found | Treat the line as unpriceable; surface `502 PricingUnavailable` on the quote |
  | 500 | catalog error | Retry (see resilience); on exhaustion `502` |
- **Resilience:**
  - Timeout: 3s
  - Retries: 2 (exponential backoff 1s/2s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: return the quote with `quoteError` / `502 PricingUnavailable` (BR-SHIP-013 error path)

#### Call: Read a product (virtual / shippable flags + weight/dimension attributes)
- **Triggered by:** BR-SHIP-020 (virtual products are excluded from packaging)
- **Method:** GET
- **Path:** `/api/v1/catalog/products/{id}`
- **Provider operationId:** `getProduct`
- **Headers:** x-tenant-id, x-correlation-id, Authorization: Bearer {service token}
- **Success response:** `200`
  ```json
  { "id": "prod-10", "sku": "SKU-1", "available": true, "visible": true,
    "virtual": false, "shippable": true, "free": false }
  ```
  A product with `virtual == true` is skipped by packaging (BR-SHIP-020). Physical weight/dimensions
  used by the box/weight-based engine arrive as `ShippingItem` attributes on the incoming quote request
  (`weight`, `height`, `length`, `width`); the catalog product read supplies the `virtual`/`shippable`
  disposition.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Product not found | Exclude the line from packaging; log |
  | 500 | catalog error | Retry; on exhaustion `502` |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: exclude the unresolved line and continue the quote where possible.

### reference-data (MS-01) — sync REST  ⚠️ NOT BACKED BY A RULE (see GAPS)

The graph carries a `CALLS` edge MS-08 → MS-01, but no shipping rule performs a reference-data read.
Destination country comparisons (BR-SHIP-002/003/004/009) use `delivery.country_code` from the request
and the store's supported-countries config — country codes are **request/config values**, not kernel
lookups. **No synchronous call to reference-data is modeled.** See GAPS.

## Events Published

None. shipping is a synchronous calculator (quote / packaging / config) only.

## Events Consumed

- **`merchant.deleted`** (from MS-03) — shipping owns store-scoped shipping configuration, supported
  countries, and weight-based regions; on store decommission it purges that store's data
  (BR-MS-LIFE-002 fan-out consumer). Inbound event, not an outgoing call.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync calls): **1 provider** (catalog), 2 calls.
- Integration count implied by MS-08 rules: **1** — catalog (BR-SHIP-013 final price, BR-SHIP-020 virtual flag; BR-SHIP-020 Integrations 1/1). reference-data = 0 (codes are inputs).
- **Status: MATCH on catalog (1 = 1); MISMATCH vs the graph on reference-data** (edge present, no backing rule).

## GAPS

1. **MS-08 → MS-01 (reference-data) edge is spurious.** No shipping rule reads reference-data;
   `country_code` is a request/config value. **Action:** human / Phase-2 to remove the edge or add a
   country-validation BR-ID if inbound-code validation is desired. Do NOT fabricate a call.
   **Status: GAP.**
