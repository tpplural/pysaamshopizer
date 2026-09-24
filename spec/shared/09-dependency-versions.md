# Shared Dependency Versions — Shopizer Modernization

> **Generated in Phase 4 Stage 1.5** (Dependency Version Manifest).
> Target stack (Phase 4b / Phase 0 assumption): **Python 3.12 + FastAPI + PostgreSQL 15+ + Redis +
> event messaging + OIDC**.
>
> **This file is the SINGLE SOURCE OF TRUTH for shared package versions.** Phase 5 code generators and
> Phase 4c test generation MUST consume these exact pins. Generators do **NOT** choose versions
> ad-hoc — pinning here eliminates version drift between the 11 services generated in parallel and
> prevents build failures from incompatible transitive dependencies. Update this file (only) when the
> target stack changes or a package has a known CVE; then regenerate affected services.
>
> Versions are exact GA pins (`==`). Every one of the 11 services uses this same set so cross-service
> DTOs, event payloads, and HTTP clients serialize identically.

## Messaging transport decision

The event bus (payment.captured / payment.refunded / order.placed / merchant.deleted — see
`spec/shared/event-schemas/`) is realized with **Redis Streams** for the v1 target, using the async
`redis-py` client's Streams API. Rationale: Redis is already in the stack (caching + cart session), so
v1 avoids standing up a separate broker; Redis Streams provides consumer groups, at-least-once
delivery, and per-key ordering, which satisfy the event guarantees documented in the schemas
(idempotent consumers dedupe on `transactionId` / `orderId` / `merchantId`). If event volume or
multi-region fan-out later outgrows Redis Streams, migrate to Kafka via `aiokafka` (listed below,
commented, as the documented upgrade path) — the event schemas are transport-agnostic.

## Pinned versions (`requirements`-style)

```
# ---- Web framework / ASGI ----
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.0

# ---- Persistence (PostgreSQL 15+) ----
sqlalchemy==2.0.36
asyncpg==0.30.0            # async PostgreSQL driver used by SQLAlchemy async engine
alembic==1.14.0           # schema migrations (entity-state models / DDL from 02-domain-model.md)

# ---- Cache + event transport (Redis Streams) ----
redis==5.2.1              # async client (redis.asyncio) + Streams API for the event bus
# aiokafka==0.12.0        # DOCUMENTED UPGRADE PATH ONLY — enable if the bus migrates off Redis Streams

# ---- Auth / OIDC (ADR-004) ----
authlib==1.4.0            # OIDC/OAuth2 client + JWT validation against the OIDC provider
python-jose[cryptography]==3.3.0   # JWT decode/verify helper for service-to-service bearer tokens

# ---- Outbound HTTP (cross-service calls in 05-dependencies.md) ----
httpx==0.28.1             # async client for all sync cross-service REST calls (timeouts/retries)

# ---- Resilience (timeouts / retries / circuit breakers per 05-dependencies.md) ----
tenacity==9.0.0           # retry/backoff policies
purgatory-circuitbreaker==0.7.2   # async circuit-breaker (open-after-N / half-open-after-Ns)

# ---- Observability ----
opentelemetry-api==1.29.0
opentelemetry-sdk==1.29.0
opentelemetry-instrumentation-fastapi==0.50b0
opentelemetry-instrumentation-httpx==0.50b0
structlog==24.4.0         # structured logging (x-correlation-id propagation)

# ---- Validation / serialization helpers ----
email-validator==2.2.0    # EmailStr validation (customer emailAddress, store email)
python-multipart==0.0.20  # multipart/form-data (content-cms image/logo/file uploads)

# ---- Testing (Phase 4c test suites) ----
pytest==8.3.4
pytest-asyncio==0.25.0
httpx==0.28.1             # (same pin) — test client for API assertions
respx==0.22.0             # mock cross-service HTTP dependencies in unit tests
testcontainers[postgres,redis]==4.9.0   # integration tests against real PostgreSQL 15 + Redis
```

## Runtime / infrastructure pins (non-Python)

```
python==3.12.x
postgresql==15.x          # minimum PostgreSQL 15 (entity-state models, JSONB config blobs)
redis==7.4.x              # server — cache + Redis Streams event bus
```

## Consumption rules (MANDATORY)

- Phase 5 code generation copies these exact pins into every service's dependency manifest
  (`pyproject.toml` / `requirements.txt`) VERBATIM. No generator selects a version independently.
- Phase 4c test generation uses the testing pins above; test suites run against the
  `testcontainers`-provided PostgreSQL 15 + Redis so they match production.
- The event-transport choice (Redis Streams via `redis`) is authoritative for both publisher services
  (MS-09, MS-10, MS-03) and consumer services (MS-09, and the `merchant.deleted` fan-out consumers).
- Any change to a pin here is a tracked change: update this file, note the reason (stack change / CVE),
  then regenerate the affected services so parallel builds stay in lock-step.

## Notes on the pinned set

- **pydantic 2.x** is required — the contracts are OpenAPI 3.1 and DTOs are generated as Pydantic v2
  models. (Field-naming camelCase-vs-snake_case is an open reconciliation item — see
  `assessment/shared-convention-reconciliation.md` Concern A; whichever the human confirms, it is
  implemented via Pydantic v2 alias configuration, not a version change.)
- **SQLAlchemy 2.0 + asyncpg** gives the async engine used by all services; **alembic** owns the DDL
  migrations derived from each `02-domain-model.md`.
- **httpx + tenacity + circuit-breaker** together implement the timeout / retry / circuit-breaker /
  fallback parameters written into every `05-dependencies.md`.
- **authlib / python-jose** implement the service-to-service bearer-token (OIDC target, ADR-004) that
  every cross-service call carries in its `Authorization` header.

> Package versions were selected as current GA releases at manifest-generation time. Verify against the
> registry and re-pin before a production build if significant time has elapsed. Content on external
> package versions was rephrased for compliance with licensing restrictions.
