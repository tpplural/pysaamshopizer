# Infrastructure Patterns — Python 3.12 / FastAPI

**Single source of truth for cross-cutting HTTP/runtime conventions.** ALL 11 services implement these
identically. Phase 4c test suites assert against them; Phase 5 generation applies them. Without this, each
service invents plumbing differently — the dominant class of systemic test failures (ENG-003).

**Wire convention:** JSON, **snake_case** field names (P4 exit-gate decision, Concern A). This matches the
`04-api-contract.yaml` of every service and the shared `spec/shared/common-schemas.yaml`. Pydantic v2 models
use snake_case fields directly (no camelCase aliasing).

---

## Health Endpoints

| Path | Purpose | Checks |
|------|---------|--------|
| `GET /health` | simple liveness | process up → `200` |
| `GET /health/alive` | liveness (k8s/ECS) | process up → `200` |
| `GET /health/ready` | readiness | DB reachable AND (if the service touches the bus) broker connection up |

Response body: `{ "status": "healthy" | "degraded" | "unhealthy" }` (snake_case, lowercase enum).
`/health/ready` returns `503` with `{"status":"unhealthy"}` when a dependency is down.

## Error Handling Middleware

A single FastAPI exception handler set produces these shapes (snake_case, matching the shared
`ErrorResponse` in `common-schemas.yaml`):

| Condition | HTTP | Body |
|-----------|------|------|
| Validation error (Pydantic / request) | `422` | `{ "error": "unprocessable_entity", "message": "...", "errors": [{ "field": "...", "message": "..." }] }` |
| Authentication failure | `401` | `{ "error": "unauthorized", "message": "..." }` |
| Authorization failure | `403` | `{ "error": "forbidden", "message": "..." }` |
| Not found | `404` | `{ "error": "not_found", "message": "..." }` |
| Conflict (unique/constraint) | `409` | `{ "error": "conflict", "message": "..." }` |
| Domain rule violation | `422` | `{ "error": "unprocessable_entity", "message": "...", "message_key": "<optional>" }` |
| Unhandled exception | `500` | `{ "error": "internal_error", "correlation_id": "..." }` |

- NEVER return a stack trace, framework HTML error page, or raw DB error to the client.
- `message_key` (optional) composes via `allOf` with the shared `ErrorResponse` — used by MS-10 payment for
  machine-readable failure reasons (P4 exit-gate exception).
- `422` is the canonical validation code across all services (matches every `04-api-contract.yaml`).

## Tenant Extraction

- **Header:** `x-store-id` (the store IS the tenant in Shopizer — MS-04/MS-08 store==tenant; MS-09/MS-10
  require it; MS-01 reference-data is global/tenant-neutral by exception).
- **Format:** UUID string. Validate on extraction; malformed → `400 {"error":"bad_request","message":"x-store-id must be a uuid"}`.
- **Injection:** a request-scoped FastAPI dependency (`get_store_context`) available to service/repository
  layers.
- **DB filter:** every owned table carries a `store_id` (or `merchant_id`) scoping column; repositories
  apply the tenant filter automatically. Cross-tenant reads are never implicit.
- **Exceptions (documented, from the P4 reconciliation):** MS-01 (global reference data, no tenant header);
  MS-02 global-kernel/admin endpoints use their own audience scoping, not `x-store-id`.

## Request / Response Conventions

- All responses JSON, **snake_case** (matching `04-api-contract.yaml`).
- **Paged lists:** `{ "items": [...], "total": N, "page": N, "page_size": N }`.
- **Non-paged lists:** `{ "items": [...] }` (P4 exit-gate envelope decision, Concern D).
- **Empty collections:** `200` with `{ "items": [] }` (or `{ "items": [], "total": 0 }` when paged) — NEVER
  `404`.
- **IDs on the wire:** `id`, `store_id`, `customer_id` etc. are UUID strings (P4 Concern F).
- **Enums on the wire:** PascalCase values where the domain uses them (e.g. MS-08 shipping enums — P4
  Concern G); documented per contract.
- **reference-data fail-soft:** MS-01 lookups that miss return `{ "status": "...", "items": [...] }` rather
  than erroring (BR-REF-CAC-002 fail-soft) — a documented per-service exception.

## Messaging (broker-agnostic port — D-09)

Services depend on a **port**, not on RabbitMQ directly. The RabbitMQ adapter is the only concrete impl
shipped (alternate providers are out of scope).

- **Ports:** `MessagePublisher.publish(topic, key, payload)` and `MessageConsumer.subscribe(topic, handler)`.
- **Delivery:** durable queues/exchanges; publisher confirms on; consumer manual-ack after successful handling.
- **Dead-letter:** each consumer queue has a DLQ; poison messages are dead-lettered, never infinitely retried.
- **Idempotency:** consumers are idempotent, keyed on `checkout_id` (payment↔order) or the event's business
  key. Replays and redeliveries must not double-apply (ADR-003 money-safety).
- **Event payloads:** as defined in `spec/shared/event-schemas/` (payment.captured, payment.refunded,
  order.placed, merchant.deleted). snake_case fields.
- **Only 5 services touch the bus:** payment (pub), order (pub+sub), cart (sub), identity (pub), merchant
  (pub). The other 6 ship no messaging code.

## Startup / Initialization

- **DB migration:** Alembic `upgrade head` on startup (dev/test); in prod, migrations run as a pre-deploy
  step, app verifies schema version on boot.
- **Test mode:** seed deterministic reference data; messaging + external gateways use in-process doubles
  (see Test-mode isolation below) — the readiness probe does NOT block on a real broker in test.
- **Messaging connect:** after DB ready; `/health/ready` waits on the broker connection for bus-touching
  services only.
- **Graceful shutdown:** stop accepting new requests, drain in-flight, stop consumers (finish acking
  in-flight handlers), close DB pool, exit.

## Test-Mode Dependency Isolation (first-order test-pass driver — ENG-003)

- In the Test profile, the messaging port binds to an **in-memory fake** (records published events for
  assertions; delivers to registered handlers synchronously). No real RabbitMQ required to run the suite.
- External payment gateways (EXT-PAY-001) bind to a **stub adapter** returning deterministic results.
- The object store (EXT-CMS-001) binds to a **local/temp filesystem or in-memory** implementation in Test.
- DB uses a real PostgreSQL (or a per-test schema) — integrity constraints and the Layer-C cascade/set-based
  operations MUST be exercised against a real engine, not mocked.
- A missing REQUIRED runtime config key degrades to a Test double and NEVER throws in Test (mirrors
  `env-schema.md` fail-fast-in-prod / degrade-in-test rule).

## Logging / Observability

- Structured JSON logging in prod, console in dev.
- **Correlation ID:** read from `x-correlation-id` if present, else generate; propagate through the request,
  DB calls, and any published events; include in the `500` body.
- OpenTelemetry traces for HTTP requests, DB queries, and messaging publish/consume.

## Notes

- Terminology is FastAPI/Python-specific but the CONVENTIONS are the contract; a service may not diverge.
- Any field-name casing question is resolved by `04-api-contract.yaml` (snake_case) + this document.
