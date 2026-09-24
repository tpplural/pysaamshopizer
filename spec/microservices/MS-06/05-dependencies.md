# Dependencies: cart (MS-06)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-06 is the SOURCE + documented domain events.
> All request/response shapes below are copied from the provider's `04-api-contract.yaml`.

## Services Consumed

### catalog (MS-04) — sync REST

Adding / repricing a line requires the product to exist, to belong to the cart's store, to yield a
price snapshot, and (for selected attributes) to expose those attributes. These are catalog reads.
The cart keeps only a per-line **subtotal preview**; it owns no product/price data.

#### Call: Product existence + store guard + disposition flags
- **Triggered by:** BR-CART-007 (adding an item requires the product to exist), BR-CART-008 (an item must belong to the cart's store), BR-CART-024 (shipping-eligibility / free-cart derivations use `virtual`/`shippable`)
- **Method:** GET
- **Path:** `/api/v1/catalog/products/{id}`
- **Provider operationId:** `getProduct`
- **Headers:**
  - x-tenant-id: {propagated from request context}
  - x-store-id: {propagated}
  - x-correlation-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Success response:** `200` (`Product`)
  ```json
  { "id": "prod-10", "sku": "SKU-1", "available": true, "visible": true,
    "virtual": false, "shippable": true, "free": false }
  ```
  A `404` (unknown product) → reject the add (422). Store mismatch is enforced with the store-scoped
  read; `virtual`/`shippable`/`free` feed BR-CART-024 eligibility derivation.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Product not found | Reject the add / drop the obsolete line on read (422 or line cleanup, BR-CART-021) |
  | 500 | catalog error | Retry (see resilience); on exhaustion return `502` |
- **Resilience:**
  - Timeout: 3s
  - Retries: 2 (exponential backoff 1s/2s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: reject the mutation with `502 BadGateway` (pricing/product upstream unavailable)

#### Call: Product price snapshot / reprice
- **Triggered by:** BR-CART-009 (a line captures a unit-price snapshot when added), BR-CART-018 (updating a line re-prices it), BR-CART-023 (session items are re-validated and re-priced during merge)
- **Method:** GET (default attributes) / POST (selected attributes)
- **Paths:**
  - GET `/api/v1/catalog/products/{id}/final-price` — `getFinalPrice`
  - POST `/api/v1/catalog/products/{id}/final-price` — `getFinalPriceForAttributes`
- **Headers:** x-tenant-id, x-store-id, x-correlation-id, Authorization: Bearer {service token}
- **Request body (POST variant):** (`FinalPriceRequest`)
  ```json
  { "selected_attribute_ids": ["attr-100", "attr-205"] }
  ```
- **Success response:** `200` (`FinalPrice`)
  ```json
  { "final_price": 13.00, "original_price": 15.00, "discounted_price": 13.00,
    "default_price": true, "discounted": true, "discount_percent": 13 }
  ```
  cart stores `final_price` as the line `unit_price` snapshot (BR-CART-009); `sub_total = unit_price × quantity` (preview only, BR-CART-013).
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Product/price not found | Reject the add or drop the line on reprice (BR-CART-021) |
  | 500 | catalog error | Retry; on exhaustion `502` |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: `502 BadGateway`.

#### Call: Validate a line's selected attributes belong to the product
- **Triggered by:** BR-CART-010 (selected attributes must belong to the product; others are ignored)
- **Method:** GET
- **Path:** `/api/v1/catalog/products/{id}/attributes`
- **Provider operationId:** `listProductAttributes`
- **Headers:** x-tenant-id, x-store-id, x-correlation-id, Authorization: Bearer {service token}
- **Success response:** `200` (`AttributeListResponse` → `items[].id`). cart keeps only attribute ids
  present in the product's attribute set; unknown selected attributes are ignored (BR-CART-010).
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Product not found | Reject the add (422) |
  | 500 | catalog error | Retry; on exhaustion `502` |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: `502 BadGateway`.

### order (MS-09) — sync REST

The authoritative grand total (subtotal roll-up + tax + shipping + promotions) is DELEGATED to the
order service (BV-3). The cart keeps only a per-line subtotal preview; it calls order for the total.

#### Call: Compute the authoritative cart total
- **Triggered by:** BR-CART-014 (authoritative cart total is delegated to the order service, BV-3), BR-CART-016 (every mutation recalculates and re-persists the cart)
- **Method:** POST
- **Path:** `/api/v1/orders/calculate-total`
- **Provider operationId:** `calculateOrderTotal`
- **Headers:**
  - x-tenant-id: {propagated}
  - x-store-id: {propagated}
  - x-correlation-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Request body:** (`CalculateOrderTotalRequest`)
  ```json
  { "cart_code": "CART-USER-1",
    "items": [ { "sku": "SKU-1", "product_name": "Widget", "unit_price": 13.00, "quantity": 2 } ],
    "shipping": null,
    "customer": { "customer_id": "CUST-9", "zone": "QC", "country": "CA", "state_province": "QC" } }
  ```
- **Success response:** `200` (`OrderTotalSummary`)
  ```json
  { "sub_total": 26.00, "tax_total": 3.90, "total": 29.90,
    "totals": [ { "code": "order.total.subtotal", "value": 26.00, "sort_order": 5 },
                { "code": "order.total.total", "value": 29.90, "sort_order": 300 } ] }
  ```
  cart maps `sub_total` → `Cart.sub_total` (display preview), `total` → `Cart.total`, and `totals[]`
  → `CartSummary.totals[]` (`{code, value}`). The cart's own line subtotals remain preview-only.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 422 | Invalid basket | Surface a `422` on the cart summary |
  | 502 | tax/shipping upstream failed inside order | Surface `502 BadGateway` on the cart summary |
  | 500 | order error | Retry (see resilience); on exhaustion `502` |
- **Resilience:**
  - Timeout: 8s (order internally calls tax + shipping, so allow more headroom than a leaf read)
  - Retries: 2 (exponential backoff 2s/4s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: return the cart with the per-line **subtotal preview only** and `total: null`
    (`CartSummary` degrades to the preview; the authoritative total is unavailable until order recovers)

## Events Published

None. cart does not publish domain events. (Cart teardown at checkout is performed by MS-09 order
deleting the cart — BR-ORD-025 — not by a cart-emitted event.)

## Events Consumed

- **`merchant.deleted`** (from MS-03) — cart owns store-scoped carts; on store decommission it purges
  that store's carts (BR-MS-LIFE-002 fan-out consumer). Inbound event, not an outgoing call.

## Inbound (for reference — NOT this service's dependencies)

- **MS-05 customer** calls cart's `POST /carts/merge` (`mergeCarts`) on login (BR-CART-022/023 own the
  merge mechanics; MS-05 BR-CUST-022 is the caller). Documented here so the merge seam is visible from
  the cart side; it is modeled as an outgoing dependency in `MS-05/05-dependencies.md`.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync calls): **2 providers** (catalog, order), 4 call variants.
- Integration count implied by MS-06 rules: **2** — catalog reads (BR-CART-007/008/009/010/018/023/024), order total delegation (BR-CART-014/016).
- **Status: MATCH (2 = 2).**
