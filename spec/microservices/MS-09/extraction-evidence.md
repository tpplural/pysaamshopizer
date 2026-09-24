# MS-09 Order Service — Extraction Evidence

**Analysis Mode**: Direct Source Read (no CAST)
**Session**: Phase 4 deep extraction

## Source Files Processed

| # | File | Sections Read | Rules Extracted | Vectors Counted |
|---|------|---------------|-----------------|-----------------|
| 1 | `sm-core/.../order/service/OrderServiceImpl.java` | caculateOrder (172-326); caculateOrderTotal (329-377); process (108-166); processOrder (96-102); addOrderStatusHistory (85-90); saveOrUpdate (454-464); hasDownloadFiles (469-485); generateInvoice (414-431) | BR-ORD-001..013 | ✅ |
| 2 | `sm-core/.../order/dao/OrderDaoImpl.java` | getById (29-52); listByStore (57-166) | BR-ORD-014, 015 | ✅ |
| 3 | `sm-core/.../order/service/OrderProductDownloadServiceImpl.java` | getByOrderId (53-55) | BR-ORD-016 | ✅ |
| 4 | `sm-core/.../order/dao/OrderProductDownloadDaoImpl.java` | getByOrderId (41-56); getById (18-38) | BR-ORD-016 | ✅ |
| 5 | `sm-shop/.../controller/order/OrderFacadeImpl.java` | calculateOrderTotal (154-213); setOrderTotals (231-247); processOrderModel (267-416); initEmptyCustomer (443-461); initializeOrder (127-149); validateOrder (555-745); getShippingSummary (534-552) | BR-ORD-017..024 | ✅ |
| 6 | `sm-shop/.../controller/order/ShoppingOrderController.java` | commitOrder (367-712); commitPreAuthorizedOrder (327-361) | BR-ORD-025, 026 | ✅ |
| 7 | `sm-shop/.../controller/order/ShoppingOrderPaymentController.java` | paymentAction (117-238); returnPayPalPayment (243-251) | BR-ORD-027 | ✅ |
| 8 | `sm-shop/.../controller/order/ShoppingOrderConfirmationController.java` | displayConfirmation (104-186) | BR-ORD-028 | ✅ |
| 9 | `sm-shop/.../controller/order/ShoppingOrderDownloadController.java` | downloadFile (59-113) | BR-ORD-032 | ✅ |
| 10 | `sm-shop/.../admin/controller/orders/OrderControler.java` | saveOrder (211-375) | BR-ORD-029 | ✅ |
| 11 | `sm-shop/.../admin/controller/orders/OrderActionsControler.java` | captureOrder (89-137); refundOrder (142-225) | BR-ORD-030 | ✅ |
| 12 | `sm-shop/.../services/controller/order/OrderRESTController.java` | createOrder (73-115) | BR-ORD-031 | ✅ |
| 13 | `sm-core-model/.../order/model/Order.java` | full JPA entity (ORDERS) + embedded CreditCard/Billing/Delivery + cascades | orders table; BR-ORD-018/020 | ✅ |
| 14 | `sm-core-model/.../order/model/orderproduct/OrderProduct.java` | full entity (ORDER_PRODUCT) | order_product | ✅ |
| 15 | `sm-core-model/.../order/model/orderproduct/OrderProductPrice.java` | full entity | order_product_price | ✅ |
| 16 | `sm-core-model/.../order/model/orderproduct/OrderProductAttribute.java` | full entity | order_product_attribute | ✅ |
| 17 | `sm-core-model/.../order/model/orderproduct/OrderProductDownload.java` | full entity (DOWNLOAD_MAXDAYS default 31, DOWNLOAD_COUNT, DEFAULT_DOWNLOAD_MAX_DAYS=31) | order_product_download; BR-ORD-032 | ✅ |
| 18 | `sm-core-model/.../order/model/OrderTotal.java` | full entity (ORDER_TOTAL) | order_total; BR-ORD-001..005 | ✅ |
| 19 | `sm-core-model/.../order/model/orderstatus/OrderStatus.java` | enum (Ordered/Processed/Delivered/Refunded) | state model | ✅ |
| 20 | `sm-core-model/.../order/model/orderstatus/OrderStatusHistory.java` | full entity (ORDER_STATUS_HISTORY) | order_status_history; BR-ORD-009/010 | ✅ |
| 21 | `sm-core-model/.../order/model/OrderAccount.java` | full entity (ORDER_ACCOUNT) | order_account; INV-ORD-006 (4a scope) | ✅ |
| 22 | `sm-core-model/.../order/model/FileHistory.java` | full entity (FILE_HISTORY) | file_history (4a scope) | ✅ |

## Files searched / read as evidence only (not extracted)

- `OrderProductPopulator.java` — cart-item → OrderProduct mechanics (folded into BR-ORD-018).
- `CustomerOrdersController.java` — customer order history/detail read views; access-control gap folded into the BR-ORD-032 clarification note.
- `OrdersController.java` (admin) — list entry point → BR-ORD-015.
- `OrderTotalType.java`, `OrderValueType.java`, `OrderType.java`, `OrderChannel.java`, `OrderCriteria.java`, `CreditCard.java` — enums/models supporting the extracted rules.
- Generic-CRUD DAO stubs (`OrderTotalDaoImpl`, `OrderProductDaoImpl`, `OrderAccountDaoImpl`) — inherit `SalesManagerEntityDaoImpl`, no own logic.

## Extraction Status

- Files processed (in-scope): 22 (34 components accounted at Phase 1 granularity; supporting enums/models/stubs ACCOUNTED)
- Rules extracted: 32 (BR-ORD-001..032, contiguous)
- Source vectors complete: yes (8-dimension per rule)

## Black-Box Call Register

| Called Unit | Called By (BR-ID) | Disposition | Rationale |
|-------------|-------------------|-------------|-----------|
| taxService.calculateTax | BR-ORD-004 | CROSS-SERVICE (MS-07) | Synchronous stateless read; TAX total lines folded into the OWNED total (BV-1) |
| shippingService.getShippingConfiguration / getShippingQuote / requiresShipping | BR-ORD-002, 003, 022, 024 | CROSS-SERVICE (MS-08) | Synchronous reads; shipping/handling folded into the OWNED total (BV-1) |
| paymentService.processPayment | BR-ORD-008 | CROSS-SERVICE (MS-10) | Checkout saga CHARGE step; settlement fact applied via consumed `payment.captured` (BV-2) |
| paymentService.processCapturePayment / processRefund | BR-ORD-030 | CROSS-SERVICE (MS-10) | Delegated capture/refund; settlement applied via consumed `payment.captured` / `payment.refunded` (BV-2) |
| customerService.create / getById / saveOrUpdate | BR-ORD-008, 023, 025, 031 | CROSS-SERVICE (MS-05) | Customer reference/create |
| shoppingCartFacade.getShoppingCartModel / deleteShoppingCart | BR-ORD-025, 026 | CROSS-SERVICE (MS-06) | Source basket + cart teardown (BV-3) |
| invoiceModule.createInvoice | BR-ORD-013 | EXTERNAL | Invoice PDF render module |
| emailTemplatesUtils.send* | BR-ORD-025 | EXTERNAL | Confirmation/registration/download email; failures swallowed |
| contentService.getContentFile | BR-ORD-032 | EXTERNAL | Digital product file store |
| PayPalExpressCheckoutPayment.initPaypalTransaction | BR-ORD-027 | CROSS-SERVICE (MS-10 SPI) | External PayPal set-express-checkout |
| transactionService.create / update / getCapturable / getRefundable | BR-ORD-008, 027, 029, 030 | CROSS-SERVICE (MS-10) | Payment transaction ledger owned by MS-10 |

No unresolved black-box callees. No cross-service ORDER DB write is modeled — payment settlement is applied by CONSUMING events (BV-2/ADR-003).
