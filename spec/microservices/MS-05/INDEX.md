# MS-05 Customer Service — Spec Index

| Attribute | Value |
|-----------|-------|
| Service Name | Customer Service |
| Service ID | MS-05 |
| Port | 8005 |
| Database Schema | `customer_schema` |
| Target Stack | Python / FastAPI + PostgreSQL 15+ |
| Analysis Mode | Direct Source (no CAST) |
| Legacy System | Shopizer 2.0.1 (Java / Spring MVC / JPA-Hibernate / Spring Security) |

## Metrics

| Metric | Count |
|--------|-------|
| Business rules | 43 |
| — BR-CUST | 28 |
| — BR-CUSTOPT | 15 |
| Owned tables | 8 |
| API endpoints (operations) | 30 |
| Data invariants | 13 |

## Files
- `00-component-inventory.md` — legacy components in scope
- `01-business-rules.md` — 43 business rules (BR-CUST-001..028, BR-CUSTOPT-001..015)
- `02-domain-model.md` — DDL (8 tables), state model, 13 invariants
- `03-api-design.md` — 30 endpoints
- `04-api-contract.yaml` — OpenAPI 3.1 (30 operations)
- `06-completion-summary.md` — counts + coverage
- `extraction-evidence.md` — source files read
- `FINAL-EXTRACTION-COMPLETE.md` — sign-off

## Scope
Shopper identity + registration/login/change-password flows, embedded billing/delivery addresses, gender, and the merchant-defined customer options / values / option-sets / per-shopper attributes engine.

## Cross-service boundaries (not owned here)
- **MS-02 identity** — password encoding + `authenticate()`, group/permission catalog (id references).
- **MS-06 cart** — cart merge on login (BR-CUST-022).
- **MS-01 reference data** — country / zone / language / store (id references).
- **External integrations** — human-verification provider (BR-CUST-020), notification emails (BR-CUST-021/025).
