# Dependencies: merchant-store (MS-03)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-03 is the SOURCE + documented domain events.
> All request/response shapes below are copied from the provider's `04-api-contract.yaml`.

## Services Consumed

### reference-data (MS-01) — sync REST

merchant-store validates a store's `countryIso`, `zoneCode`, `currencyCode`, and `languageCode` as
cross-reference (xref) values against the reference-data kernel — the store persists codes only, no
cross-service foreign key (ADR-006).

> **Reconciliation note (partial edge):** The graph carries a `CALLS` edge MS-03 → MS-01. The backing
> rules (BR-MS-FIELD-001, BR-MS-FIELD-002) frame country/zone/currency/language as **presence and
> zone-resolution validation** rather than an explicit "call reference-data" step. Modeling the read
> here is the correct target design (validate the code exists before persisting the store). See the
> GAPS section — the rule wording is looser than the modeled call.

#### Call: Validate the store's country (and enumerate its zones)
- **Triggered by:** BR-MS-FIELD-002 (state/province must be resolvable — a zone for the country or a free-text state)
- **Method:** GET
- **Path:** `/api/v1/reference/countries/{isoCode}/zones?language={languageCode}`
- **Provider operationId:** `listCountryZones`
- **Headers:**
  - x-correlation-id: {propagated from request context}
  - Authorization: Bearer {service-to-service token}
  - (reference-data is global; it does NOT require x-tenant-id)
- **Success response:** `200`
  ```json
  { "items": [ { "code": "QC", "country_iso_code": "CA", "id": 12, "name": "Quebec" } ] }
  ```
  Store save is accepted when the submitted `zone_code` is among `items[].code`, OR when `items` is
  empty and a free-text `state_province` was supplied (BR-MS-FIELD-002).
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 400 | Bad language/iso | Reject store save with a validation error (422) to the admin |
  | 500 | reference-data error | Retry (see resilience); on exhaustion, fail the save with 503 |
- **Resilience:**
  - Timeout: 3s
  - Retries: 2 (exponential backoff 1s/2s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: reject the store save (do NOT persist a store with an unvalidated country/zone)

#### Call: Validate currency / language / country existence
- **Triggered by:** BR-MS-FIELD-001 (a store requires a complete identity, contact, locale, and currency set)
- **Method:** GET
- **Paths (provider operationIds):**
  - `/api/v1/reference/currencies/{code}` — `getCurrency`
  - `/api/v1/reference/languages/{code}` — `getLanguage`
  - `/api/v1/reference/countries/{isoCode}` — `getCountry`
- **Headers:** x-correlation-id, Authorization: Bearer {service token}
- **Success response:** `200` (the resolved `Currency` / `Language` / `Country`); `404` if the code is unknown.
  ```json
  { "code": "CAD", "name": "Canadian Dollar", "supported": true }
  ```
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Unknown code | Reject store save (422 "unknown currency/language/country") |
  | 500 | reference-data error | Retry; on exhaustion fail save with 503 |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: reject the save.

### content-cms (MS-11) — sync REST  ⚠️ EDGE MISSING FROM GRAPH (see GAPS)

merchant-store keeps only the store logo **filename** on its own row; the logo **bytes** are stored by
content-cms under the store's namespace (BV-5). This is a real, spec-backed cross-service call
(BR-MS-BRAND-001), but the corresponding `CALLS` edge (MS-03 → MS-11) is **absent from the graph** —
it is flagged for a human / Phase-2 edge fix rather than treated as authoritative here.

#### Call: Store the store logo bytes
- **Triggered by:** BR-MS-BRAND-001 (a store records its logo by filename while the image bytes live in content storage — upload branch)
- **Method:** POST (multipart/form-data)
- **Path:** `/api/v1/content/stores/{storeCode}/logo`
- **Provider operationId:** `storeStoreLogo`
- **Headers:**
  - x-tenant-id: {propagated}
  - x-store-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Request body (multipart):**
  ```
  file: <binary>            # LogoUploadRequest.file
  ```
- **Success response:** `201`
  ```json
  { "stored": ["logo.png"], "fileType": "Logo" }
  ```
  merchant-store then sets `merchant_store.store_logo = stored[0]` and updates the store row.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 400 | Bad file | Return 422 to admin; do not set logo filename |
  | 422 | Validation failed | Same as 400 |
  | 500 | content-cms error | Retry; on exhaustion, do NOT set the filename (store row unchanged) |
- **Resilience:** Timeout 10s; Retries 3 (2s/4s/8s); circuit breaker 5/30s; Fallback: abort logo update, store row keeps its previous logo filename (BR-MS-BRAND-001 error path).

#### Call: Remove the store logo bytes
- **Triggered by:** BR-MS-BRAND-001 (remove branch)
- **Method:** DELETE
- **Path:** `/api/v1/content/stores/{storeCode}/logo?fileName={storeLogo}`
- **Provider operationId:** `removeStoreLogo`
- **Headers:** x-tenant-id, x-store-id, Authorization: Bearer {service token}
- **Success response:** `204` (no content). merchant-store then clears `merchant_store.store_logo`.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Logo not found | Treat as already-removed; clear the local filename anyway |
  | 500 | content-cms error | Retry; on exhaustion, leave the filename set and surface 503 |
- **Resilience:** Timeout 10s; Retries 3 (2s/4s/8s); circuit breaker 5/30s; Fallback: leave the local logo filename unchanged.

## Events Published

### Publishes: `merchant.deleted`
- **Triggered by:** BR-MS-LIFE-002 (store decommission — event-driven cascade saga, R-06)
- **Channel:** `merchant.deleted`
- **Schema:** see `spec/shared/event-schemas/merchant.deleted.yaml`
  ```json
  { "merchantId": 42, "storeCode": "acme_store", "timestamp": "2026-01-01T12:00:00Z" }
  ```
- **Consumers:** MS-04 catalog, MS-05 customer, MS-07 tax, MS-08 shipping, MS-09 order, MS-10 payment,
  MS-11 content-cms, MS-02 identity-admin (each purges its own store-scoped data).
- **Guarantees:** at-least-once
- **Ordering:** by `merchantId`

## Events Consumed

None.

## Reconciliation (integration dimension)

- specIntegrations written into this file: **2 sync providers** (reference-data, content-cms) across 4 calls + **1 published event** (`merchant.deleted`).
- Integration count implied by MS-03 rules: reference-data validation (BR-MS-FIELD-001/002), content-cms logo put+delete (BR-MS-BRAND-001, Integrations 2/2), merchant.deleted publish (BR-MS-LIFE-002, Integrations 8/8 = 8 consumers).
- **Status: MATCH** on content-cms and the event; **reference-data is modeled slightly RICHER than the rules** (rules say "validate", this file makes it an explicit MS-01 read) — see GAPS.

## GAPS

1. **MS-03 → MS-11 (content-cms) edge missing from the graph.** BR-MS-BRAND-001 and MS-11's inbound
   endpoints `storeStoreLogo` / `removeStoreLogo` both exist, but no `CALLS` edge connects MS-03 to
   MS-11. **Action:** human / Phase-2 to add the edge. The call is modeled here from the real provider
   contract — no path/field was invented. **Status: GAP (blocks exit gate until the edge is added).**
2. **MS-03 → MS-01 (reference-data) is validation-framed, not an explicit call in the rules.**
   BR-MS-FIELD-001/002 require the codes to resolve but do not literally state a reference-data call.
   The modeled reads are the correct target behavior. **Status: GAP — confirm the modeled reads with a human (informational; low risk).**
