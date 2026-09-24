# MS-10 Payment Service — Component Inventory

**Service ID**: MS-10
**Analysis Mode**: Direct Source Read (no CAST)
**Legacy system**: Shopizer 2.0.1 (Java / Spring, JPA/Hibernate + QueryDSL)

## Legacy Components (in scope)

| Component | Module | Type | Role | Disposition |
|-----------|--------|------|------|-------------|
| `PaymentServiceImpl.java` | sm-core | Service (complex) | Orchestration hub: process/capture/refund + config CRUD + card validation | EXTRACTED (BR-PAY-001..012b, 020-026, 029) |
| `PaymentService.java` | sm-core | Service interface | Contract only | ACCOUNTED (interface of PaymentServiceImpl) |
| `TransactionServiceImpl.java` | sm-core | Service (medium) | Ledger create + capturable/refundable selection + list | EXTRACTED (BR-PAY-005, 013, 014, 016, 017) |
| `TransactionService.java` | sm-core | Service interface | Contract only | ACCOUNTED |
| `TransactionDaoImpl.java` | sm-core | DAO | listByOrder (QueryDSL) | EXTRACTED (BR-PAY-018) |
| `TransactionDao.java` | sm-core | DAO interface | Contract only | ACCOUNTED |
| `PaymentModule.java` | sm-core-modules | SPI interface | Gateway plug-in contract | EXTRACTED (BR-PAY-019 — EXT-PAY-001) |
| `CreditCardUtils.java` | sm-core | Utility | maskCardNumber | EXTRACTED (BR-PAY-028) |
| `Transaction.java` | sm-core-model | Entity (SM_TRANSACTION) | Ledger row + JSON details | EXTRACTED (BR-PAY-016; entity → transaction table) |
| `Payment.java` | sm-core-model | Model | Base payment (default AuthorizeCapture) | EXTRACTED (BR-PAY-029) |
| `CreditCardPayment.java` | sm-core-model | Model | Card fields (PCI-relevant) | ACCOUNTED (fields used by BR-PAY-020/022) |
| `PaypalPayment.java` | sm-core-model | Model | Forces Paypal type; express fields | EXTRACTED (BR-PAY-030) |
| `PaymentMethod.java` | sm-core-model | Model | Storefront method DTO | ACCOUNTED (shape of BR-PAY-011 output) |
| `TransactionType.java` | sm-core-model | Enum | Init/Authorize/Capture/AuthorizeCapture/Refund | EXTRACTED (state model) |
| `PaymentType.java` | sm-core-model | Enum | CreditCard/Free/Cod/MoneyOrder/Paypal | ACCOUNTED (enum) |
| `CreditCardType.java` | sm-core-model | Enum | Amex/Visa/Mastercard/Diners/Discovery | ACCOUNTED (used by BR-PAY-022) |
| `PaymentsController.java` | sm-shop | Controller (admin) | Admin config screens — belongs to admin/UI segment | OUT_OF_SCOPE (entry point only; drives save/remove config) |
| `PayPalExpressCheckoutPayment.java` | sm-core-modules | SPI impl | Gateway internals (PayPal) | OUT_OF_SCOPE (external gateway internals — read as SPI-contract evidence only) |

## Owned Tables (target)

| Target table | Legacy origin |
|--------------|---------------|
| `transaction` | SM_TRANSACTION |
| `payment_method_configuration` | SM_MERCHANT_CONFIGURATION (key="PAYMENT", encrypted JSON) + per-module custom rows |

## Cross-service / external (NOT owned)

- ORDER / ORDER_TOTAL / ORDER_STATUS_HISTORY → MS-09 (via `payment.captured` / `payment.refunded` events)
- MERCHANT_STORE / currency → MS-03; COUNTRY / region → MS-01 (reference reads)
- MODULE_CONFIGURATION (gateway registry) → shared/system reference
- External PSPs (PayPal, authorize.net, BeanStream) → plug-in via EXT-PAY-001
