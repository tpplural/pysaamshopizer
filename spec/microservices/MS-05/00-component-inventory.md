# MS-05 Customer Service — Component Inventory

Legacy components in scope for MS-05, under `initial-source/shopizer/`. Rule-bearing components are extracted in `01-business-rules.md`; model/enum/embeddable classes are structural.

## Model / entity (sm-core-model)
| Component | Path | Role |
|-----------|------|------|
| `Customer.java` | sm-core-model/.../customer/model/Customer.java | Shopper entity (embedded Billing/Delivery, groups, gender) |
| `CustomerGender.java` | sm-core-model/.../customer/model/CustomerGender.java | Enum M/F (BR-CUST-027) |
| `Billing.java` | sm-core-model/.../common/model/Billing.java | Embedded billing address (BR-CUST-011) |
| `Delivery.java` | sm-core-model/.../common/model/Delivery.java | Embedded delivery address (BR-CUST-012) |
| `CustomerOption.java` | sm-core-model/.../customer/model/attribute/CustomerOption.java | Custom field definition (BR-CUSTOPT-001/002) |
| `CustomerOptionValue.java` | sm-core-model/.../customer/model/attribute/CustomerOptionValue.java | Option value (BR-CUSTOPT-004/005) |
| `CustomerOptionSet.java` | sm-core-model/.../customer/model/attribute/CustomerOptionSet.java | (option,value) binding (BR-CUSTOPT-008) |
| `CustomerAttribute.java` | sm-core-model/.../customer/model/attribute/CustomerAttribute.java | Shopper's stored value (BR-CUSTOPT-010) |
| `CustomerOptionType.java` | sm-core-model/.../customer/model/attribute/CustomerOptionType.java | Enum Text/Radio/Select/Checkbox (BR-CUSTOPT-011) |

## Service / DAO (sm-core)
| Component | Path | Role |
|-----------|------|------|
| `CustomerServiceImpl.java` | sm-core/.../customer/service/CustomerServiceImpl.java | Upsert, lookup, delete-cascade (BR-CUST-015/028) |
| `CustomerAttributeServiceImpl.java` | sm-core/.../customer/service/attribute/CustomerAttributeServiceImpl.java | Attribute upsert/delete (BR-CUSTOPT-009) |
| `CustomerOptionServiceImpl.java` | sm-core/.../customer/service/attribute/CustomerOptionServiceImpl.java | Option upsert + cascade delete (BR-CUSTOPT-013) |
| `CustomerOptionValueServiceImpl.java` | sm-core/.../customer/service/attribute/CustomerOptionValueServiceImpl.java | Value upsert + cascade delete (BR-CUSTOPT-014) |
| `CustomerOptionSetServiceImpl.java` | sm-core/.../customer/service/attribute/CustomerOptionSetServiceImpl.java | Set upsert (BR-CUSTOPT-009) |
| `CustomerDAOImpl.java` | sm-core/.../customer/dao/CustomerDAOImpl.java | getByNick (BR-CUST-001) |

## Facade / populator / controllers (sm-shop)
| Component | Path | Role |
|-----------|------|------|
| `CustomerFacadeImpl.java` | sm-shop/.../shop/controller/customer/facade/CustomerFacadeImpl.java | Registration, auth, defaults, cart merge (BR-CUST-002/006/007/008/022) |
| `CustomerPopulator.java` | sm-shop/.../populator/customer/CustomerPopulator.java | Gender/country/zone/language defaults, attribute build (BR-CUST-013/014/027, BR-CUSTOPT-010) |
| `CustomerRegistrationController.java` | sm-shop/.../shop/controller/customer/CustomerRegistrationController.java | Registration flow (BR-CUST-002/003/020/021) |
| `CustomerLoginController.java` | sm-shop/.../shop/controller/customer/CustomerLoginController.java | Login flow (BR-CUST-009/022) |
| `CustomerAccountController.java` | sm-shop/.../shop/controller/customer/CustomerAccountController.java | Change password, attribute reconcile (BR-CUST-016, BR-CUSTOPT-011/012) |
| `CustomerDashboardController.java` | sm-shop/.../shop/controller/customer/CustomerDashboardController.java | Option visibility (BR-CUSTOPT-015) |
| `CustomerController.java` | sm-shop/.../admin/controller/customers/CustomerController.java | Admin save/reset (BR-CUST-011/017/019/025) |
| `CustomerOptionsController.java` | sm-shop/.../admin/controller/customers/CustomerOptionsController.java | Option CRUD (BR-CUSTOPT-001/002/003/013) |
| `CustomerOptionsValueController.java` | sm-shop/.../admin/controller/customers/CustomerOptionsValueController.java | Value CRUD (BR-CUSTOPT-004/005/006/014) |
| `CustomerOptionsSetController.java` | sm-shop/.../admin/controller/customers/CustomerOptionsSetController.java | Set CRUD (BR-CUSTOPT-007/008) |
| `CustomerRESTController.java` | sm-shop/.../services/controller/customer/CustomerRESTController.java | Service API create/get/delete (BR-CUST-024/026/028) |

## Out of scope (referenced, other services)
- Cart merge internals → MS-06. Country/zone/language/store → MS-01. Group/permission catalog + `authenticate()` + password encoder → MS-02. Email/captcha → external integrations.
