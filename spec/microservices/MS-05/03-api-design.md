# Customer Service (MS-05) — API Design

**Base path**: `/api/v1` · **Port**: 8005 · **Naming**: snake_case fields, kebab-case paths.
**Global headers (every request):** `x-tenant-id` (required), `x-store-id` (required) — multi-tenant + per-store isolation (BR-CUST-018/024).

Authentication (`authenticate()`) and password encoding are delegated to the identity mechanism (MS-02). Cart merge (BR-CUST-022) delegates to the cart service (MS-06). Country/zone/language (MS-01) and group/permission (MS-02) are external references (id only). Notifications/verification (BR-CUST-020/021/025) are external integrations.

## Endpoints (30 operations)

| # | Method | Endpoint | Description | Driven by |
|---|--------|----------|-------------|-----------|
| 1 | GET | `/customers` | List shoppers in the store (paged) | CRUD (store-scoped, BR-CUST-024) |
| 2 | POST | `/customers` | Create a shopper (admin/system path) | BR-CUST-005,006,007,014,015,027 |
| 3 | GET | `/customers/{id}` | Get a shopper | BR-CUST-018,024 |
| 4 | PUT | `/customers/{id}` | Update a shopper | BR-CUST-015,017 |
| 5 | DELETE | `/customers/{id}` | Delete a shopper (cascades attributes) | BR-CUST-018,028 |
| 6 | GET | `/customers/lookup` | Resolve a shopper by username within the store | BR-CUST-001 |
| 7 | POST | `/customers/registration` | Self-service registration | BR-CUST-002,003,010,020,021 |
| 8 | POST | `/customers/login` | Authenticate a shopper + merge session cart | BR-CUST-008,009,022 |
| 9 | POST | `/customers/{id}/password` | Change own password | BR-CUST-004,016,021 |
| 10 | POST | `/customers/{id}/password-reset` | Admin reset password | BR-CUST-006,021,025 |
| 11 | GET | `/customers/{id}/addresses/billing` | Get billing address | CRUD |
| 12 | PUT | `/customers/{id}/addresses/billing` | Update billing address | BR-CUST-011,013,019 |
| 13 | GET | `/customers/{id}/addresses/delivery` | Get delivery address | CRUD |
| 14 | PUT | `/customers/{id}/addresses/delivery` | Update delivery address | BR-CUST-012,013,019 |
| 15 | GET | `/customers/{id}/groups` | List a shopper's groups | CRUD |
| 16 | POST | `/customers/{id}/groups` | Add a group membership | BR-CUST-007,023 |
| 17 | DELETE | `/customers/{id}/groups/{groupId}` | Remove a group membership | BR-CUST-023 |
| 18 | GET | `/customers/{id}/attributes` | List a shopper's attributes | CRUD |
| 19 | PUT | `/customers/{id}/attributes` | Reconcile a shopper's attributes | BR-CUSTOPT-010,011,012 |
| 20 | GET | `/customers/{id}/available-options` | Options visible to the shopper with selections | BR-CUSTOPT-015 |
| 21 | GET | `/customer-options` | List customer options | CRUD |
| 22 | POST | `/customer-options` | Create a customer option | BR-CUSTOPT-001,002,003,009 |
| 23 | GET | `/customer-options/{id}` | Get a customer option | BR-CUST-018 |
| 24 | PUT | `/customer-options/{id}` | Update a customer option | BR-CUSTOPT-002,003,009 |
| 25 | DELETE | `/customer-options/{id}` | Delete a customer option (cascade) | BR-CUSTOPT-013 |
| 26 | GET | `/customer-option-values` | List customer option values | CRUD |
| 27 | POST | `/customer-option-values` | Create a customer option value | BR-CUSTOPT-004,005,006,009 |
| 28 | DELETE | `/customer-option-values/{id}` | Delete a customer option value (cascade) | BR-CUSTOPT-014 |
| 29 | GET | `/customer-option-sets` | List (option,value) bindings | CRUD |
| 30 | POST | `/customer-option-sets` | Create an (option,value) binding | BR-CUSTOPT-007,008,009 |

## Notes
- All mutating operations return standard error responses (400/401/404/409/422/500).
- `POST /customers/login` accepts an optional `session_cart_code`; cart assignment/merge is delegated to MS-06 (BR-CUST-022) and the resolved cart code is returned.
- `POST /customers` (service path) currently assigns the ADMIN group — see BR-CUST-026 (suspected defect, flagged for clarification).
