# MS-10 Payment Service — Business Rules

**Service ID**: MS-10
**Service Name**: payment-service
**Version**: 1.0
**Status**: 🟡 In Progress (Phase 4 extraction — pending 4a review)
**Analysis Mode**: Direct Source Read (no CAST)
**Rule Group**: PAY (single group)
**Total Rules**: 31 (BR-PAY-001..030 plus sub-rules BR-PAY-009b, BR-PAY-012a, BR-PAY-012b; BR-PAY-023/024 AMEX/DINERS/DISCOVERY are FOLDED into BR-PAY-022)

## Architecture context (READ FIRST)

This service is modernized under **BV-2 / ADR-003 (money-safety by events + reconciliation)**. In the
legacy `PaymentServiceImpl`, capture and refund write `ORDER` / `ORDER_TOTAL` / `ORDER_STATUS_HISTORY`
directly (a cross-domain DB write). In the modernized design this is **FORBIDDEN**:

- Payment owns **only** its transaction ledger (target `transaction` table, legacy `SM_TRANSACTION`) and
  its payment-method configuration.
- On capture/refund the service records the ledger transaction and **PUBLISHES a domain event**
  (`payment.captured` / `payment.refunded`). The **order service (MS-09)** consumes those events and applies
  order status/total changes in its own transaction.
- There is **NO shared order table and NO cross-service DB write**. Money-safety is guaranteed by the
  reconciliation flow: no order may reach a settled/refunded state without a corresponding CAPTURED/REFUND
  ledger transaction.

Rules BR-PAY-006, BR-PAY-007, BR-PAY-015 therefore describe the modernized behavior (record ledger +
publish event); the legacy direct-order-write is documented in Logic and a migration note as the source
behavior only.

**D-06 preservation:** BR-PAY-022 (with folded AMEX/DINERS/DISCOVERY brand rules) and BR-PAY-026 preserve a
legacy defect exactly as-is and are FLAGGED for Phase 4a — they are NOT corrected in this spec.

---

### BR-PAY-001: Payment request mandatory input preconditions

**Source Reference:** `PaymentServiceImpl.java:processPayment:288-298` (`Validate.notNull(...)` block and `payment.setCurrency(store.getCurrency())`)
**Discovery Method:** Direct Source Read

**Statement:** A payment request cannot be processed unless it carries a customer, a store, a payment instruction, an order, and an order total. When it does, the store's currency is authoritative and overrides any currency the caller supplied on the payment.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
require customer, store, payment, order, order.getTotal() all non-null → else IllegalArgumentException
payment.currency := store.currency          // store currency wins, caller value discarded
amount := order.getTotal()
```

**Data Dependencies:**
- Reads: customer, merchant_store.currency, payment (in-memory), order.total
- Writes: none (mutates payment.currency in memory only)

**Side Effects:**
- None (no persistence)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","paymentType":"CreditCard","amount":129.90}`
- Success: `200 {"transactionId":"TX-9001","transactionType":"AuthorizeCapture","currency":"USD"}` (currency taken from store, not request)
- Error Input: `POST /api/v1/payments/process {"moduleName":"paypal"}` (no orderId / total)
- Error Output: `422 {"error":"ValidationError","message":"customer, store, payment, order and order total are required"}`

---

### BR-PAY-002: Payment module selection by configured module name

**Source Reference:** `PaymentServiceImpl.java:processPayment:301-316`
**Discovery Method:** Direct Source Read

**Statement:** A payment can only proceed through a payment method the store has configured and enabled. If no methods are configured, or the requested method is not configured, or the requested method is inactive, the payment is rejected.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
modules := getPaymentModulesConfigured(store)             // decrypted per-store config map
if modules == null → error "No payment module configured"
configuration := modules.get(payment.moduleName)
if configuration == null → error "Payment module <name> is not configured"
if !configuration.isActive() → error "Payment module <name> is not active"
```

**Data Dependencies:**
- Reads: payment_method_configuration (decrypted per-store config) keyed by moduleName; configuration.active
- Writes: none

**Side Effects:**
- None (read/validate)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 3 | 3 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","paymentType":"Paypal","amount":129.90}`
- Success: `200 {"transactionId":"TX-9001","moduleName":"paypal"}`
- Error Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"stripe","amount":129.90}` (stripe not configured)
- Error Output: `422 {"error":"ValidationError","message":"Payment module stripe is not configured"}`

---

### BR-PAY-003: Transaction-type resolution (default AuthorizeCapture)

**Source Reference:** `PaymentServiceImpl.java:processPayment:318-327`
**Discovery Method:** Direct Source Read

**Statement:** The transaction mode of a payment is driven by the configured method's transaction setting. When the setting is Authorize, the payment authorizes only; for any other value (including a missing setting) the payment authorizes and captures in one step.
**Intent:** Routing / Calculation
**Weight:** Critical

**Logic:**
```
sTransactionType := configuration.integrationKeys["transaction"]
if sTransactionType == null → sTransactionType := "AUTHORIZECAPTURE"
if sTransactionType == "AUTHORIZE" → payment.transactionType := AUTHORIZE
else                                → payment.transactionType := AUTHORIZECAPTURE
```

**Data Dependencies:**
- Reads: payment_method_configuration.integrationKeys["transaction"]
- Writes: none (mutates payment.transactionType in memory)

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (AUTHORIZE, AUTHORIZECAPTURE) |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","amount":129.90}` where config transaction="AUTHORIZE"
- Success: `200 {"transactionId":"TX-9001","transactionType":"Authorize"}`
- Error Input: config transaction is an unusable value and gateway rejects → `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","amount":129.90}`
- Error Output: `502 {"error":"GatewayError","message":"Payment gateway declined the authorization"}`

---

### BR-PAY-004: Dispatch to payment gateway by transaction type

**Source Reference:** `PaymentServiceImpl.java:processPayment:329-357`; `PaymentModule.java:authorize/authorizeAndCapture/initTransaction:1-53`
**Discovery Method:** Direct Source Read

**Statement:** A payment is executed by dispatching to the pluggable gateway registered under the requested method. An Authorize payment reserves funds, an AuthorizeCapture payment reserves and settles in one step, and an Init payment obtains a redirect/checkout token. If the requested gateway is not registered, the payment is rejected. Credit-card payments are validated before dispatch.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
module := paymentModules.get(payment.moduleName)         // pluggable gateway registry
if module == null → error "Payment module <name> does not exist"
if payment is CreditCardPayment → validateCreditCard(number, type, month, year)   // BR-PAY-020
integrationModule := getPaymentMethodByCode(store, payment.moduleName)
transactionType := TransactionType.valueOf(sTransactionType)   // from raw config string
if transactionType == AUTHORIZE        → txn := module.authorize(...)
if transactionType == AUTHORIZECAPTURE → txn := module.authorizeAndCapture(...)
if transactionType == INIT             → txn := module.initTransaction(...)
```

**Data Dependencies:**
- Reads: gateway plug-in registry (paymentModules), integration module metadata, payment_method_configuration
- Writes: none directly (gateway returns a transaction)

**Side Effects:**
- Calls: external payment gateway (authorize / authorizeAndCapture / initTransaction) — EXTENSION POINT EXT-PAY-001

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 3 | 3 | OK (AUTHORIZE/AUTHORIZECAPTURE/INIT) |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 3 | 3 | OK (authorize/authorizeAndCapture/initTransaction) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","paymentType":"Paypal","amount":129.90}`
- Success: `200 {"transactionId":"TX-9001","transactionType":"AuthorizeCapture","gatewayReference":"PPL-77"}`
- Error Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"ghost","amount":129.90}` (no plug-in registered)
- Error Output: `422 {"error":"ValidationError","message":"Payment module ghost does not exist"}`

---

### BR-PAY-005: Persist transaction unless Init

**Source Reference:** `PaymentServiceImpl.java:processPayment:359-361`; `TransactionServiceImpl.java:create:34-43`
**Discovery Method:** Direct Source Read

**Statement:** A completed authorization or authorize-and-capture is recorded as a ledger transaction. An initialization (redirect/checkout token) step is transient and is not recorded in the ledger; its token is returned to the caller.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
if transactionType != INIT → transactionService.create(transaction)   // INSERT ledger row
// INIT (redirect token step) is NOT persisted here; it returns a token to the caller
```

**Data Dependencies:**
- Reads: transaction (gateway result)
- Writes: transaction (ledger INSERT) for Authorize / AuthorizeCapture

**Side Effects:**
- Creates a ledger transaction row (Authorize / AuthorizeCapture only)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (INIT) |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"authnet","amount":129.90}` (AuthorizeCapture)
- Success: `201 {"transactionId":"TX-9001","transactionType":"AuthorizeCapture","persisted":true}`
- Error Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal-express","amount":129.90}` where transaction resolves to INIT but caller expects a persisted settlement
- Error Output: `200 {"transactionType":"Init","token":"EC-2X","persisted":false}` (no ledger row created — token returned instead)

---

### BR-PAY-006: Order settlement signalled by event on AuthorizeCapture (money-order exception)

**Source Reference:** `PaymentServiceImpl.java:processPayment:363-368`
**Discovery Method:** Direct Source Read

**Statement:** When a payment authorizes and captures in one step, the order is signalled as ordered and, for every payment type except money order, as fully settled. A money-order payment leaves the order awaiting offline funds. In the modernized design the payment service records the ledger transaction and publishes a settlement event; the order service applies the resulting order status.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
// LEGACY (source, cross-domain write — REPLACED):
//   if transactionType == AUTHORIZECAPTURE:
//       order.status := ORDERED
//       if payment.paymentType != MONEYORDER → order.status := PROCESSED
// MODERNIZED (BV-2/ADR-003):
if transactionType == AUTHORIZECAPTURE:
    record ledger transaction (BR-PAY-005)
    publish payment.captured { transactionId, orderId, amount, currency, transactionType, paymentType, timestamp }
    // MS-09 (order service) consumes payment.captured and applies:
    //   money order → order awaiting funds; all other types → order settled
```

**Data Dependencies:**
- Reads: transaction, payment.paymentType
- Writes: transaction (ledger); NO order write (event emitted instead)

**Side Effects:**
- Publishes: `payment.captured` (consumed by MS-09)
- Migration note: legacy set ORDER.status ORDERED/PROCESSED directly — REPLACED by event; NO cross-service DB write

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (ORDERED/PROCESSED equivalents; MONEYORDER) |
| State transitions | 2 | 2 | OK (mapped to event semantics) |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK (ledger write; order write → event) |
| Integrations | 0 | 1 | OK (event publish is the modernized integration seam) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK (behavior preserved via event; cross-domain DB write intentionally removed per ADR-003)

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"authnet","paymentType":"CreditCard","amount":129.90}`
- Success: `201 {"transactionId":"TX-9001","transactionType":"AuthorizeCapture","eventPublished":"payment.captured"}`
- Error Input: `POST /api/v1/payments/process {"orderId":"ORD-5002","moduleName":"moneyorder","paymentType":"MoneyOrder","amount":50.00}`
- Error Output: `201 {"transactionId":"TX-9002","transactionType":"AuthorizeCapture","eventPublished":"payment.captured","note":"money order — order awaits offline funds"}`

---

### BR-PAY-007: Capture a prior authorization

**Source Reference:** `PaymentServiceImpl.java:processCapturePayment:377-437`; `PaymentModule.java:capture:39-42`
**Discovery Method:** Direct Source Read

**Statement:** A previously authorized order can be captured only through its configured, active payment method, and only when a capturable authorization exists for that order. On success a capture transaction is recorded and the order is signalled as settled. In the modernized design the payment service records the capture ledger transaction and publishes a settlement event; the order service applies the settled status.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
require customer, store, order non-null
config := configuredModules[order.paymentModuleCode]
if config == null → error "not configured"; if !config.active → error "not active"
module := paymentModules[order.paymentModuleCode]; if null → error "does not exist"
capturable := getCapturableTransaction(order); if null → error "No capturable transaction"
txn := module.capture(store, customer, order, capturable, config, integrationModule)   // gateway capture
record ledger transaction (CAPTURE)
// LEGACY (REPLACED): add OrderStatusHistory(PROCESSED); order.status := PROCESSED; orderService.saveOrUpdate
// MODERNIZED: publish payment.captured → MS-09 sets order settled
```

**Data Dependencies:**
- Reads: order.paymentModuleCode, prior AUTHORIZE ledger transaction, payment_method_configuration
- Writes: transaction (CAPTURE ledger row); NO order/history write (event emitted instead)

**Side Effects:**
- Calls: external gateway capture (EXT-PAY-001)
- Publishes: `payment.captured` (consumed by MS-09)
- Migration note: legacy wrote ORDER.status + ORDER_STATUS_HISTORY directly — REPLACED by event

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (PROCESSED equivalent) |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 3 | 1 | OK (ledger write kept; order + history writes → event, per ADR-003) |
| Integrations | 1 | 2 | OK (gateway capture + event publish) |
| Error paths | 4 | 4 | OK |

**Preservation:** OK (order/history writes intentionally converted to an event, not a data-flow loss)

**Concrete Example:**
- Input: `POST /api/v1/payments/orders/ORD-5001/capture`
- Success: `200 {"transactionId":"TX-9003","transactionType":"Capture","eventPublished":"payment.captured"}`
- Error Input: `POST /api/v1/payments/orders/ORD-7777/capture` (no prior authorization)
- Error Output: `422 {"error":"NoCapturableTransaction","message":"No capturable transaction for order ORD-7777"}`

---

### BR-PAY-008: Load and decrypt per-store payment-method configuration

**Source Reference:** `PaymentServiceImpl.java:getPaymentModulesConfigured:186-208`
**Discovery Method:** Direct Source Read

**Statement:** A store's enabled payment methods and their credentials are stored as an encrypted configuration blob and are only usable after decryption into the set of configured methods. A store with no configuration yields an empty set.
**Intent:** Calculation (config load)
**Weight:** Critical

**Logic:**
```
mc := merchantConfiguration("PAYMENT", store)
if mc != null and mc.value not blank:
    decrypted := decrypt(mc.value)
    modules := loadIntegrationConfigurations(decrypted)   // JSON → map<code, configuration>
return modules (possibly empty)
```

**Data Dependencies:**
- Reads: payment_method_configuration.config_blob (encrypted JSON), key="PAYMENT"
- Writes: none

**Side Effects:**
- Calls: encryption/decryption service (in-process)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK ("PAYMENT" config key) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (decrypt) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/payments/config` (store context in header)
- Success: `200 {"methods":[{"moduleCode":"paypal","active":true},{"moduleCode":"authnet","active":false}]}`
- Error Input: `GET /api/v1/payments/config` with a corrupted config blob
- Error Output: `500 {"error":"ConfigDecryptError","message":"Unable to load payment configuration"}`

---

### BR-PAY-009: Save a payment-method configuration (validate, encrypt, upsert)

**Source Reference:** `PaymentServiceImpl.java:savePaymentModuleConfiguration:211-252`; `PaymentModule.java:validateModuleConfiguration:17`
**Discovery Method:** Direct Source Read

**Statement:** A payment method can only be configured if a gateway plug-in exists for it and the gateway accepts the supplied configuration. Valid configuration is merged into the store's method set, encrypted, and stored — credentials are never persisted in clear text.
**Intent:** Validation / State Transition
**Weight:** Critical

**Logic:**
```
module := paymentModules[configuration.moduleCode]; if null → error "module does not exist"
module.validateModuleConfiguration(configuration, store)   // gateway plug-in hook, may reject
existing := merchantConfiguration("PAYMENT", store)
map := existing ? decrypt+load(existing) : new config(key="PAYMENT", store)
map.put(configuration.moduleCode, configuration)
blob := encrypt(toJSON(map))
save/update payment_method_configuration with blob
```

**Data Dependencies:**
- Reads: gateway plug-in registry, payment_method_configuration
- Writes: payment_method_configuration.config_blob (encrypted)

**Side Effects:**
- Calls: gateway plug-in validation (EXT-PAY-001), encryption
- Writes: upsert payment_method_configuration

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK ("PAYMENT") |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 2 | 2 | OK (validate + encrypt) |
| Error paths | 2 | 2 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/payments/config/paypal {"active":true,"defaultSelected":false,"integrationKeys":{"username":"...","transaction":"AUTHORIZECAPTURE"}}`
- Success: `200 {"moduleCode":"paypal","active":true,"stored":true}`
- Error Input: `PUT /api/v1/payments/config/paypal {"integrationKeys":{}}` (gateway rejects missing credentials)
- Error Output: `422 {"error":"ConfigValidationError","message":"Payment module configuration is invalid"}`

---

### BR-PAY-009b: Remove a payment-method configuration

**Source Reference:** `PaymentServiceImpl.java:removePaymentModuleConfiguration:254-296`
**Discovery Method:** Direct Source Read

**Statement:** Removing a store's payment method drops that method from the store's configured set and deletes any method-specific custom configuration, leaving all other methods intact.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
mc := merchantConfiguration("PAYMENT", store)
if mc and value not blank:
    map := decrypt+load(mc.value); map.remove(moduleCode); re-encrypt; save/update(mc)
custom := merchantConfiguration(moduleCode, store)
if custom != null → delete(custom)
```

**Data Dependencies:**
- Reads: payment_method_configuration (key="PAYMENT" and key=moduleCode)
- Writes: payment_method_configuration (update PAYMENT blob; delete per-method custom row)

**Side Effects:**
- Calls: encryption
- Writes: update + delete payment_method_configuration

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK ("PAYMENT") |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (encrypt) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `DELETE /api/v1/payments/config/paypal`
- Success: `204` (paypal removed, other methods intact)
- Error Input: `DELETE /api/v1/payments/config/paypal` with a corrupted config blob
- Error Output: `500 {"error":"ConfigError","message":"Unable to update payment configuration"}`

---

### BR-PAY-010: Payment-method region eligibility filter

**Source Reference:** `PaymentServiceImpl.java:getPaymentMethods:74-90`
**Discovery Method:** Direct Source Read

**Statement:** A payment gateway is only offered to a store when the gateway's declared regions cover the store's country, or the gateway is declared globally available.
**Intent:** Authorization / Routing
**Weight:** Critical

**Logic:**
```
modules := integrationModules("PAYMENT")
for module in modules:
    if module.regionsSet contains store.country.isoCode OR contains "*" → include
```

**Data Dependencies:**
- Reads: payment gateway registry metadata (regionsSet), store.country.isoCode (MS-03/MS-01 reference reads)
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK ("*" wildcard) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (store/country reference read) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/payments/methods` (store country = CA)
- Success: `200 {"methods":[{"code":"paypal","regions":["*"]},{"code":"beanstream","regions":["CA"]}]}`
- Error Input: `GET /api/v1/payments/methods` (store country = FR, no gateway covers FR)
- Error Output: `200 {"methods":[]}` (no eligible gateway — empty set, not an error)

---

### BR-PAY-011: Accepted payment methods — active only, with payment-type mapping

**Source Reference:** `PaymentServiceImpl.java:getAcceptedPaymentMethods:93-135`
**Discovery Method:** Direct Source Read

**Statement:** The methods offered to a shopper are the store's active configured methods, each classified by its payment type (credit card, free, money order, PayPal), defaulting to cash-on-delivery when the type is unrecognized. Inactive methods and methods without registry metadata are omitted.
**Intent:** Routing / Calculation
**Weight:** Critical

**Logic:**
```
configured := getPaymentModulesConfigured(store)
for code in configured:
    cfg := configured[code]; if !cfg.active → skip
    md := getPaymentMethodByCode(store, cfg.moduleCode); if md == null → skip
    type := COD (default)
    if md.type ~ CREDITCARD → CreditCard; FREE → Free; MONEYORDER → MoneyOrder; PAYPAL → Paypal
    add PaymentMethod(code, type, defaultSelected)
```

**Data Dependencies:**
- Reads: configured methods, gateway registry metadata (type)
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 5 | 5 | OK (CREDITCARD/FREE/MONEYORDER/PAYPAL/COD) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (registry read) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/payments/accepted-methods` (store has active paypal + inactive authnet)
- Success: `200 {"methods":[{"code":"paypal","paymentType":"Paypal","defaultSelected":true}]}`
- Error Input: `GET /api/v1/payments/accepted-methods` (method active but unknown registry type)
- Error Output: `200 {"methods":[{"code":"custom","paymentType":"Cod","defaultSelected":false}]}` (unknown type silently defaults to Cod)

---

### BR-PAY-012: Refund orchestration

**Source Reference:** `PaymentServiceImpl.java:processRefund:440-520`; `PaymentModule.java:refund:44-46`
**Discovery Method:** Direct Source Read

**Statement:** An order can be refunded only through its configured payment method and only when a settled transaction exists to refund against. On success a refund transaction is recorded. In the modernized design the payment service records the refund ledger transaction and publishes a refund event; the order service applies the refund to the order total and status.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
require customer, store, amount, order, order total non-null
config := configuredModules[order.paymentModuleCode]; if null → error (active NOT re-checked — legacy quirk preserved)
refundable := getRefundableTransaction(order); if null → error "No refundable transaction"
txn := module.refund(partial, store, refundable, order, amount, config, integrationModule)   // gateway refund
record ledger transaction (REFUND)
// LEGACY (REPLACED): add OT_REFUND line, decrement order total, order.status := REFUNDED, saveOrUpdate
// MODERNIZED: publish payment.refunded → MS-09 applies refund line + status
```

**Data Dependencies:**
- Reads: order.paymentModuleCode, refundable ledger transaction, amount
- Writes: transaction (REFUND ledger row); NO order/order-total write (event emitted instead)

**Side Effects:**
- Calls: external gateway refund (EXT-PAY-001)
- Publishes: `payment.refunded` (consumed by MS-09)
- Migration note: legacy wrote ORDER / ORDER_TOTAL / ORDER_STATUS_HISTORY directly — REPLACED by event
- Note: unlike capture, refund does NOT re-check `configuration.isActive()` — legacy behavior preserved

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 3 | 1 | OK (ledger kept; order/total writes → event per ADR-003) |
| Integrations | 1 | 2 | OK (gateway refund + event publish) |
| Error paths | 3 | 3 | OK |

**Preservation:** OK (order/total writes intentionally converted to event)

**Concrete Example:**
- Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":50.00}`
- Success: `200 {"transactionId":"TX-9004","transactionType":"Refund","partial":true,"eventPublished":"payment.refunded"}`
- Error Input: `POST /api/v1/payments/orders/ORD-7777/refund {"amount":10.00}` (no settled transaction)
- Error Output: `422 {"error":"NoRefundableTransaction","message":"No refundable transaction for this order"}`

---

### BR-PAY-012a: Refund amount cannot exceed order total

**Source Reference:** `PaymentServiceImpl.java:processRefund:456-461`
**Discovery Method:** Direct Source Read

**Statement:** A refund is rejected when the requested amount is greater than the order's remaining total. Because the remaining total is reduced by each prior refund, cumulative refunds can never exceed the original order value.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
orderTotal := order.getTotal()
if amount > orderTotal → error "refunded amount is greater than the total allowed"
// NOTE: legacy compares via double (amount.doubleValue() > orderTotal.doubleValue()) — precision risk; see clarification
```

**Data Dependencies:**
- Reads: order.total (as known to the refund request context), amount
- Writes: none

**Side Effects:**
- None (guard)

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
| Error paths | 1 | 1 | OK |

**Preservation:** OK (double-vs-BigDecimal comparison flagged for 4a — money should use exact decimal)

**Concrete Example:**
- Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":50.00}` (remaining total 129.90)
- Success: `200 {"transactionId":"TX-9004","transactionType":"Refund"}`
- Error Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":200.00}` (exceeds remaining total)
- Error Output: `422 {"error":"RefundExceedsTotal","message":"the refunded amount is greater than the total allowed"}`

---

### BR-PAY-012b: Partial-vs-full refund determination

**Source Reference:** `PaymentServiceImpl.java:processRefund:483-486`
**Discovery Method:** Direct Source Read

**Statement:** A refund is classified as partial when its amount differs from the order total and as full when it equals the order total; this classification is passed to the gateway to select the appropriate refund type.
**Intent:** Calculation
**Weight:** Critical

**Logic:**
```
partial := (amount != order.getTotal())
// passed to gateway refund(partial,...) → gateway FULL vs PARTIAL refund type
// NOTE: legacy uses double equality (fragile) — see clarification
```

**Data Dependencies:**
- Reads: amount, order.total
- Writes: none

**Side Effects:**
- Drives gateway refund type (partial flag)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (gateway flag) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK (double-equality flagged for 4a)

**Concrete Example:**
- Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":50.00}` (total 129.90)
- Success: `200 {"transactionId":"TX-9004","partial":true}`
- Error Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":129.90}` (equals total → full)
- Error Output: `200 {"transactionId":"TX-9005","partial":false}` (full refund — not an error, contrast case)

---

### BR-PAY-015: Refund event — order-total decrement and refund line (consumed by order service)

**Source Reference:** `PaymentServiceImpl.java:processRefund:499-520`
**Discovery Method:** Direct Source Read

**Statement:** A successful refund reduces the order's remaining total by the refunded amount, records a refund line against the order, and marks the order as refunded. In the modernized design the payment service publishes a refund event carrying the refunded amount; the order service applies the total decrement, refund line, and refunded status in its own transaction.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
// LEGACY (source, cross-domain write — REPLACED):
//   refund := OrderTotal(module=OT_REFUND, value=amount, sortOrder=100)
//   order.orderTotal.add(refund); orderTotal := orderTotal.subtract(amount)
//   set OT_TOTAL line to orderTotal; order.total := orderTotal
//   order.status := REFUNDED; add OrderStatusHistory(REFUNDED); orderService.saveOrUpdate
// MODERNIZED (BV-2/ADR-003):
publish payment.refunded { transactionId, orderId, amount, currency, transactionType:"Refund", timestamp }
// MS-09 consumes payment.refunded and: adds refund line, decrements order total, sets order refunded
```

**Data Dependencies:**
- Reads: refunded amount, order reference
- Writes: transaction (REFUND ledger row, via BR-PAY-012); NO order/order-total write (event emitted)

**Side Effects:**
- Publishes: `payment.refunded` (consumed by MS-09)
- Migration note: legacy sortOrder=100 refund line + OT_TOTAL rewrite + REFUNDED status were direct order writes — REPLACED by event
- Note: legacy has no PARTIALLY_REFUNDED state — a partial refund also lands the order at REFUNDED (flagged, Layer A)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK (OT_REFUND, sortOrder 100 → event payload) |
| State transitions | 1 | 1 | OK (REFUNDED via event) |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 1 | OK (order/total writes → event per ADR-003) |
| Integrations | 0 | 1 | OK (event publish) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK (order writes intentionally converted to event; no PARTIALLY_REFUNDED state flagged for 4a)

**Concrete Example:**
- Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":50.00}` (total 129.90)
- Success: `200 {"transactionId":"TX-9004","transactionType":"Refund","eventPublished":"payment.refunded","refundedAmount":50.00}`
- Error Input: `POST /api/v1/payments/orders/ORD-5001/refund {"amount":50.00}` when gateway refund fails
- Error Output: `502 {"error":"GatewayError","message":"Refund declined by gateway — no ledger row, no event"}`

---

### BR-PAY-013: Locate the capturable authorization

**Source Reference:** `TransactionServiceImpl.java:getCapturableTransaction:66-93`; `Transaction.java:1-190`
**Discovery Method:** Direct Source Read

**Statement:** The authorization eligible for capture is the earliest recorded authorization for the order that still carries gateway details, scanning in ledger order and stopping at the first capture or refund already recorded. An authorization with no gateway details is not capturable.
**Intent:** Routing / State query
**Weight:** Critical

**Logic:**
```
transactions := listByOrder(order)          // ledger order
capturable := null
for t in transactions:
    if t.type == AUTHORIZE and t.details not blank → capturable := t (rehydrate details)
    if t.type == CAPTURE → break
    if t.type == REFUND  → break
return capturable
```

**Data Dependencies:**
- Reads: transaction rows for the order (transaction_type, details)
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 3 | 3 | OK (AUTHORIZE/CAPTURE/REFUND) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK (ledger-ordering dependency flagged, Layer A — see BR-PAY-018)

**Concrete Example:**
- Input: `GET /api/v1/payments/orders/ORD-5001/capturable-transaction`
- Success: `200 {"transactionId":"TX-9001","transactionType":"Authorize","hasDetails":true}`
- Error Input: `GET /api/v1/payments/orders/ORD-8888/capturable-transaction` (already captured)
- Error Output: `404 {"error":"NotFound","message":"No capturable transaction for order ORD-8888"}`

---

### BR-PAY-014: Select the settled transaction to refund against

**Source Reference:** `TransactionServiceImpl.java:getRefundableTransaction:96-160`; `Transaction.java:1-190`
**Discovery Method:** Direct Source Read

**Statement:** The transaction eligible for refund is the order's settled transaction, preferring a capture over an authorize-and-capture when both exist. Selection scans the order's ledger and rehydrates the chosen transaction's gateway details.
**Intent:** Routing / State query
**Weight:** Critical

**Logic:**
```
for t in transactions:
    if t.type == AUTHORIZECAPTURE → finalTransactions[AC] := t
    if t.type == CAPTURE          → finalTransactions[CAPTURE] := t
    if t.type == REFUND           → track latest by date (finalTransactions[REFUND])   // computed but unused
final := finalTransactions[AC]
if finalTransactions has CAPTURE → final := finalTransactions[CAPTURE]   // CAPTURE overrides AC
rehydrate final.details; return final
```

**Data Dependencies:**
- Reads: transaction rows (transaction_type, transaction_date, details)
- Writes: none

**Side Effects:**
- None
- Note: the "latest REFUND" tracking is dead (never assigned to the result); prior-refund amount is NOT subtracted at selection (bounding relies on BR-PAY-012a). Flagged for 4a.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 3 | 3 | OK (AUTHORIZECAPTURE/CAPTURE/REFUND) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** FLAGGED (dead REFUND branch + selection precedence ambiguity — carried to Phase 4a for confirmation of refund-target rules)

**Concrete Example:**
- Input: `GET /api/v1/payments/orders/ORD-5001/refundable-transaction` (has AuthorizeCapture then Capture)
- Success: `200 {"transactionId":"TX-9003","transactionType":"Capture"}` (capture preferred)
- Error Input: `GET /api/v1/payments/orders/ORD-9999/refundable-transaction` (no settled transaction)
- Error Output: `404 {"error":"NotFound","message":"No refundable transaction for this order"}`

---

### BR-PAY-016: Record a ledger transaction — serialize gateway details

**Source Reference:** `TransactionServiceImpl.java:create:34-43`; `Transaction.java:toJSONString:165-180`
**Discovery Method:** Direct Source Read

**Statement:** When a transaction is recorded, its transient gateway detail map (tokens, gateway references, correlation ids) is serialized into the persisted transaction's detail field so it survives beyond the request.
**Intent:** Calculation / State Transition
**Weight:** Critical

**Logic:**
```
details := transaction.toJSONString()      // JSON over the transient detail map
if details not blank → transaction.details := details
persist transaction                         // INSERT ledger row
```

**Data Dependencies:**
- Reads: transaction.transactionDetails (transient map)
- Writes: transaction.details (serialized JSON), transaction row (INSERT)

**Side Effects:**
- Writes: INSERT transaction

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (JSON serialization) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: internal — gateway returns `{transactionType:"Authorize", details:{token:"EC-2X", correlationId:"abc"}}`
- Success: ledger row persisted with `details` = `{"token":"EC-2X","correlationId":"abc"}`; `201 {"transactionId":"TX-9001"}`
- Error Input: detail map contains a non-serializable value
- Error Output: `500 {"error":"SerializationError","message":"Cannot serialize transaction details"}`

---

### BR-PAY-017: List an order's transactions with rehydrated details

**Source Reference:** `TransactionServiceImpl.java:listTransactions:46-63`
**Discovery Method:** Direct Source Read

**Statement:** Listing an order's transactions returns each recorded transaction with its serialized gateway details parsed back into a structured detail map.
**Intent:** Calculation
**Weight:** Critical

**Logic:**
```
transactions := listByOrder(order)
for t in transactions: if t.details not blank → t.transactionDetails := parseJSON(t.details)
```

**Data Dependencies:**
- Reads: transaction.details
- Writes: none (in-memory rehydrate)

**Side Effects:**
- None (parse failure → error)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (JSON parse) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/payments/orders/ORD-5001/transactions`
- Success: `200 {"transactions":[{"transactionId":"TX-9001","transactionType":"Authorize","details":{"token":"EC-2X"}}]}`
- Error Input: `GET /api/v1/payments/orders/ORD-5001/transactions` with a corrupted details field
- Error Output: `500 {"error":"ParseError","message":"Unable to read transaction details"}`

---

### BR-PAY-018: Retrieve transactions for an order

**Source Reference:** `TransactionDaoImpl.java:listByOrder:20-31`; `Transaction.java:1-190`
**Discovery Method:** Direct Source Read

**Statement:** All transactions belonging to a specific order can be retrieved together. The legacy retrieval imposes no explicit ordering, so capture/refund selection that walks the results depends on the storage return order — a correctness risk the modernized design must fix with a deterministic order (by transaction date, then id).
**Intent:** Data access
**Weight:** Critical

**Logic:**
```
SELECT transaction WHERE transaction.order_id = :orderId
// LEGACY: no ORDER BY → row order is storage-dependent (see BR-PAY-013/014)
// MODERNIZED: ORDER BY transaction_date, transaction_id  (deterministic)
```

**Data Dependencies:**
- Reads: transaction (by order_id)
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (persistence query) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK (net-new: modernized design adds deterministic ORDER BY to remove the legacy ordering hazard)

**Concrete Example:**
- Input: `GET /api/v1/payments/orders/ORD-5001/transactions`
- Success: `200 {"transactions":[{"transactionId":"TX-9001","transactionType":"Authorize"},{"transactionId":"TX-9003","transactionType":"Capture"}]}` (deterministic date order)
- Error Input: `GET /api/v1/payments/orders/UNKNOWN/transactions`
- Error Output: `200 {"transactions":[]}` (empty — no order rows)

---

### BR-PAY-019: Payment-gateway plug-in contract (extension point)

**Source Reference:** `PaymentModule.java:1-53`; `PaymentServiceImpl.java:paymentModules:66-70`
**Discovery Method:** Direct Source Read

**Statement:** Payment gateways are pluggable behind a fixed contract that every gateway implements: validate configuration, initialize a checkout token, authorize, capture, authorize-and-capture, and refund. A store selects and activates gateways by code; new gateways are added by implementing the contract and registering it — no change to core payment logic.
**Intent:** Extensibility contract (Routing)
**Weight:** Critical
**Extension Point:** EXT-PAY-001

**Logic:**
```
interface PaymentModule {
  validateModuleConfiguration(configuration, store)
  initTransaction(store, customer, amount, payment, configuration, module)     // redirect/checkout token
  authorize(store, customer, items, amount, payment, configuration, module)
  capture(store, customer, order, capturableTransaction, configuration, module)
  authorizeAndCapture(store, customer, items, amount, payment, configuration, module)
  refund(partial, store, transaction, order, amount, configuration, module)
}
// implementations registered in a code-keyed registry (paymentModules) — this map IS the plug-in registry
```

**Data Dependencies:**
- Reads: payment_method_configuration (per-store, decrypted), gateway registry metadata
- Writes: none (implementations return a transaction)

**Side Effects:**
- Calls: external gateway operations (EXT-PAY-001) — resolver consumes per-store config

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 6 | 6 | OK (6 contract operations) |
| Data writes | 0 | 0 | OK |
| Integrations | 6 | 6 | OK (6 gateway seams) |
| Error paths | 6 | 6 | OK (each throws IntegrationException) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/payments/gateways` (list registered plug-ins)
- Success: `200 {"gateways":[{"code":"paypal","operations":["authorize","capture","refund","initTransaction"]}]}`
- Error Input: configure a method whose code has no registered plug-in — `PUT /api/v1/payments/config/ghost {...}`
- Error Output: `422 {"error":"ValidationError","message":"Payment module ghost does not exist"}`

---

### BR-PAY-020: Orchestrated credit-card validation

**Source Reference:** `PaymentServiceImpl.java:validateCreditCard:523-556`
**Discovery Method:** Direct Source Read

**Statement:** A credit-card payment is validated before dispatch: the expiry month and year must be numeric, the card number must be present and contain only digits and permitted separators, and after stripping separators the expiry and card number must pass their respective checks.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
parseInt(month); parseInt(date) → else error "creditcard.dateformat"
if blank(number) → error "creditcard.number"
if number matches [^\d\s.-] → error "creditcard.number"     // any char not digit/space/dot/dash
number := strip [\s.-]
validateCreditCardDate(month, year)     // BR-PAY-021
validateCreditCardNumber(number, type)  // BR-PAY-022 (+ Luhn BR-PAY-025)
```

**Data Dependencies:**
- Reads: card number, card type, expiry month/year
- Writes: none

**Side Effects:**
- None (throws on invalid)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 1 | 1 | OK (separator/char-class pattern) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 3 | 3 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"authnet","paymentType":"CreditCard","card":{"number":"4111 1111 1111 1111","type":"Visa","expMonth":"12","expYear":"2030"}}`
- Success: `200 {"transactionId":"TX-9001"}`
- Error Input: `{"card":{"number":"4111-XX11","type":"Visa","expMonth":"12","expYear":"2030"}}` (non-permitted characters)
- Error Output: `422 {"error":"ValidationError","message":"Invalid card number","messageKey":"messages.error.creditcard.number"}`

---

### BR-PAY-021: Credit-card expiry not in the past

**Source Reference:** `PaymentServiceImpl.java:validateCreditCardDate:558-573`
**Discovery Method:** Direct Source Read

**Statement:** A credit card is rejected when its expiry year is before the current year, or the expiry year is the current year and the expiry month is before the current month. The check has no upper bound on the month value, so an out-of-range month is not caught here (preserved as-is).
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
monthNow := now.month (1-based); yearNow := now.year
if yearNow > y → error "dateformat"
if yearNow == y and monthNow > m → error "dateformat"
// NO check that m in 1..12 — a month like 13 passes this guard (preserved)
```

**Data Dependencies:**
- Reads: system clock, expiry month m / year y
- Writes: none

**Side Effects:**
- None

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

**Preservation:** OK (no-upper-bound-on-month quirk preserved as-is per D-06 guidance for BR-PAY-021)

**Concrete Example:**
- Input: card expMonth="12" expYear="2030"
- Success: `200 {"transactionId":"TX-9001"}` (future date accepted)
- Error Input: card expMonth="01" expYear="2020" (past)
- Error Output: `422 {"error":"ValidationError","message":"Invalid date format","messageKey":"messages.error.creditcard.dateformat"}`

---

### BR-PAY-022: Card brand length/prefix validation — DEAD CODE (preserved, flagged)

**Source Reference:** `PaymentServiceImpl.java:validateCreditCardNumber:575-620`; `CreditCardType.java:1-6`
**Discovery Method:** Direct Source Read

**Statement:** The system intends to apply brand-specific length and prefix rules (Mastercard, Visa, Amex, Diners, Discovery — folding former BR-PAY-023 Amex and BR-PAY-024 Diners/Discovery) before the checksum. As implemented, every brand guard tests card-type identity in a way that is always false, so NONE of the brand rules ever execute — only the checksum (BR-PAY-025) actually validates a card number. This defect is preserved exactly.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
// INTENDED (never runs):
//   MASTERCARD : len==16 and 51 ≤ prefix2 ≤ 55
//   VISA       : (len==13 or 16) and prefix1 == 4
//   AMEX       : len==15 and prefix2 in {34,37}         (folded BR-PAY-023)
//   DINERS     : len==14 and (prefix2 in {36,38} or 300 ≤ prefix3 ≤ 305)   (folded BR-PAY-024)
//   DISCOVERY  : len==16 and prefix5 == 6011            (folded BR-PAY-024; also a 5-vs-4-digit compare bug)
// ACTUAL: each guard is CreditCardType.<BRAND>.equals(creditCard.name()) i.e. enum.equals(String)
//         → ALWAYS FALSE → every brand block is DEAD CODE. Only luhnValidate (BR-PAY-025) runs.
luhnValidate(number)   // the only card-number check that actually executes
```

**Data Dependencies:**
- Reads: stripped card number, card type
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 10 | 10 | OK (all brand branches recorded — dead at runtime) |
| Data-flow | 2 | 2 | OK |
| Constants | 12 | 12 | OK (all brand lengths/prefixes recorded as evidence) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 5 | 5 | OK (all dead-code error paths recorded) |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] — brand length/prefix validation is dead code (enum-`.equals(String)` always false); only Luhn runs. DISCOVERY substring(0,5)==6011 is additionally logically inconsistent. Carried to Phase 4a: "brand validation intentionally disabled vs defect to reimplement — BA decision." NOT corrected in this spec.

**Concrete Example:**
- Input: `POST /api/v1/payments/process {...,"card":{"number":"4111111111111111","type":"Amex","expMonth":"12","expYear":"2030"}}` (a Visa number labelled Amex)
- Success: `200 {"transactionId":"TX-9001"}` — accepted because brand check never runs and the number passes Luhn (preserved dead-code behavior)
- Error Input: `{...,"card":{"number":"4111111111111112","type":"Visa",...}}` (fails Luhn)
- Error Output: `422 {"error":"ValidationError","message":"Invalid card number","messageKey":"messages.error.creditcard.number"}` (only Luhn rejects)

---

### BR-PAY-025: Luhn (mod-10) checksum

**Source Reference:** `PaymentServiceImpl.java:luhnValidate:627-651`
**Discovery Method:** Direct Source Read

**Statement:** A card number is rejected when it fails the mod-10 checksum: doubling every second digit from the right (subtracting nine from any result over nine) and summing all digits must yield a multiple of ten. This is the only card-number check that actually executes.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
digits := numeric value of each char
from second-to-last, step back by 2: d *= 2; if d > 9 → d -= 9
total := Σ digits
if total % 10 != 0 → error "creditcard.number"
```

**Data Dependencies:**
- Reads: stripped card number
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (×2, mod 10) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: card number "4111111111111111"
- Success: `200 {"transactionId":"TX-9001"}` (valid Luhn)
- Error Input: card number "4111111111111112"
- Error Output: `422 {"error":"ValidationError","message":"Invalid card number","messageKey":"messages.error.creditcard.number"}`

---

### BR-PAY-026: Capture-via-process-payment guard — UNREACHABLE (preserved, flagged)

**Source Reference:** `PaymentServiceImpl.java:processPayment:349-355`
**Discovery Method:** Direct Source Read

**Statement:** The code intends to reject a capture transaction routed through the ordinary payment-processing path and redirect it to the dedicated capture path. As implemented the guard is unreachable — the transaction-type parse throws on an unknown value rather than yielding an empty result, and the inner comparison compares a type against a string and is always false — so the guard never fires. This defect is preserved exactly.
**Intent:** Validation (intended) / dead code (actual)
**Weight:** Critical

**Logic:**
```
// INTENDED (never runs):
//   if transactionType == null:
//       transactionType := payment.transactionType
//       if transactionType.equals(TransactionType.CAPTURE.name()) → error "Use processCapturePayment"
// ACTUAL: TransactionType.valueOf(...) throws on unknown input (never returns null) → the == null block
//         is unreachable; and enum.equals(String) is always false. Guard NOT enforced.
```

**Data Dependencies:**
- Reads: resolved transaction type
- Writes: none

**Side Effects:**
- None (unreachable)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (recorded — dead at runtime) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (CAPTURE) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (dead error path recorded) |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] — guard unreachable (valueOf throws instead of returning null; enum-vs-String compare always false). Carried to Phase 4a: "should the modernized service explicitly reject CAPTURE/INIT/REFUND in the transaction config key?" NOT corrected in this spec.

**Concrete Example:**
- Input: config transaction key set to "CAPTURE", then `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"authnet","amount":10.00}`
- Success: (no success path — the intended guard would have blocked this; preserved behavior is that the guard never fires)
- Error Input: config transaction key = "CAPTURE" (an invalid mode for this path)
- Error Output: `422 {"error":"ConfigValueError","message":"Unknown transaction mode 'CAPTURE'"}` — arising from the parse throwing, NOT from the intended guard (preserved)

---

### BR-PAY-027: Checkout-token initialization not persisted

**Source Reference:** `PaymentServiceImpl.java:processPayment:355-361`; `PaymentModule.java:initTransaction:26-30`
**Discovery Method:** Direct Source Read

**Statement:** A redirect/checkout initialization returns a token to the caller and is intentionally not recorded in the ledger; the settlement transaction is recorded later when the shopper returns and the payment authorizes or captures. Not every gateway implements the initialization operation.
**Intent:** Routing / State Transition
**Weight:** Critical

**Logic:**
```
INIT branch → module.initTransaction(...)   // returns a token transaction, NOT persisted (BR-PAY-005)
// Some gateways do not implement initTransaction (throw not-implemented); the real express-init
// may flow through a gateway-specific entry point outside the core dispatch.
```

**Data Dependencies:**
- Reads: gateway configuration (integration keys)
- Writes: none (token not persisted)

**Side Effects:**
- Calls: external gateway initialization (EXT-PAY-001); returns a transient token transaction

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (INIT) |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (gateway init) |
| Error paths | 1 | 1 | OK |

**Preservation:** FLAGGED (external-system boundary — whether INIT should be a first-class operation in the target design; carried to Phase 4a)

**Concrete Example:**
- Input: `POST /api/v1/payments/initialize {"orderId":"ORD-5001","moduleName":"paypal-express","amount":129.90}`
- Success: `200 {"transactionType":"Init","token":"EC-2X","persisted":false}`
- Error Input: `POST /api/v1/payments/initialize {"orderId":"ORD-5001","moduleName":"authnet","amount":129.90}` (gateway has no init operation)
- Error Output: `501 {"error":"NotImplemented","message":"Initialization not supported by payment module authnet"}`

---

### BR-PAY-028: Card number display masking

**Source Reference:** `CreditCardUtils.java:maskCardNumber:11-24`
**Discovery Method:** Direct Source Read

**Statement:** A card number shown for display keeps its first four and last four digits and masks the middle with a fixed ten-character mask; numbers shorter than ten digits are rejected as invalid. The mask is fixed width, so the masked value does not reveal the real card length.
**Intent:** Calculation
**Weight:** Critical

**Logic:**
```
if number.length < 10 → error "Invalid number of digits"
mask := number[0..4] + "XXXXXXXXXX" + number[len-4..len]   // first4 + 10 X + last4 (fixed width)
```

**Data Dependencies:**
- Reads: clear card number
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 3 | 3 | OK (10, 4, "XXXXXXXXXX") |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK (fixed-width mask preserved as-is per D-06 guidance for BR-PAY-028)

**Concrete Example:**
- Input: card number "4111111111111111"
- Success: masked "4111XXXXXXXXXX1111"
- Error Input: card number "123456" (fewer than 10 digits)
- Error Output: `422 {"error":"ValidationError","message":"Invalid number of digits"}`

---

### BR-PAY-029: Payment defaults to authorize-and-capture

**Source Reference:** `Payment.java:8`; `PaymentServiceImpl.java:processPayment:318-327`
**Discovery Method:** Direct Source Read

**Statement:** A newly constructed payment defaults to the authorize-and-capture transaction mode unless the store's method configuration overrides it.
**Intent:** Calculation (default)
**Weight:** Critical

**Logic:**
```
Payment.transactionType default := AUTHORIZECAPTURE
// later overridden by BR-PAY-003 from the configured method's transaction key
```

**Data Dependencies:**
- Reads: payment.transactionType (default)
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (AUTHORIZECAPTURE) |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"authnet","amount":10.00}` (config has no transaction key)
- Success: `201 {"transactionId":"TX-9001","transactionType":"AuthorizeCapture"}` (default applied)
- Error Input: config transaction key = "AUTHORIZE" overrides the default
- Error Output: `200 {"transactionId":"TX-9002","transactionType":"Authorize"}` (contrast — override wins, not an error)

---

### BR-PAY-030: PayPal payment forces PayPal payment type on construction

**Source Reference:** `PaypalPayment.java:13-15`; `PaymentServiceImpl.java:getAcceptedPaymentMethods:93-135`
**Discovery Method:** Direct Source Read

**Statement:** A PayPal payment is always classified with the PayPal payment type from the moment it is created, and it carries the express-checkout payer id and payment token.
**Intent:** State Transition (invariant on construct)
**Weight:** Critical

**Logic:**
```
new PaypalPayment() ⇒ paymentType := PAYPAL
// carries payerId + paymentToken for express checkout
```

**Data Dependencies:**
- Reads: payment.paymentType, payerId, paymentToken
- Writes: none

**Side Effects:**
- None

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (PAYPAL) |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","paymentType":"Cod","payerId":"PAYER-1","paymentToken":"EC-2X","amount":10.00}`
- Success: `201 {"transactionId":"TX-9001","paymentType":"Paypal"}` (type forced to Paypal regardless of the request value)
- Error Input: `POST /api/v1/payments/process {"orderId":"ORD-5001","moduleName":"paypal","payerId":"","paymentToken":"","amount":10.00}` (express checkout without token)
- Error Output: `422 {"error":"ValidationError","message":"PayPal express checkout requires a payer id and payment token"}`
