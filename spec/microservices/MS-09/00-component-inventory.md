# MS-09 Order Service — Component Inventory

**Service ID**: MS-09
**Analysis Mode**: Direct Source Read (no CAST)
**Legacy system**: Shopizer 2.0.1 (Java / Spring MVC, JPA/Hibernate + QueryDSL)

## Legacy Components (in scope)

| Component | Module | Type | Role | Disposition |
|-----------|--------|------|------|-------------|
| `OrderServiceImpl.java` | sm-core | Service (complex) | Totals engine (caculateOrder), placement orchestration (process), status history, invoice, hasDownloadFiles | EXTRACTED (BR-ORD-001..013) |
| `OrderService.java` | sm-core | Service interface | Contract only | ACCOUNTED |
| `OrderDaoImpl.java` | sm-core | DAO | getById eager graph; listByStore criteria + paging | EXTRACTED (BR-ORD-014, 015) |
| `OrderDao.java` | sm-core | DAO interface | Contract only | ACCOUNTED |
| `OrderProductDownloadServiceImpl.java` | sm-core | Service | Downloads by order id | EXTRACTED (BR-ORD-016) |
| `OrderProductDownloadDaoImpl.java` | sm-core | DAO | getByOrderId / getById | EXTRACTED (BR-ORD-016) |
| `OrderTotalDaoImpl.java` | sm-core | DAO | Generic CRUD stub (order_total) | ACCOUNTED (inherits generic CRUD) |
| `OrderProductDaoImpl.java` | sm-core | DAO | Generic CRUD stub (order_product) | ACCOUNTED |
| `OrderAccountDaoImpl.java` | sm-core | DAO | Generic CRUD stub (order_account) — not wired | ACCOUNTED (scaffolding, 4a scope) |
| `OrderFacadeImpl.java` | sm-shop | Facade (complex) | calculateOrderTotal, processOrderModel (cart→order), validateOrder, shipping summary, empty-customer prefill, payment assembly | EXTRACTED (BR-ORD-017..024) |
| `ShoppingOrderController.java` | sm-shop | Controller | Checkout commit, cart resolution + payment-method selection | EXTRACTED (BR-ORD-025, 026) |
| `ShoppingOrderPaymentController.java` | sm-shop | Controller | PayPal Express pre-auth initiation | EXTRACTED (BR-ORD-027) |
| `ShoppingOrderConfirmationController.java` | sm-shop | Controller | Confirmation + cross-store guard | EXTRACTED (BR-ORD-028) |
| `ShoppingOrderDownloadController.java` | sm-shop | Controller | Digital download delivery | EXTRACTED (BR-ORD-032 — SECURITY FLAG) |
| `CustomerOrdersController.java` | sm-shop | Controller | Customer order history/detail | ACCOUNTED (read views; access-control flag folded into BR-ORD-032 note) |
| `OrderControler.java` | sm-shop (admin) | Controller | Admin order edit — status change + history | EXTRACTED (BR-ORD-029) |
| `OrderActionsControler.java` | sm-shop (admin) | Controller | Capture / refund / invoice / emails | EXTRACTED (BR-ORD-030) |
| `OrdersController.java` | sm-shop (admin) | Controller | Admin order list / paging | ACCOUNTED (entry point → BR-ORD-015) |
| `OrderRESTController.java` | sm-shop | REST controller | REST create order (no payment) | EXTRACTED (BR-ORD-031) |
| `OrderProductPopulator.java` | sm-shop | Populator | Cart-item → OrderProduct snapshot | ACCOUNTED (mechanics of BR-ORD-018) |
| `Order.java` | sm-core-model | Entity (ORDERS) | Order aggregate root + embedded CreditCard/Billing/Delivery | EXTRACTED (→ orders table; BR-ORD-018/020) |
| `OrderProduct.java` | sm-core-model | Entity (ORDER_PRODUCT) | Ordered line snapshot | EXTRACTED (→ order_product) |
| `OrderProductPrice.java` | sm-core-model | Entity (ORDER_PRODUCT_PRICE) | Line price snapshot | EXTRACTED (→ order_product_price) |
| `OrderProductAttribute.java` | sm-core-model | Entity (ORDER_PRODUCT_ATTRIBUTE) | Line attribute snapshot | EXTRACTED (→ order_product_attribute) |
| `OrderProductDownload.java` | sm-core-model | Entity (ORDER_PRODUCT_DOWNLOAD) | Download entry (maxdays 31, downloadCount) | EXTRACTED (→ order_product_download; BR-ORD-032) |
| `OrderTotal.java` | sm-core-model | Entity (ORDER_TOTAL) | Total line (module/type/sortOrder/value) | EXTRACTED (→ order_total; BR-ORD-001..005) |
| `OrderStatus.java` | sm-core-model | Enum | Ordered/Processed/Delivered/Refunded | EXTRACTED (state model) |
| `OrderStatusHistory.java` | sm-core-model | Entity (ORDER_STATUS_HISTORY) | Append-only status audit | EXTRACTED (→ order_status_history; BR-ORD-009/010) |
| `OrderTotalType.java` / `OrderValueType.java` | sm-core-model | Enum | Total line typing / one-time vs monthly | ACCOUNTED (total_type; BR-ORD-001/005) |
| `OrderType.java` / `OrderChannel.java` | sm-core-model | Enum | Order type / channel | ACCOUNTED (columns) |
| `OrderSummary.java` / `OrderTotalSummary.java` | sm-core-model | Model | Calc inputs/outputs | ACCOUNTED (shape of BR-ORD-001..007/017) |
| `OrderCriteria.java` | sm-core-model | Model | List filter/paging criteria | ACCOUNTED (shape of BR-ORD-015) |
| `OrderAccount.java` | sm-core-model | Entity (ORDER_ACCOUNT) | Recurring-billing account — not wired | EXTRACTED (→ order_account; INV-ORD-006; 4a scope) |
| `CreditCard.java` | sm-core-model | Embeddable | Masked PAN + owner/expiry/CVV (PCI) | ACCOUNTED (embedded in orders; BR-ORD-020) |
| `FileHistory.java` | sm-core-model | Entity (FILE_HISTORY) | Download accounting — unused by download path | EXTRACTED (→ file_history; 4a scope) |

## Owned Tables (target — 10)

| Target table | Legacy origin |
|--------------|---------------|
| `orders` | ORDERS |
| `order_product` | ORDER_PRODUCT |
| `order_total` | ORDER_TOTAL |
| `order_status_history` | ORDER_STATUS_HISTORY |
| `order_product_price` | ORDER_PRODUCT_PRICE |
| `order_product_download` | ORDER_PRODUCT_DOWNLOAD |
| `order_product_attribute` | ORDER_PRODUCT_ATTRIBUTE |
| `order_account` | ORDER_ACCOUNT (recurring-billing scaffolding — not wired in 2.0.1) |
| `order_account_product` | ORDER_ACCOUNT_PRODUCT (recurring-billing scaffolding) |
| `file_history` | FILE_HISTORY (download-accounting — unused by download path) |

> `SM_SEQUENCER` is NOT owned — it is the shared JPA table-generator (target uses per-table sequences).

## Cross-service / external (NOT owned)

- TAX (MS-07) — synchronous stateless read (`/calculate`) folded into the OWNED total (BV-1).
- SHIPPING (MS-08) — synchronous stateless read (`/quote` + config) folded into the OWNED total (BV-1).
- PAYMENT (MS-10) — charge = saga CHARGE step; settlement applied by CONSUMING `payment.captured` /
  `payment.refunded` (BV-2/ADR-003). NO cross-service order write from payment.
- CART (MS-06) — source basket (BV-3 — cart delegates its authoritative total here); deleted on commit.
- CUSTOMER (MS-05), REFERENCE country/zone/language (MS-01), MERCHANT STORE (MS-03) — reference reads (ids).
- EMAIL (confirmation/registration/download), CONTENT (digital file), INVOICE module — external integrations.
- External PayPal Express — via MS-10 payment SPI (pre-auth init).
