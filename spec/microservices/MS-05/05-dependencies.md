# Dependencies: customer (MS-05)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-05 is the SOURCE + documented domain events.
> All request/response shapes below are copied from the provider's `04-api-contract.yaml`.

## Services Consumed

### cart (MS-06) — sync REST

On login, an anonymous session cart is merged into the shopper's cart. customer OWNS the login-side
trigger; cart OWNS the merge mechanics (MS-06 BR-CART-022/023). customer calls cart's merge endpoint.

#### Call: Merge the session cart into the shopper's cart on login
- **Triggered by:** BR-CUST-022 (on login, an anonymous session cart is merged into the shopper's cart)
- **Method:** POST
- **Path:** `/api/v1/carts/merge`
- **Provider operationId:** `mergeCarts`
- **Headers:**
  - x-tenant-id: {propagated from request context}
  - x-store-id: {propagated}
  - x-correlation-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Request body:** (`MergeCartsRequest`)
  ```json
  { "user_cart_code": "CART-USER-1", "session_cart_code": "CART-SESSION-9", "customer_id": "CUST-9" }
  ```
- **Success response:** `200` (`Cart`)
  ```json
  { "id": "…", "code": "CART-USER-1", "store_id": "…", "customer_id": "CUST-9",
    "quantity": 3, "sub_total": null, "total": null, "items": [ … ] }
  ```
  customer returns the merged cart's `code` to the client as `LoginResponse.cart_code`.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | A referenced cart is gone | Skip the merge; log; login still succeeds |
  | 422 | Merge rule violation | Skip the merge; log; login still succeeds |
  | 500 | cart error | Retry (see resilience); on exhaustion skip merge, login still succeeds |
- **Resilience:**
  - Timeout: 5s
  - Retries: 2 (exponential backoff 1s/2s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: login succeeds WITHOUT the merge (the merge is best-effort; the shopper keeps the user cart untouched)

### reference-data (MS-01) — sync REST

Customer addresses supply a country and a state/zone code; each supplied code must resolve to an
existing reference-data entry, else the operation is rejected. customer stores codes only, no cross-
service foreign key (ADR-006).

#### Call: Validate an address country / zone code
- **Triggered by:** BR-CUST-021 (an address country/zone code must correspond to an existing reference-data entry)
- **Method:** GET
- **Paths (provider operationIds):**
  - `/api/v1/reference/countries/{isoCode}` — `getCountry`
  - `/api/v1/reference/zones/{code}` — `getZone`
- **Headers:**
  - x-correlation-id: {propagated}
  - Authorization: Bearer {service-to-service token}
  - (reference-data is global; it does NOT require x-tenant-id)
- **Success response:** `200`
  ```json
  { "iso_code": "CA", "supported": true, "name": "Canada" }
  ```
  A `404` means the submitted code is unknown → reject the create/update with a validation error.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Unknown country/zone code | Reject the customer create/update (422 "unknown country/zone") |
  | 500 | reference-data error | Retry; on exhaustion fail the operation with 503 |
- **Resilience:**
  - Timeout: 3s
  - Retries: 2 (exponential backoff 1s/2s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: reject the address save (do NOT persist an address with an unvalidated code)

## Events Published

None. customer does not publish domain events.

## Events Consumed

- **`merchant.deleted`** (from MS-03) — customer owns store-scoped shopper records; on store
  decommission it purges that store's customers (BR-MS-LIFE-002 fan-out consumer). Inbound event, not
  an outgoing call.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync calls): **2 providers** (cart, reference-data), 3 call variants.
- Integration count implied by MS-05 rules: **2** — cart merge (BR-CUST-022), reference-data address validation (BR-CUST-021).
- **Status: MATCH (2 = 2).**
