# Dependencies: order (MS-09)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-09 is the SOURCE + documented domain events.
> All request/response shapes below are copied from each provider's `04-api-contract.yaml`.
>
> **Architecture seams:** BV-1/ADR-001 — order OWNS the total; tax (MS-07) and shipping (MS-08) are
> synchronous stateless calculator reads folded into the owned computation. BV-2/ADR-003 — order
> CONSUMES `payment.captured` / `payment.refunded` (idempotent on `transaction_id`), and its charge is a
> synchronous call to payment as the checkout-saga CHARGE step (D-08 — saga, not 2PC).

## Services Consumed

### tax (MS-07) — sync REST (stateless calculator)

#### Call: Calculate tax over the order
- **Triggered by:** BR-ORD-004 (tax total lines — tax entry point, cross-service calculator)
- **Method:** POST
- **Path:** `/api/v1/tax/calculate`
- **Provider operationId:** `calculateTax`
- **Headers:**
  - x-tenant-id: {propagated}
  - x-store-id: {propagated}
  - x-correlation-id: {propagated}
  - Authorization: Bearer {service-to-service token}
- **Request body:** (`TaxCalculationRequest`)
  ```json
  { "customer": { "billing": { "country_id": 38, "zone_id": 12, "state": null },
                  "delivery": { "country_id": 38, "zone_id": 12, "state": null } },
    "store": { "country_id": 38, "zone_id": 12, "state_province": null },
    "items": [ { "unit_price": 49.95, "quantity": 2, "tax_class_code": "DEFAULT" } ],
    "shipping": { "shipping": 12.50, "handling": 3.00 },
    "language_id": 1, "tax_basis": "BillingAddress" }
  ```
- **Success response:** `200` (`TaxCalculationResponse`, or `null` when no tax applies)
  ```json
  { "tax_lines": [ { "code": "GST", "label": "GST", "rate": 5.0, "amount": 5.00 },
                  { "code": "QST", "label": "QST", "rate": 9.975, "amount": 9.975 } ] }
  ```
  order folds each `tax_lines[].label` + `amount` into its own TAX `OrderTotal` lines (BR-ORD-004).
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 422 | Invalid tax input | Surface `422` — total cannot be finalized |
  | 400 | Bad request | Surface `422`/`400` to the caller |
  | 500 | tax error | Retry (see resilience); on exhaustion `502 UpstreamError` (BR-ORD-004 error path) |
- **Resilience:**
  - Timeout: 4s
  - Retries: 2 (exponential backoff 1s/2s)
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: fail the total with `502 UpstreamError` — the order total is NOT finalized without the tax read (money-correctness over availability)

### shipping (MS-08) — sync REST (stateless calculator)

#### Call: Read the store's shipping configuration (handling-fee gate)
- **Triggered by:** BR-ORD-003 (handling fee line — conditional on the store shipping configuration)
- **Method:** GET
- **Path:** `/api/v1/shipping/configuration`
- **Provider operationId:** `getShippingConfiguration`
- **Headers:** x-tenant-id, x-correlation-id, Authorization: Bearer {service token}
- **Success response:** `200` (`ShippingConfiguration`) — order reads `handling_fees` and `tax_on_shipping`
  to decide whether the handling line applies (BR-ORD-003).
  ```json
  { "handling_fees": 3.00, "tax_on_shipping": true, "free_shipping_enabled": false }
  ```
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 500 | shipping error | Retry; on exhaustion treat handling as unconfigured (no handling line) |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: omit the handling line (degrade rather than fail the total, since handling is conditional).

#### Call: Compute a shipping quote (when order performs the quote)
- **Triggered by:** BR-ORD-024 / BR-ORD-030 (shipping quotation feeding the shipping total line, BR-ORD-002)
- **Method:** POST
- **Path:** `/api/v1/shipping/quotes`
- **Provider operationId:** `computeShippingQuote`
- **Headers:** x-tenant-id, x-correlation-id, Authorization: Bearer {service token}
- **Request body:** (`ShippingQuoteRequest`)
  ```json
  { "delivery": { "country_code": "CA", "name": "Home" },
    "items": [ { "product_id": "prod-10", "quantity": 2, "final_price": 49.95,
                 "weight": 1.2, "height": 5, "length": 10, "width": 8,
                 "virtual": false, "shippable": true } ],
    "language_code": "en" }
  ```
- **Success response:** `200` (`ShippingQuote`) — order reads `free_shipping`, the selected
  `options[].option_price`, `handling_fees`, and `apply_tax_on_shipping` and folds them into the shipping
  total line (BR-ORD-002).
  ```json
  { "shipping_module_code": "weightBased",
    "options": [ { "option_id": "std", "option_code": "STD", "option_name": "Standard", "option_price": 12.50 } ],
    "selected_option": { "option_id": "std", "option_price": 12.50 },
    "return_code": null, "free_shipping": false, "handling_fees": 3.00, "apply_tax_on_shipping": true }
  ```
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 422 | Invalid quote input | Surface `422` |
  | 500 | shipping error | Retry; on exhaustion `502 UpstreamError` |
- **Resilience:** Timeout 4s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: `502 UpstreamError` when a quote is required for the total; a degenerate/zero quote yields a zero shipping line (BR-ORD-002).

### payment (MS-10) — sync REST (checkout-saga CHARGE step)

The checkout charge is a synchronous, idempotent call to payment (saga CHARGE step, D-08). Settlement
facts return ASYNCHRONOUSLY via `payment.captured` / `payment.refunded` (see Events Consumed) — order
does NOT read order state back from payment.

#### Call: Charge the payment for an order
- **Triggered by:** BR-ORD-008 (order placement orchestration — SAGA step 1 CHARGE)
- **Method:** POST
- **Path:** `/api/v1/payments/process`
- **Provider operationId:** `processPayment`
- **Headers:**
  - x-tenant-id: {propagated}
  - x-store-id: {propagated}
  - idempotency-key: {checkout saga idempotency key — charge-vs-persist safety}
  - Authorization: Bearer {service-to-service token}
- **Request body:** (`ProcessPaymentRequest`)
  ```json
  { "order_id": "ORD-5001", "module_name": "authnet", "payment_type": "CreditCard",
    "amount": 130.38,
    "card": { "number": "…", "type": "Visa", "exp_month": "04", "exp_year": "2028", "card_owner": "A. Buyer" } }
  ```
  (The raw PAN is routed to payment only, NEVER persisted by order — see MS-09 domain model.)
- **Success response:** `200`/`201` (`Transaction`)
  ```json
  { "transaction_id": "TX-9001", "order_id": "ORD-5001", "amount": 130.38, "currency": "USD",
    "transaction_type": "AuthorizeCapture", "payment_type": "CreditCard",
    "event_published": "payment.captured", "persisted": true, "partial": false }
  ```
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 402 | Charge declined | Fail checkout with `402 PaymentRequired`; do NOT persist a settled order |
  | 422 | Invalid payment input | Surface `422` |
  | 502 | Gateway error | Retry the idempotent charge; on exhaustion fail checkout; reconciler resolves any orphan charge |
  | 500 | payment error | Same as 502 |
- **Resilience:**
  - Timeout: 15s (external gateway round-trip)
  - Retries: 2 on the SAME idempotency-key (exponential backoff 3s/6s) — safe because `/process` is idempotent on the key
  - Circuit breaker: open after 5 failures, half-open after 30s
  - Fallback: fail checkout; the reconciliation job (D-08 / Architecture §7) guarantees no PROCESSED order without a CAPTURED transaction and drives compensation for any stranded charge

#### Call: Capture a prior authorization (admin / delayed capture)
- **Triggered by:** BR-ORD-008 (delayed-capture path of the saga)
- **Method:** POST
- **Path:** `/api/v1/payments/orders/{orderId}/capture`
- **Provider operationId:** `capturePayment`
- **Headers:** x-tenant-id, x-store-id, Authorization: Bearer {service token}
- **Success response:** `200` (`Transaction`, `event_published: "payment.captured"`). Order state is
  applied when the `payment.captured` event is consumed — NOT from this response body.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 422 | No capturable transaction | Surface `422` |
  | 502 | Gateway error | Retry; on exhaustion surface `502` |
- **Resilience:** Timeout 15s; Retries 2 (3s/6s); circuit breaker 5/30s; Fallback: surface the error; settlement still arrives via `payment.captured` if the capture actually succeeded.

#### Call: Refund an order (admin refund delegates to payment)
- **Triggered by:** BR-ORD refund path (the admin `POST /{orderId}/refund` endpoint delegates settlement to payment; the order total decrement is applied on `payment.refunded`)
- **Method:** POST
- **Path:** `/api/v1/payments/orders/{orderId}/refund`
- **Provider operationId:** `refundPayment`
- **Headers:** x-tenant-id, x-store-id, Authorization: Bearer {service token}
- **Request body:** (`RefundRequest`)
  ```json
  { "amount": 50.00 }
  ```
- **Success response:** `200` (`Transaction`, `event_published: "payment.refunded"`). Order responds
  `202 Accepted` to its own caller; the total decrement + Refunded status are applied when
  `payment.refunded` is consumed.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 422 | Invalid refund | Surface `422` |
  | 502 | Gateway declined | No ledger row, no event → surface `502`; order stays unchanged |
- **Resilience:** Timeout 15s; Retries 2 (3s/6s); circuit breaker 5/30s; Fallback: surface `502`; order total is only decremented when `payment.refunded` is consumed.

### cart (MS-06) — sync REST

#### Call: Read the cart to convert to an order, and delete it on commit
- **Triggered by:** BR-ORD-021 (build order from the cart — cart is the source basket), BR-ORD-025 (checkout finalize — the cart is consumed/cleared)
- **Method:** GET (read) / DELETE (teardown)
- **Paths:**
  - GET `/api/v1/carts/{code}` — `getCart`
  - DELETE `/api/v1/carts/{code}` — `deleteCart`
- **Headers:** x-tenant-id, x-store-id, x-correlation-id, Authorization: Bearer {service token}
- **Success response:** GET `200` (`Cart` with `items[]`); DELETE `204`.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Cart gone/expired | Fail checkout with `410 Gone` (BR-ORD-026 timeout) |
  | 500 | cart error | Retry; on exhaustion fail checkout |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback for DELETE: cart teardown is best-effort post-commit — a failed delete does NOT roll back the placed order (enqueue a cleanup retry).

### customer (MS-05) — sync REST

#### Call: Ensure the customer exists at checkout
- **Triggered by:** BR-ORD-008 (ensure-customer step — `customerService.create(...)`), BR-ORD-025 (a new/volatile customer is provisioned on commit)
- **Method:** POST (create) / GET (lookup)
- **Paths:**
  - POST `/api/v1/customers` — `createCustomer`
  - GET `/api/v1/customers/{id}` — `getCustomer`
- **Headers:** x-tenant-id, x-store-id, x-correlation-id, Authorization: Bearer {service token}
- **Request body (create):** (`CreateCustomerRequest`) — `email_address` (+ optional billing/delivery `Address`).
- **Success response:** POST `201` (`Customer` with `id`); order sets `order.customer_id = customer.id`.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 422 | Invalid customer | Surface `422` on checkout |
  | 500 | customer error | Retry; on exhaustion fail checkout (customer must exist before persist) |
- **Resilience:** Timeout 4s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: fail the checkout (the order cannot be persisted without a customer id).

### reference-data (MS-01) — sync REST

#### Call: Resolve address country / zone / language for display
- **Triggered by:** BR-ORD-028 (address display + cross-store ownership guard uses country/zone/language reference)
- **Method:** GET
- **Paths:**
  - `/api/v1/reference/countries/{isoCode}/name?language={lang}` — `getCountryName`
  - `/api/v1/reference/zones/{code}/name?language={lang}` — `getZoneName`
  - `/api/v1/reference/languages/{code}` — `getLanguage`
- **Headers:** x-correlation-id, Authorization: Bearer {service token} (reference-data is global — no x-tenant-id)
- **Success response:** `200` (`NameResponse` `{value}` for the name endpoints; `Language` for language).
  These endpoints are fail-soft: the localized name, or the echoed input code if unresolved.
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 500 | reference-data error | Retry; on exhaustion fall back to the raw code (display-only, non-blocking) |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: display the raw country/zone code (reference names are cosmetic on the order, never block placement).

### merchant-store (MS-03) — sync REST

#### Call: Read the store for the cross-store guard and defaults
- **Triggered by:** BR-ORD-023 (store defaults — currency/measurement), BR-ORD-028 (cross-store ownership guard on confirmation/read)
- **Method:** GET
- **Path:** `/api/v1/stores/{storeCode}` — merchant-store `getStore` (store read)
- **Headers:** x-tenant-id, x-correlation-id, Authorization: Bearer {service token}
- **Success response:** `200` (the merchant store — `code`, `currency_code`, defaults). order uses it to
  seed order defaults (BR-ORD-023) and to enforce that a fetched order belongs to the acting store
  (BR-ORD-028 → `403 Forbidden` on mismatch).
- **Error handling:**
  | Status | Meaning | Action |
  |--------|---------|--------|
  | 404 | Store not found | `503 ServiceUnavailable` (dependency unavailable — BR-ORD integration path) |
  | 500 | store error | Retry; on exhaustion `503` |
- **Resilience:** Timeout 3s; Retries 2 (1s/2s); circuit breaker 5/30s; Fallback: use cached store defaults where available; otherwise fail the operation needing them.

### content-cms (MS-11) — ⚠️ generic "Content" integration only (see GAPS)

Digital-download delivery (BR-ORD-032) reads the product's downloadable file. The MS-09 rules describe
this as a **generic "Content integration"**, and the graph has an MS-09 → MS-11 edge, but no order rule
names content-cms (MS-11) explicitly, and the digital-file bytes are owned by catalog's blob key which
resolves to content-cms. Modeled here as the likely provider without inventing a path:

- **Would-be call:** GET `/api/v1/content/stores/{storeCode}/files/{fileName}` (content-cms static/digital file read) OR delegate through catalog's digital-file endpoint.
- **Triggered by:** BR-ORD-032 (download delivery — legacy IDOR + download-limit preserved and flagged)
- **Status:** modeled as a candidate, flagged in GAPS — the order rule does not name MS-11 concretely.

## Events Published

### Publishes: `order.placed`
- **Triggered by:** BR-ORD-008 / BR-ORD-025 (order successfully persisted at checkout)
- **Channel:** `order.placed`
- **Schema:** see `spec/shared/event-schemas/order.placed.yaml`
  ```json
  { "order_id": "ORD-5001", "store_id": "STORE-1", "customer_id": "CUST-9", "total": 130.38,
    "currency": "USD", "status": "Ordered", "has_downloads": true, "timestamp": "2026-01-01T12:00:00Z" }
  ```
- **Consumed by:** downstream capabilities (notifications, analytics, fulfillment). **No consumer
  exists among the 11 in-scope services** — see the dead-event note in the event index. Cart teardown
  is done by a direct DELETE (BR-ORD-025), not by consuming this event.
- **Guarantees:** at-least-once; downstream consumers idempotent on `order_id`.
- **Ordering:** by `order_id`

## Events Consumed

### Consumes: `payment.captured` (from MS-10)
- **Channel:** `payment.captured`
- **Action:** load the order; if `payment_type == MoneyOrder` → mark awaiting funds; else → set the
  order settled/PROCESSED and append a status-history entry (BR-ORD-009/010). Owns and enforces the
  order-state transition in ITS OWN transaction — NO cross-service order write from payment (BV-2).
- **Idempotency:** dedupe on `transaction_id` (INV-ORD-007); at-least-once delivery tolerated.

### Consumes: `payment.refunded` (from MS-10)
- **Channel:** `payment.refunded`
- **Action:** load the order; require cumulative refunds + amount ≤ `order.total` (INV-ORD-005); append
  a refund `OrderTotal` line (`module="refund"`); decrement the order total; set status Refunded and
  append status history (BR-ORD-010).
- **Idempotency:** dedupe on `transaction_id` (INV-ORD-007).

### Consumes: `merchant.deleted` (from MS-03)
- **Channel:** `merchant.deleted`
- **Action:** purge / decommission the store's orders per the decommission saga (BR-MS-LIFE-002 fan-out
  consumer). Retain ledger-relevant records per retention policy.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync providers): **7** — tax (MS-07),
  shipping (MS-08), payment (MS-10), cart (MS-06), customer (MS-05), reference-data (MS-01),
  merchant-store (MS-03); **+1 candidate** content-cms (MS-11, flagged). Plus **1 published event**
  (`order.placed`) and **2 consumed events** (`payment.captured`, `payment.refunded`), + inbound
  `merchant.deleted`.
- Integration count implied by MS-09 rules (02-domain-model Cross-Service table): tax, shipping,
  payment (charge + 2 consumed events), cart, customer, reference-data (MS-01), merchant-store = **7
  named-service integrations**; plus email/invoice/PSP external capabilities (not SAAM services) and
  the generic Content integration.
- **Status: MATCH** on the 7 named services + the payment events. The only discrepancy is the
  content-cms edge (generic Content integration in the rules, not an explicit MS-11 call) — see GAPS.

## GAPS

1. **MS-09 → MS-11 (content-cms) edge is only weakly backed.** BR-ORD-032 (digital download) references
   a generic "Content integration"; no order rule names content-cms concretely, and the digital-file
   bytes are owned by catalog's blob key. **Action:** human / Phase-2 to confirm whether order reads
   content-cms directly or delegates via catalog's digital-file endpoint, then pin the exact path. Do
   NOT fabricate a path. **Status: GAP.**
2. **`order.placed` has no consumer among the 11 in-scope services** (downstream notifications/
   analytics/fulfillment are out of scope). Not a defect — recorded as an intentional dead-among-set
   event in `spec/shared/event-schemas/index.md`.
