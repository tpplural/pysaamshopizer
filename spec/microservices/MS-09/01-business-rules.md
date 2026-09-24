# MS-09 Order Service — Business Rules

**Service ID**: MS-09
**Service Name**: order-service
**Version**: 1.0
**Status**: 🟡 In Progress (Phase 4 extraction — pending 4a review)
**Analysis Mode**: Direct Source Read (no CAST)
**Rule Group**: ORD (single group)
**Total Rules**: 32 (BR-ORD-001..032, contiguous)

## Architecture context (READ FIRST)

MS-09 is the **orchestrator hub** and the **authoritative order-totals engine** of the modernized store.
Three architectural decisions govern this service and are reflected precisely in the rules below.

- **BV-1 / ADR-001 — Order OWNS the total.** `OrderServiceImpl.caculateOrder` computes the order subtotal
  locally, then calls the tax service (MS-07 `/calculate`) and the shipping service (MS-08 `/quote`) as
  **synchronous stateless reads**, and folds their results (TAX total lines, shipping/handling) into its
  own local computation. This is the single source of truth for the order grand total — the cart service
  (MS-06, BV-3) delegates its authoritative grand total here, and tax first joins the money math here.
  Tax and shipping are modeled as cross-service calculators; the total computation is OWNED by MS-09.
  The ordered OrderTotal pipeline is preserved: subtotal → shipping → handling → tax lines → grand total,
  with totals sorted by `sortOrder`. (BR-ORD-001..005, 017, 024, 030.)

- **BV-2 / ADR-003 / D-07 — Order CONSUMES payment events.** Payment (MS-10) owns the transaction ledger
  and EMITS `payment.captured` / `payment.refunded`. In the legacy `PaymentServiceImpl` those handlers
  wrote `ORDERS` / `ORDER_TOTAL` / `ORDER_STATUS_HISTORY` directly (a cross-domain DB write). In the
  modernized design that is FORBIDDEN: MS-09 owns and enforces ALL order-state transitions and applies
  settlement facts by CONSUMING the events in its own transaction, idempotent on `transactionId`
  (BR-ORD-033-consumer behavior is documented in `02-domain-model.md` Domain Events; the state effects are
  captured by BR-ORD-009/010 and the settled/refunded transitions). MS-09 PUBLISHES `order.placed` on a
  successful checkout.

- **D-08 / R-03 — Checkout is a SAGA, not 2PC.** The checkout charge-vs-persist window (payment charged but
  order not yet persisted, or vice versa) is handled by a saga with idempotency keys and a reconciliation
  job — NOT a two-phase commit and NOT a shared cross-service transaction. The legacy synchronous
  `paymentService.processPayment(...)` at checkout is the saga's CHARGE step; the order-persist +
  status-history write is the PERSIST step. Architecture §7 money-safety invariant: **no PROCESSED order
  without a CAPTURED transaction**, guaranteed by the reconciler. (BR-ORD-008, 025.)

**D-06 preservation:** BR-ORD-006 (rounding intent not enforced), BR-ORD-032 (download IDOR + unenforced
download-limit), the OrderStatus legal-transition set (not encoded in legacy), and BR-ORD-020 (masked-PAN
persistence, PCI) are preserved EXACTLY as-is and FLAGGED for Phase 4a — they are NOT corrected in this spec.

---

### BR-ORD-001: Order subtotal from line items

**Source Reference:** `OrderServiceImpl.java:caculateOrder:172-233`; `OrderServiceImpl.java:caculateOrderTotal:329-341`
**Discovery Method:** Direct Source Read

**Statement:** The order subtotal is the sum, over every line in the basket being converted to an order, of the line's unit price multiplied by its quantity. When a line carries additional (non-default) price components, each one-time additional charge is also added to the subtotal, while recurring or informational additional prices are accumulated into a separate informational line and are not re-added to the subtotal.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
subTotal = 0
for each item in summary.products:
    st = item.itemPrice * item.quantity ; item.subTotal = st ; subTotal += st
    for each price in item.finalPrice.additionalPrices where !price.isDefaultPrice():
        accumulate into informational OrderTotal(type=PRODUCT, module="itemprice", sortOrder=0)
        if price.productPriceType == ONE_TIME: subTotal += price.finalPrice
totalSummary.subTotal = subTotal ; grandTotal = subTotal
emit OrderTotal{module="subtotal", type=SUBTOTAL, code="order.total.subtotal", sortOrder=5, value=subTotal}
```

**Data Dependencies:**
- Reads: cart line unit price / quantity, additional final-price components and their price type (`itemprice`, `subtotal` module constants)
- Writes: none (in-memory `OrderTotalSummary` during calculation)

**Side Effects:**
- None (no persistence; mutates in-memory line subtotal and builds the totals summary)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 2 | 2 | OK (itemprice, subtotal) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/calculate-total {"items":[{"sku":"SKU-1","unitPrice":49.95,"quantity":2}]}`
- Success: `200 {"totals":[{"code":"order.total.subtotal","value":99.90,"sortOrder":5}],"subTotal":99.90}`
- Error Input: `POST /api/v1/orders/calculate-total {"items":null}`
- Error Output: `422 {"error":"ValidationError","message":"order summary products are required"}`

---

### BR-ORD-002: Shipping total line

**Source Reference:** `OrderServiceImpl.java:caculateOrder:236-260`
**Discovery Method:** Direct Source Read

**Statement:** When a shipping quotation is present on the order, a shipping line is added to the order totals. If shipping is free, the shipping line records zero and contributes nothing to the grand total; otherwise the quoted shipping amount is recorded on the line and added to the grand total.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
if summary.shippingSummary != null:
    emit OrderTotal{module="shipping", type=SHIPPING, code="order.total.shipping", sortOrder=10}
    if !shippingSummary.isFreeShipping(): line.value = shippingSummary.shipping ; grandTotal += shippingSummary.shipping
    else:                                 line.value = 0 ;                        grandTotal += 0
```

**Data Dependencies:**
- Reads: shipping quotation free-shipping flag and shipping amount (from MS-08 quote result, BR-ORD-024/030)
- Writes: none

**Side Effects:**
- None (in-memory)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (shipping) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK (quote already fetched — see BR-ORD-030) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/calculate-total {"items":[...],"shipping":{"freeShipping":false,"shipping":12.50}}`
- Success: `200 {"totals":[...,{"code":"order.total.shipping","value":12.50,"sortOrder":10}]}`
- Error Input: shipping present but no `shipping` amount and not free → treated as zero contribution
- Error Output: `200` with shipping line value `0.00` (no error; degenerate quote yields zero shipping)

---

### BR-ORD-003: Handling fee line (conditional)

**Source Reference:** `OrderServiceImpl.java:caculateOrder:262-280`
**Discovery Method:** Direct Source Read

**Statement:** A handling fee is added to the order only when the shipping quotation carries a positive handling amount and the store is configured to charge handling fees. When both conditions hold, the handling amount is recorded as its own total line and added to the grand total.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
shippingConfiguration = shippingService.getShippingConfiguration(store)     # sync read (MS-08)
if shippingSummary.handling != null AND shippingSummary.handling > 0
   AND shippingConfiguration.handlingFees != null AND shippingConfiguration.handlingFees > 0:
      emit OrderTotal{module="handling", type=HANDLING, code="order.total.handling", sortOrder=12, value=shippingSummary.handling}
      grandTotal += shippingSummary.handling
```

**Data Dependencies:**
- Reads: shipping-quote handling amount; store shipping configuration handling-fee flag (MS-08 config read)
- Writes: none

**Side Effects:**
- Synchronous read to shipping configuration (MS-08). No DB write.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (handling) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (shipping config read) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/calculate-total {"items":[...],"shipping":{"handling":3.00}}` (store handling enabled)
- Success: `200 {"totals":[...,{"code":"order.total.handling","value":3.00,"sortOrder":12}]}`
- Error Input: `{"shipping":{"handling":3.00}}` with store handling disabled
- Error Output: `200` with NO handling line (condition not met — handling suppressed)

---

### BR-ORD-004: Tax total lines — tax entry point (cross-service calculator)

**Source Reference:** `OrderServiceImpl.java:caculateOrder:283-309`
**Discovery Method:** Direct Source Read

**Statement:** Tax enters the order money math here: the order asks the tax calculator for the tax owed on the basket (prices are tax-exclusive), and each returned tax component becomes its own labelled tax line on the order. The sum of all tax components is added once, in aggregate, to the grand total, and recorded as the order's tax total.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
taxes = taxService.calculateTax(summary, customer, store, language)   # sync stateless read (MS-07 /calculate)
if taxes not empty:
    totalTaxes = 0; taxCount = 20
    for each tax in taxes:
        emit OrderTotal{module="tax", type=TAX, code=tax.label, text=tax.label, sortOrder=taxCount, value=tax.itemPrice}
        totalTaxes += tax.itemPrice ; taxCount++
    grandTotal += totalTaxes            # aggregate add, NOT per line
    totalSummary.taxTotal = totalTaxes
```

**Data Dependencies:**
- Reads: tax components (label + amount) returned by the tax calculator (MS-07); `tax` module constant
- Writes: none

**Side Effects:**
- Synchronous stateless read to the tax service (MS-07). No DB write.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (tax; sortOrder base 20) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (tax calculate) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/calculate-total {"items":[{"unitPrice":100.00,"quantity":1}],"customer":{"zone":"QC"}}`
- Success: `200 {"totals":[...,{"code":"tax.GST","value":5.00,"sortOrder":20},{"code":"tax.QST","value":9.975,"sortOrder":21}],"taxTotal":14.975}`
- Error Input: tax calculator unreachable
- Error Output: `502 {"error":"UpstreamError","message":"tax calculation failed"}` (total cannot be finalized without the tax read)

---

### BR-ORD-005: Grand-total line, aggregation formula, and total ordering

**Source Reference:** `OrderServiceImpl.java:caculateOrder:311-326`
**Discovery Method:** Direct Source Read

**Statement:** The order grand total equals the subtotal plus shipping (unless free) plus any applicable handling plus the sum of all tax components. It is recorded as a final total line, and all order total lines are presented in a fixed display order (subtotal, shipping, handling, tax lines, grand total) driven by each line's sort order.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
emit OrderTotal{module="total", type=TOTAL, code="order.total.total", sortOrder=300, value=grandTotal}
totalSummary.total = grandTotal
GRAND_TOTAL = subTotal + (freeShipping ? 0 : shipping) + (handlingApplicable ? handling : 0) + SUM(taxItems.itemPrice)
totals displayed sorted by sortOrder: subtotal(5) < shipping(10) < handling(12) < tax(20..) < total(300)
informational itemprice(0) lines are NOT re-added to grandTotal (except ONE_TIME already folded in BR-ORD-001)
```

**Data Dependencies:**
- Reads: accumulated `grandTotal`, all emitted total lines; `total` module constant
- Writes: none

**Side Effects:**
- None (returns the completed `OrderTotalSummary`)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (total, sortOrder 300) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: subtotal 99.90, shipping 12.50, handling 3.00, tax 14.975
- Success: `200 {"totals":[...],"total":130.375}` (grand total = 99.90+12.50+3.00+14.975)
- Error Input: totals list built but grand-total line missing
- Error Output: internal consistency check fails — INV-ORD-002 violated (total must equal sum of components)

---

### BR-ORD-006: Monetary rounding intent — LATENT DEFECT (preserved + flagged)

**Source Reference:** `OrderServiceImpl.java:caculateOrder:180-181,185-186,289-290` (repeated `setScale(2, HALF_UP)` whose return value is discarded)
**Discovery Method:** Direct Source Read

**Statement:** The intended behavior is that monetary accumulators are rounded to two decimals using half-up rounding. In the legacy the rounding call has no effect because its result is discarded, so no canonical scale is actually applied at the total layer; the effective precision is whatever the upstream price and tax arithmetic yields.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
Intended: grandTotal/subTotal/totalTaxes rounded HALF_UP to scale 2.
Actual:   BigDecimal.setScale(2, HALF_UP) RETURN VALUE DISCARDED (BigDecimal is immutable)
          → accumulators are never re-scaled at this layer.
```

**Data Dependencies:**
- Reads: `grandTotal`, `subTotal`, `totalTaxes`
- Writes: none

**Side Effects:**
- None. The canonical monetary scale/rounding rule is a Phase 4a decision.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK (scale 2, HALF_UP intent) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (rounding not enforced at the calc layer — canonical scale/rounding is a 4a decision)

**Concrete Example:**
- Input: tax components 5.005 and 9.9749 summed into the grand total
- Success (legacy-faithful): `200 {"total":130.3799}` (no rounding applied at total layer — preserved)
- Error Input: consumer expects a 2-decimal money value
- Error Output: precision surprise (`130.3799` vs `130.38`) — the FLAG: target must decide the canonical scale

---

### BR-ORD-007: Calculate-order-total input validation

**Source Reference:** `OrderServiceImpl.java:caculateOrderTotal:329-341,345-357`; `OrderServiceImpl.java:calculateShoppingCartTotal:390-437`
**Discovery Method:** Direct Source Read

**Statement:** A total calculation request is rejected unless it carries a basket with a product list and a store context; the customer context is required only for the customer-aware calculation. Any failure during calculation surfaces as a service error rather than a partial result.
**Intent:** Validation
**Weight:** High

**Logic:**
```
caculateOrderTotal: require summary != null, summary.products != null, store != null
                    (customer required only for the customer-aware overload)
calculateShoppingCartTotal: require cart != null, store != null (customer required for customer overload)
on any calculation Exception → wrap in ServiceException
```

**Data Dependencies:**
- Reads: order summary / shopping cart, store, (customer)
- Writes: none

**Side Effects:**
- Throws a service error on failure; logs.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/calculate-total {"items":[{"unitPrice":10,"quantity":1}]}`
- Success: `200 {"total":10.00}`
- Error Input: `POST /api/v1/orders/calculate-total {}` (no items, no store header)
- Error Output: `422 {"error":"ValidationError","message":"order summary products and store are required"}`

---

### BR-ORD-008: Order placement orchestration — process sequence (checkout saga step)

**Source Reference:** `OrderServiceImpl.java:process:108-166` (via `OrderServiceImpl.java:processOrder:96,102`)
**Discovery Method:** Direct Source Read

**Statement:** Placing an order runs a fixed sequence: charge the payment, then assign the order's initial status and open its status history if none exists, then ensure the customer record exists, then persist the order together with its products, totals and status history, then record the payment transaction against the order. In the modernized design this is a saga: the charge is a distributed step with an idempotency key, and a reconciliation job guarantees no order reaches a settled state without a captured payment. On success the service publishes an order-placed event.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
require order, customer, items (non-empty), payment, store, summary all non-null
# SAGA step 1 — CHARGE (distributed, idempotent on checkout idempotency key)
processTransaction = paymentService.processPayment(customer, store, payment, items, order)   # MS-10 charge endpoint
# step 2 — initial status
if order has no history OR no status: status = order.status ?? ORDERED; order.status = status
                                      order.orderHistory += OrderStatusHistory(status, dateAdded=now, order)
# step 3 — ensure customer
if customer.id in {null,0}: customerService.create(customer)      # MS-05
order.customerId = customer.id
# SAGA step 4 — PERSIST (local tx: INSERT ORDERS + cascade products/totals/history)
create(order)
# step 5/6 — record payment txn(s) against the order
if transaction != null: create/update transaction
if processTransaction != null: create/update processTransaction
publish order.placed
return order
```

**Data Dependencies:**
- Reads: order aggregate, customer id, payment instruction, order summary
- Writes: `orders` (+ cascade `order_product`, `order_total`, `order_status_history`); records payment transaction linkage; (MS-05 customer create if new)

**Side Effects:**
- Charge step invokes MS-10 (saga CHARGE); persists the order aggregate locally (saga PERSIST); publishes `order.placed`. Charge happens BEFORE the order row is persisted — the charge-vs-persist window is covered by the reconciler (Architecture §7: no PROCESSED order without a CAPTURED transaction). NOT 2PC.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 1 | 1 | OK (ORDERED default) |
| State transitions | 2 | 2 | OK (→ORDERED, history opened) |
| Outcomes | 2 | 2 | OK |
| Data writes | 4 | 4 | OK (orders + 3 cascades) |
| Integrations | 3 | 3 | OK (payment charge, customer, txn record) |
| Error paths | 1 | 2 | GAP (added saga compensation/reconciliation path — net-new for D-08) |

**Preservation:** FLAGGED (Error paths — modernized adds the saga reconciliation/compensation path absent in the legacy synchronous flow; intentional per D-08)

**Concrete Example:**
- Input: `POST /api/v1/orders {"idempotencyKey":"chk-abc","cart":{...},"payment":{"paymentType":"CreditCard",...},"customer":{...}}`
- Success: `201 {"orderId":"ORD-5001","status":"Ordered","total":130.38}` (publishes `order.placed`)
- Error Input: charge succeeds but persist fails
- Error Output: `500`; reconciler later detects the CAPTURED transaction with no PROCESSED order and drives compensation/retry (money-safety net)

---

### BR-ORD-009: Initial order status defaults to Ordered

**Source Reference:** `OrderServiceImpl.java:process:120-131`; `OrderFacadeImpl.java:initializeOrder:135`
**Discovery Method:** Direct Source Read

**Statement:** A newly placed order that arrives without a status is opened in the initial "ordered" state, and a matching status-history entry is recorded with the current timestamp. Order initialization also seeds the ordered state on the working order.
**Intent:** State Transition
**Weight:** High

**Logic:**
```
if order.status == null → status = ORDERED
write OrderStatusHistory{status, dateAdded=now}
facade.initializeOrder seeds orderStatus = ORDERED
```

**Data Dependencies:**
- Reads: order status; Writes: `orders.order_status`, `order_status_history`

**Side Effects:**
- Writes the initial status-history row on create.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (ORDERED) |
| State transitions | 1 | 1 | OK (→Ordered) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: order placed with no explicit status
- Success: `201 {"status":"Ordered","statusHistory":[{"status":"Ordered","date":"2026-01-01T12:00:00Z"}]}`
- Error Input: order created with an unknown status value
- Error Output: `422 {"error":"ValidationError","message":"unknown order status"}`

---

### BR-ORD-010: Append order status-history entry

**Source Reference:** `OrderServiceImpl.java:addOrderStatusHistory:85-90`
**Discovery Method:** Direct Source Read

**Statement:** A status change on an order is recorded by appending a status-history entry bound to that order and persisting the order. The legacy places no guard on the value or the legality of the transition being recorded.
**Intent:** State Transition
**Weight:** High

**Logic:**
```
order.orderHistory.add(history) ; history.order = order ; update(order)   # cascade INSERT of history
# NO guard on status value or transition legality (see status-lifecycle flag)
```

**Data Dependencies:**
- Reads: order, submitted history; Writes: `order_status_history` (via cascade on order update)

**Side Effects:**
- Inserts a status-history row. No transition-legality check (flagged — see 02-domain-model status lifecycle).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/ORD-5001/status-history {"status":"Processed","comment":"packed","customerNotified":true}`
- Success: `201 {"orderId":"ORD-5001","status":"Processed"}`
- Error Input: `POST /api/v1/orders/ORD-5001/status-history {"status":"Banana"}`
- Error Output: `422 {"error":"ValidationError","message":"unknown order status"}`

---

### BR-ORD-011: Create-vs-update discriminator on save

**Source Reference:** `OrderServiceImpl.java:saveOrUpdate:454-464`
**Discovery Method:** Direct Source Read

**Statement:** When an order is saved, an order that already has an identity is updated in place; an order without one is created as new.
**Intent:** Routing
**Weight:** High

**Logic:**
```
if order.id != null AND order.id > 0 → update(order) else create(order)
```

**Data Dependencies:**
- Reads: order id; Writes: `orders` (+ cascade)

**Side Effects:**
- Insert or update of the order aggregate.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/orders/ORD-5001 {...}` (existing id)
- Success: `200 {"orderId":"ORD-5001"}` (update path)
- Error Input: `PUT /api/v1/orders/ORD-9999 {...}` (id not found)
- Error Output: `404 {"error":"NotFound","message":"order not found"}`

---

### BR-ORD-012: Order has downloadable (virtual) products

**Source Reference:** `OrderServiceImpl.java:hasDownloadFiles:469-485`
**Discovery Method:** Direct Source Read

**Statement:** An order is considered to contain downloadable goods when at least one of its ordered products carries one or more download entries. This determines whether the download notification is sent after placement.
**Intent:** Validation
**Weight:** High

**Logic:**
```
require order != null, order.orderProducts non-empty
return exists op in order.orderProducts where op.downloads is non-empty
```

**Data Dependencies:**
- Reads: order products and their download entries; Writes: none

**Side Effects:**
- None (consumed to decide sending the download email, BR-ORD-025).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/orders/ORD-5001/downloads`
- Success: `200 {"hasDownloads":true,"downloads":[{"downloadId":"DL-1","filename":"ebook.pdf"}]}`
- Error Input: `GET /api/v1/orders/ORD-5001/downloads` for an order with no products
- Error Output: `200 {"hasDownloads":false,"downloads":[]}`

---

### BR-ORD-013: Generate order invoice (PDF)

**Source Reference:** `OrderServiceImpl.java:generateInvoice:414-431`
**Discovery Method:** Direct Source Read

**Statement:** An invoice can be produced for an order only when the order has both line items and totals; the invoice document is rendered by the invoicing capability for the given store and language.
**Intent:** Routing
**Weight:** High

**Logic:**
```
require order.orderProducts != null AND order.orderTotal != null
return invoiceModule.createInvoice(store, order, language)      # PDF byte stream
```

**Data Dependencies:**
- Reads: order products, order totals; Writes: none

**Side Effects:**
- Delegates to the invoice module (external capability); returns a PDF stream.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (invoice module) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/orders/ORD-5001/invoice`
- Success: `200 application/pdf` (invoice bytes)
- Error Input: `GET /api/v1/orders/ORD-5001/invoice` for an order missing totals
- Error Output: `409 {"error":"Conflict","message":"order has no totals to invoice"}`

---

### BR-ORD-014: Order lookup eager-load graph

**Source Reference:** `OrderDaoImpl.java:getById:29-52`
**Discovery Method:** Direct Source Read

**Statement:** Fetching a single order returns the full order aggregate — its products, totals, status history, downloads, product attributes and product prices — in one read. Because products and totals are joined as required associations, an order with no products or no totals will not be returned by this lookup.
**Intent:** Routing
**Weight:** High

**Logic:**
```
SELECT order INNER JOIN orderProducts INNER JOIN orderTotal
             LEFT JOIN orderHistory LEFT JOIN orderProduct.downloads
             LEFT JOIN orderProduct.orderAttributes LEFT JOIN orderProduct.prices
WHERE order.id = :id
# INNER joins on products+totals: order with zero products/totals is NOT returned
```

**Data Dependencies:**
- Reads: `orders`, `order_product`, `order_total`, `order_status_history`, `order_product_download`, `order_product_attribute`, `order_product_price`; Writes: none

**Side Effects:**
- Read-only.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 7 | 7 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (found / not-returned) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/orders/ORD-5001`
- Success: `200 {"orderId":"ORD-5001","products":[...],"totals":[...],"statusHistory":[...]}`
- Error Input: `GET /api/v1/orders/ORD-5001` where the order has zero totals
- Error Output: `404 {"error":"NotFound","message":"order not found"}` (required-association join excludes it — preserved behavior)

---

### BR-ORD-015: List orders by store with dynamic criteria and paging

**Source Reference:** `OrderDaoImpl.java:listByStore:57-166`
**Discovery Method:** Direct Source Read

**Statement:** Orders can be browsed for a store with optional filters on customer name, payment method and customer identity, ordered by purchase date, and returned as a page with a total count. The legacy count query combines the name filters without grouping while the page query groups them, so the reported total can be broader than the returned page for a name search.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
count: count(o) where merchant.id=:mId [+ firstName like %n% OR lastName like %n%] [+ paymentModuleCode like %pm%] [+ customerId=:cid]
if count == 0 → empty
fetch: same filters, eager-load, orderBy datePurchased ASC|DESC, limit=maxCount offset=startIndex
list.totalCount = count
# count query mixes and/or without parentheses; page query parenthesizes (firstName OR lastName)
```

**Data Dependencies:**
- Reads: `orders.merchant_id`, billing name, payment module code, customer id, purchase date; Writes: none

**Side Effects:**
- Read-only.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | GAP (operator-precedence divergence flagged — 4a) |

**Preservation:** FLAGGED (count/page filter precedence divergence — Low confidence, carried to 4a)

**Concrete Example:**
- Input: `GET /api/v1/orders?name=smith&page=1&pageSize=20&sort=datePurchased:desc`
- Success: `200 {"items":[...],"pagination":{"totalItems":42,"page":1,"pageSize":20}}`
- Error Input: `GET /api/v1/orders?pageSize=-5`
- Error Output: `422 {"error":"ValidationError","message":"pageSize must be positive"}`

---

### BR-ORD-016: Downloads by order id

**Source Reference:** `OrderProductDownloadDaoImpl.java:getByOrderId:41-56`; `OrderProductDownloadServiceImpl.java:getByOrderId:53-55`
**Discovery Method:** Direct Source Read

**Statement:** The download entries for an order are retrieved by joining the order's products to their download entries for the given order, scoped to the owning store.
**Intent:** Routing
**Weight:** High

**Logic:**
```
SELECT download JOIN orderProduct JOIN order JOIN merchant WHERE order.id = :orderId
# getById filters by download id instead
```

**Data Dependencies:**
- Reads: `order_product_download`, `order_product`, `orders`, store; Writes: none

**Side Effects:**
- Read-only.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/orders/ORD-5001/downloads`
- Success: `200 {"downloads":[{"downloadId":"DL-1","filename":"ebook.pdf","maxDays":31,"downloadCount":0}]}`
- Error Input: `GET /api/v1/orders/ORD-XXXX/downloads` (no such order)
- Error Output: `404 {"error":"NotFound","message":"order not found"}`

---

### BR-ORD-017: Checkout order-total facade orchestration

**Source Reference:** `OrderFacadeImpl.java:calculateOrderTotal:154-162,190-213`; `OrderFacadeImpl.java:setOrderTotals:231-247`
**Discovery Method:** Direct Source Read

**Statement:** During checkout the order-total request is assembled from the basket lines and optional shipping quotation, delegated to the authoritative total calculation, and each resulting total line is mapped onto the order for display. The persistable-order calculation path is explicitly unsupported.
**Intent:** Calculation
**Weight:** High

**Logic:**
```
build OrderSummary from order.shoppingCartItems (+ shippingSummary)
summary = orderService.caculateOrderTotal(orderSummary, customer, store, language)   # BR-ORD-001..005
setOrderTotals(order, summary): map each core OrderTotal → display total (code,title,value)
PersistableOrder path → not implemented (throws)
```

**Data Dependencies:**
- Reads: basket lines, shipping summary, computed totals; Writes: none (sets display totals on the working order)

**Side Effects:**
- None persisted.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (delegates to owned total calc) |
| Error paths | 1 | 1 | OK (unsupported persistable path) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/calculate-total {"cartCode":"CART-1"}`
- Success: `200 {"totals":[{"code":"order.total.subtotal","title":"Subtotal","value":99.90},...]}`
- Error Input: calculate-total requested against a persistable-order shape
- Error Output: `501 {"error":"NotImplemented","message":"calculateOrderTotal not supported for persistable order"}`

---

### BR-ORD-018: Cart-to-order snapshot (order-product materialization)

**Source Reference:** `OrderFacadeImpl.java:processOrderModel:267-343`
**Discovery Method:** Direct Source Read

**Statement:** When a cart is converted to an order, the order captures a point-in-time snapshot: purchase date, billing and delivery addresses, payment and shipping method identifiers, store locale and currency, and for every basket line an ordered-product record with its sku, name, quantity, prices, attributes and downloads. Totals are attached in display order and the order grand total is recorded.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
order.datePurchased = now ; order.billing = customer.billing ; order.delivery = customer.delivery
order.paymentModuleCode/paymentType/shippingModuleCode set from submitted order
order.locale = store locale ; order.currency = store.currency ; order.merchant = store
for each cart item: op = OrderProductPopulator.populate(item, ...) ; op.order = order ; add
sort summary.totals by sortOrder ASC ; bind each total.order = order ; order.orderTotal = totals
order.total = summary.total
```

**Data Dependencies:**
- Reads: cart items → ordered-product snapshot (sku, name, qty, prices, attributes, downloads), totals, store; Writes: builds the full aggregate in memory (persisted by BR-ORD-008)

**Side Effects:**
- Builds the order aggregate (price/attribute snapshot frozen at placement time).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 8 | 8 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (cart → order snapshot) |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK (in-memory; persisted in BR-ORD-008) |
| Integrations | 1 | 1 | OK (cart source MS-06) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders {"cartCode":"CART-1",...}`
- Success: `201 {"orderId":"ORD-5001","products":[{"sku":"SKU-1","quantity":2,"price":49.95}],"total":130.38}`
- Error Input: cart line references a product with no resolvable price
- Error Output: `422 {"error":"ValidationError","message":"cart item price could not be resolved"}`

---

### BR-ORD-019: Ship-to-billing address collapse

**Source Reference:** `OrderFacadeImpl.java:processOrderModel:273-277`; `ShoppingOrderController.java:commitOrder:398-400`
**Discovery Method:** Direct Source Read

**Statement:** When the shopper elects to ship to the billing address, the delivery address on the order is set equal to the billing address.
**Intent:** Derivation
**Weight:** High

**Logic:**
```
if order.isShipToBillingAdress(): customer.delivery = customer.billing
```

**Data Dependencies:**
- Reads: ship-to-billing flag, billing address; Writes: delivery address on the order

**Side Effects:**
- Mutates delivery used for the persisted order.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders {"shipToBillingAddress":true,"billing":{"city":"Boston"}}`
- Success: `201 {"delivery":{"city":"Boston"}}` (delivery mirrors billing)
- Error Input: `shipToBillingAddress:false` with no delivery address supplied
- Error Output: `422 {"error":"ValidationError","message":"delivery address required"}` (BR-ORD-022)

---

### BR-ORD-020: Payment instrument assembly and card masking — PCI FLAG (preserved)

**Source Reference:** `OrderFacadeImpl.java:processOrderModel:344-410`
**Discovery Method:** Direct Source Read

**Statement:** The payment instrument is assembled from the submitted checkout fields. For a card payment, the card brand is resolved and only a masked card number is stored on the order; the raw number goes to the payment processor, not the order record. For a PayPal payment, a prior transaction (payer id and token) is required. The stored card record also embeds card holder, expiry and CVV field.
**Intent:** Derivation
**Weight:** Critical

**Logic:**
```
payment.paymentType = order.paymentMethodType
if CREDITCARD: resolve brand in {AMEX,VISA,MASTERCARD,DINERS,DISCOVERY}
               cc = CreditCard(type, cvv, owner, expires "MM-YYYY")
               cc.ccNumber = maskCardNumber(rawNumber)     # ONLY masked PAN stored on order
               order.creditCard = cc
if PAYPAL: require prior transaction else error; build PaypalPayment(PAYERID, TOKEN)
```

**Data Dependencies:**
- Reads: submitted payment fields, card type, prior transaction (PayPal); Writes: masked card record embedded on the order

**Side Effects:**
- Persisted order stores masked PAN only (CVV/owner/expiry embedded — PCI concern). Raw PAN routed to MS-10, not persisted here.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 1 | 1 | OK (card-type set) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK (masked card on order) |
| Integrations | 1 | 1 | OK (payment) |
| Error paths | 1 | 1 | OK |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (masked-PAN persistence + embedded CVV/owner — PCI/PII; target should tokenize / never-persist; masking preserved for 4a)

**Concrete Example:**
- Input: `POST /api/v1/orders {"payment":{"paymentType":"CreditCard","number":"4111111111111111","holder":"J Doe","cvv":"123","expiryMonth":12,"expiryYear":2028}}`
- Success: `201 {"payment":{"maskedNumber":"XXXXXXXXXXXX1111","cardType":"Visa"}}`
- Error Input: `POST /api/v1/orders {"payment":{"paymentType":"Paypal"}}` with no prior transaction
- Error Output: `422 {"error":"ValidationError","message":"payment.error: paypal transaction required"}`

---

### BR-ORD-021: Process-order transaction-branch dispatch — LIKELY DEFECT (preserved + flagged)

**Source Reference:** `OrderFacadeImpl.java:processOrderModel:412-416`
**Discovery Method:** Direct Source Read

**Statement:** When placing the order, the code selects between two placement paths based on whether a pre-authorization transaction exists. The two branches appear inverted, so the previously created pre-authorization (e.g. a PayPal express transaction) is not forwarded on the transaction-bearing path.
**Intent:** Routing
**Weight:** High

**Logic:**
```
if transaction != null: processOrder(order, customer, items, summary, payment, store)          # 6-arg — transaction DROPPED
else:                   processOrder(order, customer, items, summary, payment, transaction, store) # 7-arg — passes null
# net: pre-auth transaction linkage lost on the transaction path
```

**Data Dependencies:**
- Reads: pre-auth transaction; Writes: order (transaction linkage possibly lost)

**Side Effects:**
- Possible loss of pre-auth transaction linkage on the order.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 1 | GAP (defect: dropped transaction path) |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (inverted branch drops pre-auth transaction linkage — cannot confirm intent from code; carried to 4a)

**Concrete Example:**
- Input: PayPal pre-authorized checkout commit (a prior transaction exists)
- Success (legacy-faithful): `201 {"orderId":"ORD-5001"}` but the pre-auth transaction is not linked (preserved defect)
- Error Input: consumer expects the order to reference the pre-auth transaction
- Error Output: transaction linkage missing — the FLAG for 4a (fix vs preserve)

---

### BR-ORD-022: Order submission validation (billing / delivery / payment / shipping / card)

**Source Reference:** `OrderFacadeImpl.java:validateOrder:555-745`
**Discovery Method:** Direct Source Read

**Statement:** An order submission is validated before placement: billing must carry name, email, address, city, country, a region or state, phone and postal code; when not shipping to billing, delivery must carry name, address, city, country, region-or-state and postal code; a payment type is mandatory; a shipping option is mandatory when the basket requires shipping; and for a card payment the holder, security code, number, expiry month and year are mandatory and the brand must be resolvable.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
billing required: firstName,lastName,email,address,city,country,(zone OR state),phone,postalCode
if !shipToBilling: delivery required: firstName,lastName,address,city,country,(zone OR state),postalCode
if paymentType == null → error "payment.required"
if requiresShipping(items,store) AND selectedShippingOption == null → error "shipping.required"
if CREDITCARD: require holder,cvv,number,expMonth,expYear ; require brand resolvable else "cc.type"
```

**Data Dependencies:**
- Reads: billing/delivery fields, payment type, shipping option, card fields; Writes: none

**Side Effects:**
- Surfaces field errors; throws validation errors for payment/shipping/card failures.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 6 | 6 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (requiresShipping — MS-08) |
| Error paths | 4 | 4 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/validate {"billing":{"firstName":"J","lastName":"D","email":"j@x.com","country":"US"},"paymentType":"CreditCard"}`
- Success: `200 {"valid":true}`
- Error Input: `POST /api/v1/orders/validate {"paymentType":null}`
- Error Output: `422 {"error":"ValidationError","message":"payment.required"}`

---

### BR-ORD-023: Empty-customer prefill from store defaults

**Source Reference:** `OrderFacadeImpl.java:initEmptyCustomer:443-461`; `OrderFacadeImpl.java:initializeOrder:127-149`
**Discovery Method:** Direct Source Read

**Statement:** A new anonymous checkout customer is prefilled with the store's default country, region, state and postal code on both the billing and delivery addresses.
**Intent:** Derivation
**Weight:** High

**Logic:**
```
new Customer.billing/delivery.{country,zone,state,postalCode} = store defaults
```

**Data Dependencies:**
- Reads: store default country/zone/state/postal code; Writes: none (in-memory form default)

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (store reference MS-03) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/orders/checkout-context` (new anonymous checkout)
- Success: `200 {"customer":{"billing":{"country":"US","state":"MA","postalCode":"02101"}}}`
- Error Input: store has no default country configured
- Error Output: `200 {"customer":{"billing":{"country":null}}}` (blank default — no error)

---

### BR-ORD-024: Shipping summary derivation from quote

**Source Reference:** `OrderFacadeImpl.java:getShippingSummary:534-552`
**Discovery Method:** Direct Source Read

**Statement:** When a shipping option has been selected on the quotation, a shipping summary is derived carrying the free-shipping flag, whether tax applies to shipping, the handling amount, the selected option's price, and the chosen option and module identifiers. With no selected option, no summary is produced.
**Intent:** Derivation
**Weight:** High

**Logic:**
```
if quote.selectedShippingOption != null:
   ShippingSummary{freeShipping, taxOnShipping=quote.applyTaxOnShipping, handling=quote.handlingFees,
                   shipping=selectedOption.optionPrice, shippingOption=name, shippingModule=code}
else null
```

**Data Dependencies:**
- Reads: shipping quotation fields (MS-08); Writes: none (feeds BR-ORD-002/003/004)

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (quote MS-08) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/shipping-summary {"selectedShippingOption":{"code":"weight","optionPrice":12.50}}`
- Success: `200 {"shipping":12.50,"freeShipping":false,"shippingModule":"weight"}`
- Error Input: `POST /api/v1/orders/shipping-summary {"selectedShippingOption":null}`
- Error Output: `200 {"shippingSummary":null}` (no option chosen — no summary)

---

### BR-ORD-025: Checkout commit — provisioning, cart teardown, notifications, order-placed publish

**Source Reference:** `ShoppingOrderController.java:commitOrder:367-511`; `ShoppingOrderController.java:commitOrder:513-712`; `ShoppingOrderController.java:commitPreAuthorizedOrder:327-361`
**Discovery Method:** Direct Source Read

**Statement:** On a successful checkout commit the shopper is provisioned (an anonymous shopper gets a generated volatile account), the placed order is persisted, the shopping cart is consumed and cleared, and confirmation, registration and download notifications are sent as applicable. Post-placement notification or sign-in failures are logged and do not roll back the order. An order-placed event is published for downstream consumers.
**Intent:** State Transition
**Weight:** High

**Logic:**
```
if authenticated: reuse customer else customer.id = null
if customer.id in {null,0}: generate password ; encode ; volatile customer
if shipToBilling: delivery = billing
save customer ; transaction = session pre-auth (if any)
order = processOrder(...)                      # BR-ORD-008 (saga)
delete shopping cart (cart consumed — MS-06)
send confirmation email ; if new customer send registration email ; if hasDownloads send download email  # failures caught+logged
publish order.placed
```

**Data Dependencies:**
- Reads: session/checkout state, customer, order; Writes: creates volatile customer (MS-05), persists order (BR-ORD-008), deletes cart (MS-06)

**Side Effects:**
- Creates volatile customer, persists order, deletes cart, sends up to 3 emails, publishes `order.placed`. Email/auth post-processing failures do NOT roll back the order.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 2 | 2 | OK (order placed; cart consumed) |
| Outcomes | 2 | 2 | OK |
| Data writes | 3 | 3 | OK (customer, order, cart delete) |
| Integrations | 4 | 4 | OK (customer, cart, email, publish) |
| Error paths | 2 | 2 | OK (notify failure swallowed) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders {"idempotencyKey":"chk-abc","cartCode":"CART-1","payment":{...},"customer":{...}}`
- Success: `201 {"orderId":"ORD-5001","status":"Ordered"}` (cart cleared; `order.placed` published)
- Error Input: order persisted but confirmation email transport down
- Error Output: `201 {"orderId":"ORD-5001"}` with a logged notification warning (order NOT rolled back — preserved)

---

### BR-ORD-026: Checkout cart resolution and payment-method selection

**Source Reference:** `ShoppingOrderController.java:commitOrder:513-645`
**Discovery Method:** Direct Source Read

**Statement:** Checkout resolves the active cart from the session or a cart cookie scoped to the store, rejecting a cart that belongs to a different store or has expired. It requires at least one enabled payment method unless the cart is free, defaults the payment method selection, computes (or reuses the cached) totals, and validates the submission before proceeding.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
resolve cart code from session else cookie "store_cart"; if cookie store != this store → timeout
if cart code blank → timeout ; cart = getShoppingCartModel(code, store)
methods = acceptedPaymentMethods(store) ; freeCart = isFreeCart(cart)
if methods empty AND !freeCart → error "no payments configured"
pick default method (else force first) ; quote shipping ; totals = cached ?? calculateOrderTotal(...)
validateOrder(...) → errors return checkout view
```

**Data Dependencies:**
- Reads: cart code, store code, payment methods, shipping quote, totals; Writes: session totals/shipping cache

**Side Effects:**
- Session writes; returns checkout/timeout view on failure.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK (session only) |
| Integrations | 3 | 3 | OK (cart, payment methods, shipping) |
| Error paths | 3 | 3 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/checkout-context {"cartCode":"CART-1"}`
- Success: `200 {"paymentMethods":[{"code":"paypal","default":true}],"totals":[...]}`
- Error Input: cart cookie references a different store
- Error Output: `410 {"error":"Gone","message":"cart session expired"}`

---

### BR-ORD-027: PayPal Express pre-authorization initiation

**Source Reference:** `ShoppingOrderPaymentController.java:paymentAction:117-238`; `ShoppingOrderPaymentController.java:returnPayPalPayment:243-251`
**Discovery Method:** Direct Source Read

**Statement:** For a PayPal express checkout the order is validated, the totals are computed or reused, and a pre-authorization is initiated with the external provider. The returned token is recorded as a transaction and the shopper is redirected to the provider's approval page; on approval the flow proceeds to the pre-authorized commit, otherwise back to checkout.
**Intent:** Routing
**Weight:** High

**Logic:**
```
require cart ; validateOrder(...) → on messages return VALIDATION_FAILED
config = paymentConfiguration(module, store) ; totals = cached ?? calculateOrderTotal(...)
if action==init AND method==PAYPAL:
   txn = initPaypalTransaction(store, items, summary, payment, config, module)   # external HTTP (MS-10 SPI)
   record transaction ; stash pre-auth + order ; return approval URL (prod/sandbox × device)
returnPayPalPayment: SUCCESS → commitPreAuthorized else checkout
```

**Data Dependencies:**
- Reads: payment configuration, integration module, provider token, environment URLs; Writes: records a payment transaction (MS-10)

**Side Effects:**
- External PayPal set-express-checkout call; records a pre-auth transaction; session writes.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 2 | 2 | OK (init/PAYPAL, URLs) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK (transaction — via MS-10) |
| Integrations | 2 | 2 | OK (payment init, redirect) |
| Error paths | 2 | 2 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/payment/init/paypal {"cartCode":"CART-1"}`
- Success: `200 {"redirectUrl":"https://www.paypal.com/checkoutnow?token=EC-123"}`
- Error Input: validation fails (missing billing)
- Error Output: `422 {"error":"ValidationError","messages":["billing.required"]}`

---

### BR-ORD-028: Order confirmation display and store-ownership guard

**Source Reference:** `ShoppingOrderConfirmationController.java:displayConfirmation:104-186`
**Discovery Method:** Direct Source Read

**Statement:** The order confirmation view is shown only for an order that belongs to the current store; an order from another store is refused. A one-time confirmation flag, keyed to the placement session, is exposed once and then cleared, and the order's downloads are listed.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
orderId = session ORDER_ID ; if null → redirect
order = getById(orderId) ; if null → error
if order.merchant.id != store.id → redirect        # cross-store guard
if session ORDER_ID_TOKEN present → expose one-time "confirmation"; remove token
resolve country/zone display names ; list downloads
```

**Data Dependencies:**
- Reads: order merchant id, session confirmation token, downloads; Writes: clears the one-time token

**Side Effects:**
- Removes the one-time confirmation token; otherwise read-only.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK (session token cleared) |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/orders/ORD-5001/confirmation` (store owns ORD-5001)
- Success: `200 {"orderId":"ORD-5001","justConfirmed":true,"downloads":[...]}`
- Error Input: `GET /api/v1/orders/ORD-5001/confirmation` from a different store context
- Error Output: `403 {"error":"Forbidden","message":"order does not belong to this store"}`

---

### BR-ORD-029: Admin order edit — status change, history and audit fields

**Source Reference:** `OrderControler.java:saveOrder:211-375`
**Discovery Method:** Direct Source Read

**Statement:** An administrator can edit an order's billing and delivery details and change its status; the status assignment is unguarded so any status may be set from any status. When a comment is supplied a status-history entry is recorded with the customer-notified flag, and the last-modified timestamp is updated.
**Intent:** State Transition
**Weight:** High

**Logic:**
```
validate email + billing name/address/city/(zone or state)/postalCode
newOrder = getById(order.id) ; if !MONEYORDER: fetch capturable/refundable for UI
if errors → return edit view
newOrder.status = submitted.status              # FREE assignment — NO transition guard
newOrder.lastModified = now
if comment present: history{comment, customerNotified=1, status, dateAdded=now} ; add
saveOrUpdate(newOrder)
```

**Data Dependencies:**
- Reads: submitted order fields; Writes: `orders` status/date/billing/delivery, `order_status_history`

**Side Effects:**
- Updates the order; inserts a status-history row when a comment is present. Confirms the status lifecycle has NO enforced transition rules.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (free assignment — unguarded) |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (capturable/refundable lookup) |
| Error paths | 1 | 1 | OK |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (free status assignment — the legal transition set is not encoded in legacy; carried to 4a, see status lifecycle)

**Concrete Example:**
- Input: `PATCH /api/v1/orders/ORD-5001/status {"status":"Delivered","comment":"handed to courier","customerNotified":true}`
- Success: `200 {"orderId":"ORD-5001","status":"Delivered"}`
- Error Input: `PATCH /api/v1/orders/ORD-5001/status {"customerEmailAddress":"not-an-email"}`
- Error Output: `422 {"error":"ValidationError","message":"invalid customer email"}`

---

### BR-ORD-030: Admin capture / refund payment (cross-service calls)

**Source Reference:** `OrderActionsControler.java:captureOrder:89-137`; `OrderActionsControler.java:refundOrder:142-225`
**Discovery Method:** Direct Source Read

**Statement:** An authorized administrator can capture or refund payment for an order that belongs to the current store. Capture requires a resolvable customer; refund requires a positive amount that does not exceed the order total and a resolvable customer. Both delegate to the payment capability; the resulting settlement facts return to the order as payment events.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
@hasRole ORDER ; order = getById(id) ; require order != null AND order.merchant.id == store.id
capture: customer = getById(order.customerId) ; require customer != null ; paymentService.processCapturePayment(order,customer,store)
refund:  amount = parse(refund.amount) ; reject if amount == 0, amount > order.total, amount <= 0
         require customer != null ; paymentService.processRefund(order,customer,store,amount)
# settlement facts applied to order via payment.captured / payment.refunded (BV-2)
```

**Data Dependencies:**
- Reads: order total, customer id, refund amount; Writes: none locally (settlement applied via consumed events)

**Side Effects:**
- Invokes MS-10 capture/refund. Order status/total effects arrive as `payment.captured` / `payment.refunded` (consumed, idempotent on transactionId) — NOT a direct write from payment.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK (state change applied via consumed event) |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (payment capture/refund) |
| Error paths | 3 | 3 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/orders/ORD-5001/refund {"amount":50.00}`
- Success: `202 {"orderId":"ORD-5001","refundRequested":50.00}` (settlement fact returns via `payment.refunded`)
- Error Input: `POST /api/v1/orders/ORD-5001/refund {"amount":9999.00}` (> order total 130.38)
- Error Output: `422 {"error":"ValidationError","message":"refund amount exceeds order total"}`

---

### BR-ORD-031: REST create order — persistence without payment orchestration (flagged)

**Source Reference:** `OrderRESTController.java:createOrder:73-115`
**Discovery Method:** Direct Source Read

**Statement:** An integration channel can create an order directly from a submitted payload, persisting the order and its customer without running the payment charge or the placement status seeding. This channel behaves differently from storefront checkout.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
resolve store by code (503 if null)
if customer present: save customer ; set id back
populate order (products/attributes/downloads)
orderService.save(order)          # DIRECT save — bypasses process()/payment/status seeding
return created order (201)
```

**Data Dependencies:**
- Reads: submitted order/customer; Writes: `orders`, `customer` (MS-05), `order_product`

**Side Effects:**
- Inserts order + customer. Does NOT run BR-ORD-008 (no charge, no status-history seeding beyond populator).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (customer) |
| Error paths | 1 | 1 | GAP (no payment/status orchestration — behavioral divergence flagged) |

**Preservation:** FLAGGED (integration-channel path bypasses checkout orchestration — confirm at 4a whether it should converge)

**Concrete Example:**
- Input: `POST /api/v1/integration/orders {"customer":{...},"products":[...]}`
- Success: `201 {"orderId":"ORD-7001"}` (no charge performed)
- Error Input: `POST /api/v1/integration/orders {}` for an unknown store
- Error Output: `503 {"error":"ServiceUnavailable","message":"store not found"}`

---

### BR-ORD-032: Virtual product download delivery — SECURITY FLAG (IDOR + unenforced limits, preserved)

**Source Reference:** `ShoppingOrderDownloadController.java:downloadFile:59-113`
**Discovery Method:** Direct Source Read

**Statement:** An authenticated shopper can download a digital product file identified by an order and a download entry. The legacy does not verify that the requested order or download belongs to the signed-in shopper, and it neither increments the download count nor enforces the maximum-days window even though those policy fields exist.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
@hasRole AUTH_CUSTOMER
order = getById(orderId) ; if null → 404
customer = session ; if null → 404
download = getById(id) ; if null → 404
file = contentService.getContentFile(store.code, PRODUCT_DIGITAL, download.orderProductFilename)
if file != null → stream bytes else 404
# NO ownership check (orderId/download vs customer) → IDOR
# NO downloadCount increment, NO maxdays enforcement (fields DOWNLOAD_MAXDAYS default 31, DOWNLOAD_COUNT exist)
```

**Data Dependencies:**
- Reads: order, download filename, content store; Writes: none (should increment download count — not done)

**Side Effects:**
- Streams file bytes. Missing ownership check and missing download-limit enforcement.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK (maxdays 31, download-count field) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | GAP (download count never incremented — preserved) |
| Integrations | 1 | 1 | OK (content store) |
| Error paths | 3 | 3 | OK |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] ((a) no owner check → potential IDOR; (b) no downloadCount increment / no maxdays enforcement — both preserved and carried to 4a)

**Concrete Example:**
- Input: `GET /api/v1/orders/ORD-5001/downloads/DL-1/file` (signed-in shopper)
- Success: `200 application/octet-stream` (Content-Disposition attachment — file bytes)
- Error Input: `GET /api/v1/orders/ORD-9999/downloads/DL-2/file` for another shopper's order (legacy-faithful: still served — IDOR)
- Error Output: `404` only when the file/entry is missing — the FLAG: no authorization/limit failure is raised (target should return `403` and enforce limits)
