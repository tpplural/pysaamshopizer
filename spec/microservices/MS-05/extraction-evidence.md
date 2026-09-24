# MS-05 — Extraction Evidence

Direct Source mode (no CAST). All files read from `initial-source/shopizer/` in this session.

## Source Files Processed

| # | File | Lines | Sections Read | Rules Extracted | Vectors Counted |
|---|------|-------|---------------|-----------------|-----------------|
| 1 | sm-core-model/.../customer/model/Customer.java | ~275 | full — entity fields, embedded billing/delivery, groups M2M cascade, gender | BR-CUST-010,023 (supports 011,012,027) | ✅ |
| 2 | sm-core-model/.../customer/model/CustomerGender.java | 7 | full — enum M/F | BR-CUST-027 | ✅ |
| 3 | sm-core-model/.../common/model/Billing.java | ~135 | full — @NotEmpty first/last, country not-null | BR-CUST-011 | ✅ |
| 4 | sm-core-model/.../common/model/Delivery.java | ~140 | full — all nullable, country nullable | BR-CUST-012 | ✅ |
| 5 | sm-core-model/.../customer/model/attribute/CustomerOption.java | ~185 | full — unique(merchant,code), pattern, active/public | BR-CUSTOPT-001,002,015 | ✅ |
| 6 | sm-core-model/.../customer/model/attribute/CustomerOptionValue.java | ~155 | full — unique(merchant,code), pattern | BR-CUSTOPT-004,005 | ✅ |
| 7 | sm-core-model/.../customer/model/attribute/CustomerOptionSet.java | ~95 | full — unique(option,value) | BR-CUSTOPT-008 | ✅ |
| 8 | sm-core-model/.../customer/model/attribute/CustomerAttribute.java | ~105 | full — unique(option,customer), FKs | BR-CUSTOPT-003(inv),010 | ✅ |
| 9 | sm-core-model/.../customer/model/attribute/CustomerOptionType.java | 7 | full — enum Text/Radio/Select/Checkbox | BR-CUSTOPT-011 | ✅ |
| 10 | sm-core/.../customer/service/CustomerServiceImpl.java | ~115 | full — saveOrUpdate, delete cascade | BR-CUST-015,028 | ✅ |
| 11 | sm-core/.../customer/service/attribute/CustomerOptionServiceImpl.java | ~95 | full — saveOrUpdate, delete cascade | BR-CUSTOPT-009,013 | ✅ |
| 12 | sm-core/.../customer/service/attribute/CustomerOptionValueServiceImpl.java | ~95 | full — saveOrUpdate, delete cascade | BR-CUSTOPT-009,014 | ✅ |
| 13 | sm-core/.../customer/service/attribute/CustomerOptionSetServiceImpl.java | ~85 | full — saveOrUpdate | BR-CUSTOPT-009 | ✅ |
| 14 | sm-core/.../customer/service/attribute/CustomerAttributeServiceImpl.java | ~80 | full — saveOrUpdate/delete | BR-CUSTOPT-009 | ✅ |
| 15 | sm-shop/.../shop/controller/customer/facade/CustomerFacadeImpl.java | ~430 | two-pass — checkIfUserExists, getCustomerModel, setCustomerModelDefaultProperties, authenticate, mergeCart, updateAddress | BR-CUST-002,004,005,006,007,008,022 | ✅ |
| 16 | sm-shop/.../populator/customer/CustomerPopulator.java | ~285 | full — gender default, country/zone resolution, language default, attribute build | BR-CUST-010,013,014,027, BR-CUSTOPT-010 | ✅ |
| 17 | sm-shop/.../shop/controller/customer/CustomerRegistrationController.java | ~250 | full — captcha, dup-username, password match, email send | BR-CUST-002,003,020,021 | ✅ |
| 18 | sm-shop/.../shop/controller/customer/CustomerLoginController.java | ~120 | full — logon, null→failure, cart merge trigger | BR-CUST-009,022 | ✅ |
| 19 | sm-shop/.../shop/controller/customer/CustomerAccountController.java | ~430 | two-pass — changePassword, saveCustomerAttributes reconcile | BR-CUST-004,016, BR-CUSTOPT-011,012 | ✅ |
| 20 | sm-shop/.../shop/controller/customer/CustomerDashboardController.java | ~135 | full — active+public option filter | BR-CUSTOPT-015 | ✅ |
| 21 | sm-shop/.../admin/controller/customers/CustomerOptionsController.java | ~300 | full — code dup, name-per-language, delete | BR-CUSTOPT-001,002,003,013 | ✅ |
| 22 | sm-shop/.../admin/controller/customers/CustomerOptionsValueController.java | ~300 | full — code dup, pattern, description required | BR-CUSTOPT-004,005,006,014 | ✅ |
| 23 | sm-shop/.../admin/controller/customers/CustomerOptionsSetController.java | ~310 | full — association required, dup pair | BR-CUSTOPT-007,008 | ✅ |
| 24 | sm-shop/.../services/controller/customer/CustomerRESTController.java | ~360 | full — store resolution, ADMIN-group defect, delete | BR-CUST-024,026,028 | ✅ |

## Extraction Status
- Files total (read this session): 24
- Files processed: 24
- Rules extracted: 43 (BR-CUST: 28, BR-CUSTOPT: 15)
- Source vectors complete: yes (8-dimension table on every rule)

## Not Found
None — all referenced components resolved to real files.

## Net-New Findings (beyond Phase 1)
- **BR-CUST-027** — gender silently defaults to `M` (`CustomerPopulator.populate`), previously not a distinct rule.
- **BR-CUST-028** — hard delete cascades attributes in application code (`CustomerServiceImpl.delete`), previously not a distinct rule.
- **BR-CUST-026** (confirmed defect surface) — REST create assigns ADMIN group; flagged for clarification.

No greenfield (source-less) rules: every rule traces to a read source file.
