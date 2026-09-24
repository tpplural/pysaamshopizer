# MS-10 Payment Service — Extraction Evidence

**Analysis Mode**: Direct Source Read (no CAST)
**Session**: Phase 4 deep extraction

## Source Files Processed

| # | File | Lines | Sections Read | Rules Extracted | Vectors Counted |
|---|------|-------|---------------|-----------------|-----------------|
| 1 | `sm-core/.../payments/service/PaymentServiceImpl.java` | ~660 | full: config load/save/remove; processPayment; processCapturePayment; processRefund; validateCreditCard/Date/Number; luhnValidate | BR-PAY-001..004, 005 (partial), 006, 007, 008, 009, 009b, 010, 011, 012, 012a, 012b, 015, 020, 021, 022, 025, 026, 029 (partial) | ✅ |
| 2 | `sm-core/.../payments/service/TransactionServiceImpl.java` | ~160 | full: create; listTransactions; getCapturableTransaction; getRefundableTransaction | BR-PAY-005 (persist), 013, 014, 016, 017 | ✅ |
| 3 | `sm-core/.../payments/dao/TransactionDaoImpl.java` | ~32 | full: listByOrder (QueryDSL, no ORDER BY) | BR-PAY-018 | ✅ |
| 4 | `sm-core-modules/.../integration/payment/model/PaymentModule.java` | ~53 | full: SPI contract (6 operations) | BR-PAY-019 (EXT-PAY-001) | ✅ |
| 5 | `sm-core/.../utils/CreditCardUtils.java` | ~30 | full: maskCardNumber + unused brand constants | BR-PAY-028 | ✅ |
| 6 | `sm-core-model/.../payments/model/Transaction.java` | ~190 | full: JPA entity (SM_TRANSACTION) + toJSONString | domain model (transaction table) + BR-PAY-016 details | ✅ |
| 7 | `sm-core-model/.../payments/model/Payment.java` | ~45 | full: base model, default AuthorizeCapture | BR-PAY-029 | ✅ |
| 8 | `sm-core-model/.../payments/model/PaypalPayment.java` | ~35 | full: forces Paypal type; express fields | BR-PAY-030 | ✅ |
| 9 | `sm-core-model/.../payments/model/CreditCardPayment.java` | ~55 | full: card fields (PCI) | supports BR-PAY-020/022 | ✅ |
| 10 | `sm-core-model/.../payments/model/PaymentMethod.java` | ~55 | full: storefront method DTO | supports BR-PAY-011 | ✅ |
| 11 | `sm-core-model/.../payments/model/TransactionType.java` | ~8 | full: enum (5 values) | state model | ✅ |
| 12 | `sm-core-model/.../payments/model/PaymentType.java` | ~8 | full: enum (5 values) | supports BR-PAY-006/011 | ✅ |
| 13 | `sm-core-model/.../payments/model/CreditCardType.java` | ~6 | full: enum (5 values) | supports BR-PAY-022 | ✅ |

## Files searched / read as evidence only (not extracted)

- `sm-shop/.../admin/controller/payments/PaymentsController.java` — admin config entry point; belongs to admin/UI segment (OUT_OF_SCOPE for MS-10 core).
- `PayPalExpressCheckoutPayment.java` — SPI-contract evidence only; external gateway internals OUT_OF_SCOPE.

## Extraction Status

- Files total (in-scope core): 13
- Files processed: 13
- Rules extracted: 31 (BR-PAY-001..030 + 009b/012a/012b; 023/024 folded into 022)
- Source vectors complete: yes (8-dimension per rule)

## Black-Box Call Register

| Called Unit | Called By (BR-ID) | Disposition | Rationale / New BR-IDs |
|-------------|-------------------|-------------|------------------------|
| PaymentModule.authorize / authorizeAndCapture / capture / refund / initTransaction | BR-PAY-004, 007, 012, 027 | OUT_OF_SCOPE | External gateway plug-in (EXT-PAY-001) — internals are third-party PSP code, contract captured in BR-PAY-019 |
| validateCreditCard → validateCreditCardDate | BR-PAY-020 | EXTRACTED | BR-PAY-021 |
| validateCreditCard → validateCreditCardNumber | BR-PAY-020 | EXTRACTED | BR-PAY-022 (dead brand code, preserved) |
| validateCreditCardNumber → luhnValidate | BR-PAY-022 | EXTRACTED | BR-PAY-025 |
| Encryption.encrypt / decrypt | BR-PAY-008, 009, 009b | OUT_OF_SCOPE | Shared encryption service; key management flagged to 4a (SECURITY) |
| MerchantConfigurationService / ModuleConfigurationService | BR-PAY-008, 009, 010 | OUT_OF_SCOPE | Config persistence + gateway registry — modernized as this service's payment_method_configuration + reference read |
| OrderService.saveOrUpdate / addOrderStatusHistory | legacy BR-PAY-007/015 (REPLACED) | OUT_OF_SCOPE | Cross-domain order write REPLACED by events (BV-2/ADR-003); MS-09 owns order state |
| ConfigurationModulesLoader.loadIntegrationConfigurations / toJSONString | BR-PAY-008, 009, 009b | OUT_OF_SCOPE | JSON (de)serialization helper — infrastructure |

No unresolved black-box callees.
