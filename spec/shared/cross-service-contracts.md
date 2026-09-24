# Cross-Service Contracts — Shopizer Modernization

> **Generated in Phase 4 Stage 1.5** (Consumer-Provider Contract Reconciliation).
> One row per SYNCHRONOUS consumer→provider call. Each row was verified by opening the provider's
> `04-api-contract.yaml` and confirming the exact path + request/response schema fields exist.
> **Column order is FIXED** (the graph importer `import_specs.py` parses it to annotate CALLS edges):
> `Consumer | Provider | Endpoint | Request Shape | Response Shape | Status`.
> Status ∈ `OK | RECONCILED | GAP`. **Any `GAP` blocks the P4 exit gate.**
>
> Asynchronous edges (payment↔order, store decommission fan-out) are NOT in this table — they are
> covered by `spec/shared/event-schemas/`. Payment→order is realized as events, not a sync call.

## Synchronous cross-service call table

| Consumer | Provider | Endpoint | Request Shape | Response Shape | Status |
|----------|----------|----------|---------------|----------------|--------|
| MS-06 cart | MS-04 catalog | GET /api/v1/catalog/products/{id} (getProduct) | path {id} | Product{id,sku,available,visible,virtual,shippable,free} | OK |
| MS-06 cart | MS-04 catalog | GET /api/v1/catalog/products/{id}/final-price (getFinalPrice) | path {id} | FinalPrice{finalPrice,originalPrice,discountedPrice,defaultPrice,discounted,discountPercent} | OK |
| MS-06 cart | MS-04 catalog | POST /api/v1/catalog/products/{id}/final-price (getFinalPriceForAttributes) | FinalPriceRequest{selectedAttributeIds[]} | FinalPrice{finalPrice,...} | OK |
| MS-06 cart | MS-04 catalog | GET /api/v1/catalog/products/{id}/attributes (listProductAttributes) | path {id}, ?languageCode | AttributeListResponse{items[Attribute{id,...}]} | OK |
| MS-06 cart | MS-09 order | POST /api/v1/orders/calculate-total (calculateOrderTotal) | CalculateOrderTotalRequest{cartCode,items[OrderLineItem{sku,productName,unitPrice,quantity}],shipping,customer} | OrderTotalSummary{subTotal,taxTotal,total,totals[OrderTotalLine{code,value,sortOrder}]} | OK |
| MS-05 customer | MS-06 cart | POST /api/v1/carts/merge (mergeCarts) | MergeCartsRequest{userCartCode,sessionCartCode,customerId} | Cart{id,code,storeId,customerId,quantity,items} | OK |
| MS-05 customer | MS-01 reference-data | GET /api/v1/reference/countries/{isoCode} (getCountry) | path {isoCode} | Country{isoCode,supported,name} | OK |
| MS-05 customer | MS-01 reference-data | GET /api/v1/reference/zones/{code} (getZone) | path {code} | Zone{code,countryIsoCode,id,name} | OK |
| MS-03 merchant-store | MS-01 reference-data | GET /api/v1/reference/countries/{isoCode}/zones (listCountryZones) | path {isoCode}, ?language | ZoneListResponse{items[Zone{code,countryIsoCode,id,name}]} | RECONCILED |
| MS-03 merchant-store | MS-01 reference-data | GET /api/v1/reference/currencies/{code} (getCurrency) | path {code} | Currency{code,name,supported} | RECONCILED |
| MS-03 merchant-store | MS-01 reference-data | GET /api/v1/reference/languages/{code} (getLanguage) | path {code} | Language{code,sortOrder} | RECONCILED |
| MS-03 merchant-store | MS-11 content-cms | POST /api/v1/content/stores/{storeCode}/logo (storeStoreLogo) | multipart LogoUploadRequest{file} | FileUploadResponse{stored[],fileType} | GAP |
| MS-03 merchant-store | MS-11 content-cms | DELETE /api/v1/content/stores/{storeCode}/logo (removeStoreLogo) | path {storeCode}, ?fileName | 204 (no body) | GAP |
| MS-04 catalog | MS-11 content-cms | POST /api/v1/content/stores/{storeCode}/images (uploadImages) | multipart FileUploadRequest{fileType,files[]} | FileUploadResponse{stored[],fileType} | OK |
| MS-04 catalog | MS-11 content-cms | POST /api/v1/content/stores/{storeCode}/files (uploadStaticFiles) | multipart FileUploadRequest{fileType,files[]} | FileUploadResponse{stored[],fileType} | OK |
| MS-04 catalog | MS-11 content-cms | DELETE /api/v1/content/stores/{storeCode}/files/{fileName} (removeStaticFile) | path {storeCode,fileName} | 204 (no body) | OK |
| MS-08 shipping | MS-04 catalog | GET /api/v1/catalog/products/{id}/final-price (getFinalPrice) | path {id} | FinalPrice{finalPrice,...} | OK |
| MS-08 shipping | MS-04 catalog | GET /api/v1/catalog/products/{id} (getProduct) | path {id} | Product{id,sku,virtual,shippable,...} | OK |
| MS-09 order | MS-07 tax | POST /api/v1/tax/calculate (calculateTax) | TaxCalculationRequest{customer{billing,delivery},store,items[{unitPrice,quantity,taxClassCode}],shipping,languageId,taxBasis} | TaxCalculationResponse{taxLines[{code,label,rate,amount}]} (nullable) | OK |
| MS-09 order | MS-08 shipping | GET /api/v1/shipping/configuration (getShippingConfiguration) | (headers only) | ShippingConfiguration{handlingFees,taxOnShipping,...} | OK |
| MS-09 order | MS-08 shipping | POST /api/v1/shipping/quotes (computeShippingQuote) | ShippingQuoteRequest{delivery{countryCode,name},items[ShippingItem{productId,quantity,finalPrice,weight,height,length,width,virtual,shippable}],languageCode} | ShippingQuote{shippingModuleCode,options[ShippingOption],selectedOption,returnCode,freeShipping,handlingFees,applyTaxOnShipping} | OK |
| MS-09 order | MS-10 payment | POST /api/v1/payments/process (processPayment) | ProcessPaymentRequest{orderId,moduleName,paymentType,amount,card{number,type,expMonth,expYear,cardOwner}} | Transaction{transactionId,orderId,amount,currency,transactionType,paymentType,eventPublished,persisted} | OK |
| MS-09 order | MS-10 payment | POST /api/v1/payments/orders/{orderId}/capture (capturePayment) | path {orderId} | Transaction{transactionId,transactionType,eventPublished} | OK |
| MS-09 order | MS-10 payment | POST /api/v1/payments/orders/{orderId}/refund (refundPayment) | path {orderId}, RefundRequest{amount} | Transaction{transactionId,transactionType,eventPublished} | OK |
| MS-09 order | MS-06 cart | GET /api/v1/carts/{code} (getCart) | path {code} | Cart{id,code,storeId,customerId,quantity,items} | OK |
| MS-09 order | MS-06 cart | DELETE /api/v1/carts/{code} (deleteCart) | path {code} | 204 (no body) | OK |
| MS-09 order | MS-05 customer | POST /api/v1/customers (createCustomer) | CreateCustomerRequest{emailAddress,billing,delivery,...} | Customer{id,storeId,emailAddress,...} | OK |
| MS-09 order | MS-05 customer | GET /api/v1/customers/{id} (getCustomer) | path {id} | Customer{id,storeId,emailAddress,...} | OK |
| MS-09 order | MS-01 reference-data | GET /api/v1/reference/countries/{isoCode}/name (getCountryName) | path {isoCode}, ?language | NameResponse{value} | OK |
| MS-09 order | MS-01 reference-data | GET /api/v1/reference/zones/{code}/name (getZoneName) | path {code}, ?language | NameResponse{value} | OK |
| MS-09 order | MS-03 merchant-store | GET /api/v1/stores/{storeCode} (store read) | path {storeCode} | MerchantStore{code,currencyCode,defaults} | OK |
| MS-09 order | MS-11 content-cms | GET /api/v1/content/stores/{storeCode}/files/{fileName} (digital download — candidate) | path {storeCode,fileName} | file bytes | GAP |
| MS-11 content-cms | MS-04 catalog | *(featured-items — no endpoint; scoped out)* | — | — | GAP |
| MS-07 tax | MS-01 reference-data | *(no call — jurisdiction codes are request inputs)* | — | — | GAP |
| MS-08 shipping | MS-01 reference-data | *(no call — country codes are request/config inputs)* | — | — | GAP |
| MS-04 catalog | MS-01 reference-data | *(no call — locale handled locally by languageCode/region)* | — | — | GAP |

### Status legend
- **OK** — the graph edge is backed by a consumer BR-ID AND the provider contract exposes the exact
  path + shapes the consumer needs. No action.
- **RECONCILED** — the call is modeled here (provider contract confirms it), but the consumer's backing
  rule framed it as validation rather than an explicit call. Modeled shape matches the provider; no
  invented fields. (Recorded so a later sweep does not re-flag.)
- **GAP** — a divergence a human must resolve before the P4 exit gate: a graph edge with no backing
  rule/endpoint (spurious edge), a spec-backed call with a missing graph edge, or a needed shape the
  provider does not expose.

## GAP register — RESOLVED (human signal 2026-09-19; edges fixed in graph)

| # | Edge | Nature of gap | Resolution applied |
|---|------|---------------|--------------------|
| G-1 | MS-03 → MS-11 (logo bytes) | Spec-backed (BR-MS-BRAND-001) + provider endpoints exist, but the graph CALLS edge was MISSING. | **ADDED** the merchant-store → content-cms CALLS edge. Contract + shapes already agreed — no shape change. ✅ RESOLVED |
| G-2 | MS-07 → MS-01 | Spurious edge — jurisdiction codes arrive in the `/calculate` request. | **REMOVED** the tax → reference-data edge. ✅ RESOLVED |
| G-3 | MS-08 → MS-01 | Spurious edge — country codes are request/config values. | **REMOVED** the shipping → reference-data edge. ✅ RESOLVED |
| G-4 | MS-04 → MS-01 | Spurious edge — catalog handles locale locally. | **REMOVED** the catalog → reference-data edge. ✅ RESOLVED |
| G-5 | MS-11 → MS-04 | Spurious/scoped-out — content-cms is inbound-only; featured-items is MS-04. | **REMOVED** the content-cms → catalog edge. ✅ RESOLVED |
| G-6 | MS-09 → MS-11 (digital download) | Weakly backed — concrete provider path unconfirmed. | **CONFIRMED: order delegates via catalog's digital-file resolution (blob_key, BV-5), not a direct content-cms read.** Removed the direct MS-09→MS-11 candidate edge; no direct order→content-cms path pinned. ✅ RESOLVED |

All six GAPs were graph/scope reconciliations, not shape mismatches. Post-fix the graph has 16 CALLS
edges (was 20). No consumer needed a shape the provider failed to expose; no path or field was invented.
**The P4 exit-gate cross-service-contract blocker is cleared.**

## Per-service integration-dimension reconciliation

Comparison of the sync integration count written into each service's `05-dependencies.md` against the
count implied by that service's rules (Logic / Side Effects "Calls"/"Publishes"/"Integrations").

| Service | Sync providers in 05-dependencies | Events pub / consumed | Rules-implied integrations | Reconciliation |
|---------|-----------------------------------|-----------------------|----------------------------|----------------|
| MS-01 reference-data | 0 | 0 / 0 | 0 | MATCH (leaf) |
| MS-02 identity-admin | 0 | 0 / 0 (consumes merchant.deleted) | 0 | MATCH (self-contained; OIDC is infra) |
| MS-03 merchant-store | 2 (reference-data, content-cms) | 1 pub (merchant.deleted) / 0 | 2 + 1 event (BR-MS-FIELD-001/002, BR-MS-BRAND-001, BR-MS-LIFE-002) | MATCH — but content-cms edge missing from graph (G-1) |
| MS-04 catalog | 1 (content-cms) | internal search event / 0 | 1 (BR-CATPROD-005/006/017/018) | MATCH — graph shows a spurious reference-data edge (G-4) |
| MS-05 customer | 2 (cart, reference-data) | 0 / 0 | 2 (BR-CUST-022, BR-CUST-021) | MATCH |
| MS-06 cart | 2 (catalog, order) | 0 / 0 | 2 (BR-CART-007..010/018/023/024; BR-CART-014/016) | MATCH |
| MS-07 tax | 0 | 0 / 0 | 0 (jurisdiction = request inputs) | MATCH on rules; graph edge spurious (G-2) |
| MS-08 shipping | 1 (catalog) | 0 / 0 | 1 (BR-SHIP-013/020) | MATCH; graph reference-data edge spurious (G-3) |
| MS-09 order | 7 (tax, shipping, payment, cart, customer, reference-data, merchant-store) + 1 candidate (content-cms) | 1 pub (order.placed) / 2 consumed (payment.captured, payment.refunded) | 7 named services + email/invoice/PSP externals + generic content | MATCH on 7 + payment events; content-cms weakly backed (G-6) |
| MS-10 payment | 0 sync | 2 pub (payment.captured, payment.refunded) / 0 | 2 event publishes (BR-PAY-006/007, BR-PAY-015); no sync order write (BV-2) | MATCH — order edge correctly realized as events |
| MS-11 content-cms | 0 | 0 / 0 | 0 (inbound-only byte provider) | MATCH on rules; graph catalog edge spurious (G-5) |

No service's rules imply MORE cross-service calls than its `05-dependencies.md` captures (no under-
capture). The only divergences are graph edges that are spurious (G-2/G-3/G-4/G-5), missing (G-1), or
weakly backed (G-6) — all recorded in the GAP register for human/Phase-2 reconciliation.
