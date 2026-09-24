# Dependencies: catalog (MS-04)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-04 is the SOURCE + documented domain events.
> All request/response shapes below are copied from the provider's `04-api-contract.yaml`.

## Services Consumed

### content-cms (MS-11) — sync REST

catalog keeps product-image and digital-file **metadata + a reference blob key** but delegates the
**bytes** to content-cms (BV-5). Image/file uploads, and cascade cleanup on product delete, are
content-cms calls under the store namespace.

#### Call: Store product image bytes
- **Triggered by:** BR-CATPROD-005 (an image is added when it carries data and has no identity, otherwise updated)
- **Method:** POST (multipart/form-data)
- **Path:** `/api/v1/content/stores/{storeCode}/images`
- **Provider operationId:** `uploadImages`
- **Headers:**
  - x-tenant-id: {propagated from request context}
  - x-store-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Request body (multipart):**
  ```
  fileType: "Product"       # FileContentType — Product / ProductLarge
  files: [<binary>, ...]    # FileUploadRequest.files
  ```
- **Success response:** `201`
  ```json
  { "stored": ["prod-10-front.jpg"], "fileType": "Product" }
  ```
  catalog records `stored[]` as the image blob key(s) on its own product-image rows.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 400 | Bad file | Return 422 to caller; do not persist the image metadata |
  | 422 | Validation failed | Same as 400 |
  | 500 | content-cms error | Retry (see resilience); on exhaustion, do not persist metadata |
- **Resilience:**
  - Timeout: 10s
  - Retries: 3 (exponential backoff 2s/4s/8s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: abort the image save; the product row keeps its prior images

#### Call: Remove product image / digital-file bytes on product delete
- **Triggered by:** BR-CATPROD-006 (deleting a product cascades dependents — "Calls: CMS file removal")
- **Method:** DELETE
- **Path:** `/api/v1/content/stores/{storeCode}/files/{fileName}` (static/digital) and image variants under `/stores/{storeCode}/images`
- **Provider operationId:** `removeStaticFile` (digital file) / image removal via the store image namespace
- **Headers:** x-tenant-id, x-store-id, Authorization: Bearer {service token}
- **Success response:** `204`
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Already removed | Treat as success; continue the product-delete cascade |
  | 500 | content-cms error | Retry; on exhaustion, record an orphan-cleanup task (do not block the delete) |
- **Resilience:** Timeout 10s; Retries 3 (2s/4s/8s); circuit breaker 5/30s; Fallback: complete the local delete and enqueue orphan blob cleanup (non-blocking).

#### Call: Store a downloadable (digital) product file
- **Triggered by:** BR-CATPROD-017 (attaching a downloadable file marks the product virtual)
- **Method:** POST (multipart/form-data)
- **Path:** `/api/v1/content/stores/{storeCode}/files`
- **Provider operationId:** `uploadStaticFiles`
- **Headers:** x-tenant-id, x-store-id, Authorization: Bearer {service token}
- **Request body (multipart):**
  ```
  fileType: "ProductDigital"
  files: [<binary>]
  ```
- **Success response:** `201`
  ```json
  { "stored": ["manual.pdf"], "fileType": "ProductDigital" }
  ```
  catalog then sets the product `virtual` and records the digital-file blob key.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 409 | Conflict (already attached) | Surface 409 to caller |
  | 422 | Validation failed | Return 422; do not mark the product virtual |
  | 500 | content-cms error | Retry; on exhaustion, do not mark the product virtual |
- **Resilience:** Timeout 10s; Retries 3 (2s/4s/8s); circuit breaker 5/30s; Fallback: abort the attach; product remains non-virtual.

#### Call: Remove a downloadable (digital) product file
- **Triggered by:** BR-CATPROD-018 (removing a downloadable file — "Calls: content-store file removal")
- **Method:** DELETE
- **Path:** `/api/v1/content/stores/{storeCode}/files/{fileName}`
- **Provider operationId:** `removeStaticFile`
- **Headers:** x-tenant-id, x-store-id, Authorization: Bearer {service token}
- **Success response:** `204`
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Already removed | Treat as success; clear the local blob key |
  | 500 | content-cms error | Retry; on exhaustion, enqueue orphan cleanup |
- **Resilience:** Timeout 10s; Retries 3 (2s/4s/8s); circuit breaker 5/30s; Fallback: clear the local key and enqueue orphan cleanup.

### reference-data (MS-01) — sync REST  ⚠️ NOT BACKED BY A RULE (see GAPS)

The graph carries a `CALLS` edge MS-04 → MS-01, but no catalog rule performs a reference-data read.
Catalog handles locale via a local `languageCode` / `LANGUAGE_ID` on descriptions and `region` on
availabilities (e.g. BR-CATPROD-013) — it does NOT resolve or validate codes against the kernel.
**No synchronous call to reference-data is modeled.** See GAPS.

## Events Published

- **`catalog.product.indexed`** — an INTERNAL search-index signal (BR-CATPROD-001/011/012), consumed
  by the catalog's own search subsystem, not by another SAAM microservice. Not a cross-service domain
  event; recorded here for completeness only.

## Events Consumed

- **`merchant.deleted`** (from MS-03) — catalog owns store-scoped products/categories/manufacturers/
  options; on store decommission it purges that store's catalog (BR-MS-LIFE-002 fan-out consumer).
  Inbound event, not an outgoing call.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync calls): **1 provider** (content-cms), 4 calls.
- Integration count implied by MS-04 rules: **1** — content-cms (BR-CATPROD-005/006/017/018). Plus the internal `catalog.product.indexed` search event (not a cross-service edge). reference-data = 0.
- **Status: MATCH on content-cms (1 = 1); MISMATCH vs the graph on reference-data** (edge present, no backing rule).

## GAPS

1. **MS-04 → MS-01 (reference-data) edge is spurious.** No catalog rule reads reference-data; locale is
   handled locally. **Action:** human / Phase-2 to remove the edge or add a code-validation BR-ID if
   desired. Do NOT fabricate a call. **Status: GAP.**
