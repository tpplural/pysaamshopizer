# MS-05 Customer Service — Completion Summary

**Service ID**: MS-05 · **Port**: 8005 · **Schema**: `customer_schema` · **Target**: Python/FastAPI + PostgreSQL 15+ · **Mode**: Direct Source

## Counts (verified against file content)

| Artifact | Count |
|----------|-------|
| Business rules total | 43 |
| — BR-CUST | 28 |
| — BR-CUSTOPT | 15 |
| Owned tables | 8 |
| API endpoints (operations) | 30 |
| Data invariants | 13 |
| Source files read | 24 |

**Rule-count decomposition (NOT a target):** the 43 rules = 24 legacy source components decomposed along their distinct behavioral seams (validation vs default vs state-transition vs cascade), starting from the 41 Phase-1 rules. Two net-new findings were produced by the deep read that Phase 1 did not carry as distinct rules:
- **BR-CUST-027** — gender silently defaults to Male when unset (`CustomerPopulator.populate`).
- **BR-CUST-028** — shopper hard-delete cascades to attributes in application code (`CustomerServiceImpl.delete`).

Plus one confirmed defect surface carried as a flagged rule: **BR-CUST-026** (REST create assigns the ADMIN group — suspected copy/paste defect). No rules were split to hit a number; no greenfield rules.

## Group breakdown
- **BR-CUST-001..028** (28): identity/lookup, registration, login/auth delegation, password lifecycle, embedded billing/delivery addresses, country/zone/language resolution, gender default, store scoping, group defaulting, delete cascade.
- **BR-CUSTOPT-001..015** (15): merchant-defined customer options, values, option-sets, and per-shopper attributes (the customer-configurability engine).

## Endpoint coverage
| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /customers | GET | CRUD-ONLY | — |
| /customers | POST | COVERED | BR-CUST-005/006/007/014/015/027 |
| /customers/{id} | GET | COVERED | BR-CUST-018/024 |
| /customers/{id} | PUT | COVERED | BR-CUST-015/017 |
| /customers/{id} | DELETE | COVERED | BR-CUST-018/028 |
| /customers/lookup | GET | COVERED | BR-CUST-001 |
| /customers/registration | POST | COVERED | BR-CUST-002/003/010/020/021 |
| /customers/login | POST | COVERED | BR-CUST-008/009/022 |
| /customers/{id}/password | POST | COVERED | BR-CUST-004/016/021 |
| /customers/{id}/password-reset | POST | COVERED | BR-CUST-006/021/025 |
| /customers/{id}/addresses/billing | GET | CRUD-ONLY | — |
| /customers/{id}/addresses/billing | PUT | COVERED | BR-CUST-011/013/019 |
| /customers/{id}/addresses/delivery | GET | CRUD-ONLY | — |
| /customers/{id}/addresses/delivery | PUT | COVERED | BR-CUST-012/013/019 |
| /customers/{id}/groups | GET | CRUD-ONLY | — |
| /customers/{id}/groups | POST | COVERED | BR-CUST-007/023 |
| /customers/{id}/groups/{groupId} | DELETE | COVERED | BR-CUST-023 |
| /customers/{id}/attributes | GET | CRUD-ONLY | — |
| /customers/{id}/attributes | PUT | COVERED | BR-CUSTOPT-010/011/012 |
| /customers/{id}/available-options | GET | COVERED | BR-CUSTOPT-015 |
| /customer-options | GET | CRUD-ONLY | — |
| /customer-options | POST | COVERED | BR-CUSTOPT-001/002/003/009 |
| /customer-options/{id} | GET | COVERED | BR-CUST-018 |
| /customer-options/{id} | PUT | COVERED | BR-CUSTOPT-002/003/009 |
| /customer-options/{id} | DELETE | COVERED | BR-CUSTOPT-013 |
| /customer-option-values | GET | CRUD-ONLY | — |
| /customer-option-values | POST | COVERED | BR-CUSTOPT-004/005/006/009 |
| /customer-option-values/{id} | DELETE | COVERED | BR-CUSTOPT-014 |
| /customer-option-sets | GET | CRUD-ONLY | — |
| /customer-option-sets | POST | COVERED | BR-CUSTOPT-007/008/009 |

## Semantic Preservation
All 43 rules carry an 8-dimension preservation table. One dimension flagged: **BR-CUST-026** (outcomes — preserved-as-flagged suspected defect). All other rules OK.

## Cross-service boundaries (documented, not owned)
- **MS-02 identity** — `authenticate()` + password encoding, group/permission catalog (id refs). BR-CUST-004/008/023.
- **MS-06 cart** — cart merge on login. BR-CUST-022.
- **MS-01 reference data** — country/zone/language/store (id refs). BR-CUST-013/014/024.
- **External** — human-verification provider (BR-CUST-020), notification emails (BR-CUST-021/025).

## Items requiring human clarification
- **BR-CUST-026** — REST create assigns ADMIN group to a shopper. Intentional or defect? (default recommendation: assign shopper group per BR-CUST-007).
- **BR-CUST-027** — target default gender MUST be configurable (per-store/service config) rather than hard-coded to Male; confirm the configured default and whether "unset" is allowed.
- **BR-CUST-004/025** — modernize to salted adaptive hashing + reset-link flow (drop clear-text password email).
- **BR-CUST-002** — add DB unique constraint on (store, username) (added as INV-CUST-002 in target).
