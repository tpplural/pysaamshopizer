# Shared Auth & Header Config — Shopizer Modernization

> DERIVED from the Stage 1.5 shared-convention reconciliation (Concern B), after the human signal
> (`assessment/shared-convention-reconciliation-completed.md`, 2026-09-19). Defined ONCE here and
> referenced by every service's `04-api-contract.yaml` (via `spec/shared/common-schemas.yaml`
> parameters `TenantHeader` / `StoreHeader` / `CorrelationHeader`).

## Standard header set (store-scoped services)

| Header | Required | Purpose |
|--------|----------|---------|
| `x-tenant-id` | required | Multi-tenancy isolation — every query scoped to this tenant. |
| `x-store-id` | required on all store-scoped operations | Store-level scoping within a tenant. **Made required on MS-09 order and MS-10 payment** (were optional — Concern B fix). Absent only where store == tenant. |
| `x-correlation-id` | optional | Distributed tracing; propagated across cross-service calls. |
| `Authorization: Bearer <token>` | required on mutating/admin ops | Service-to-service + user auth via OIDC (ADR-004). |

## Documented exceptions (legitimately service-specific — kept, not normalized)

| Service | Exception | Rationale |
|---------|-----------|-----------|
| MS-01 reference-data | No `x-tenant-id` / `x-store-id`; uses `x-correlation-id` (+ optional auth) only | Global read-only shared kernel (ADR-006). Country/zone/language/currency are not tenant-scoped. |
| MS-04 catalog | `x-tenant-id` only (no separate `x-store-id`) | In this domain store == tenant; documented in-service. |
| MS-08 shipping | `x-tenant-id` only (store folded into tenant) | Store scoping folded into the tenant header; documented in-service. |

## Test values (normalized — Concern B)

- `x-tenant-id` test value: `test-tenant-001` (all services).
- `x-store-id` test value: `test-store-001` (all services). **MS-05 customer normalized from `"1"` → `test-store-001`.**

## Auth (OIDC target, ADR-004)

Legacy Spring Security form-login + SHA-1/null-salt passwords are replaced by central OAuth2/OIDC. All
cross-service calls carry a service-to-service bearer token; user-facing endpoints validate the user's
OIDC access token. Password storage (MS-05 BR-CUST-004, MS-02) migrates to a salted adaptive hash
(bcrypt/argon2) — see the identity/customer specs. Token validation library pinned in
`spec/shared/09-dependency-versions.md` (authlib / python-jose).
