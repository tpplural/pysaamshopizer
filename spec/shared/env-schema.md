# Environment / Config Schema — Python 3.12 / FastAPI on containers

**The config-KEY contract** — the seam between the **app tier** (which keys a service READS at runtime) and
the **deploy tier** (where those values COME FROM). Both the Phase 5 generation TD (binds code to these key
names) and the IaC generator (assembles these values) read THIS artifact. Without it, each service invents
key names and the IaC generator has no authority to assemble against — the seam that fails silently at
deploy (a pod boots and can't connect).

`infrastructure-patterns.md` owns runtime *conventions*; this file owns the config *keys*.

## Config Keys (what each service READS at runtime)

| Key (app-side env var) | Type | Required | Value source (deploy-side) | Notes |
|------------------------|------|----------|----------------------------|-------|
| `DATABASE_URL` | secret | **yes (all)** | assembled from db credential secret + host + per-service db/schema name | SQLAlchemy DSN; db-per-service. Tenant scoping is per-query (`store_id`), NOT in the DSN. |
| `DB_POOL_SIZE` | config | no | shared config map (default 10) | connection pool sizing |
| `OIDC_ISSUER_URL` | config | **yes (all)** | shared config map (central IdP) | token issuer; used to fetch JWKS |
| `OIDC_JWKS_URL` | config | no | derived from issuer if absent | JWKS endpoint for token signature validation |
| `OIDC_AUDIENCE` | config | **yes (all)** | shared config map | expected token audience for this service |
| `REDIS_URL` | secret | per-cap | shared config map / secret | only cache-using services (MS-01 reference-data, MS-04 catalog, session holders) |
| `MESSAGE_BROKER_URL` | secret | per-cap | shared config map / secret | RabbitMQ AMQP URI. ONLY the 5 bus-touching services (payment, order, cart, identity, merchant). Read behind the broker-agnostic messaging port (D-09). |
| `OBJECT_STORE_ENDPOINT` | config | per-cap | shared config map | S3-compatible endpoint — ONLY MS-11 content-cms (EXT-CMS-001). |
| `OBJECT_STORE_BUCKET` | config | per-cap | per-service config | MS-11 only. |
| `OBJECT_STORE_ACCESS_KEY` / `OBJECT_STORE_SECRET_KEY` | secret | per-cap | per-service secret | MS-11 only. |
| `PAYMENT_GATEWAY_*` (endpoint + credentials) | secret | per-cap | per-service secret | ONLY MS-10 payment (EXT-PAY-001), per configured gateway. Legacy decrypted-in-app blob is replaced by secret-manager values (BR-PAY-008/009). |
| `SERVICE_PORT` | config | yes (all) | shared config map | 8001..8011 per service (see services-composition.md). |
| `LOG_LEVEL` | config | no | shared config map (default INFO) | structured logging. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | config | no | shared config map | OpenTelemetry collector. |

**Per-capability keys** are REQUIRED only for the services that have that capability — a service without the
capability MUST NOT read (or require) the key.

## Per-service required-key matrix

| Service | DATABASE_URL | OIDC_* | REDIS_URL | MESSAGE_BROKER_URL | OBJECT_STORE_* | PAYMENT_GATEWAY_* |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| MS-01 reference-data | ✅ | ✅ | ✅ | — | — | — |
| MS-02 identity-admin | ✅ | ✅ | — | ✅ (pub) | — | — |
| MS-03 merchant-store | ✅ | ✅ | — | ✅ (pub) | — | — |
| MS-04 catalog | ✅ | ✅ | ✅ | — | — | — |
| MS-05 customer | ✅ | ✅ | — | — | — | — |
| MS-06 cart | ✅ | ✅ | — | ✅ (sub) | — | — |
| MS-07 tax | ✅ | ✅ | — | — | — | — |
| MS-08 shipping | ✅ | ✅ | — | — | — | — |
| MS-09 order | ✅ | ✅ | — | ✅ (pub+sub) | — | — |
| MS-10 payment | ✅ | ✅ | — | ✅ (pub) | — | ✅ |
| MS-11 content-cms | ✅ | ✅ | — | — | ✅ | — |

## Assembly Rules (deploy-side)

- `DATABASE_URL` is **composed** from a DB credential secret + host + the per-service database/schema name;
  it is not passed through verbatim from a single source.
- `OIDC_ISSUER_URL` / `OIDC_AUDIENCE` / `LOG_LEVEL` / `OTEL_*` come from a **shared config map**.
- `MESSAGE_BROKER_URL`, `REDIS_URL`, `OBJECT_STORE_*`, `PAYMENT_GATEWAY_*` come from **per-service secrets**.
- **Fail-fast:** in deploy/prod, a missing REQUIRED key fails startup loudly. In the **Test** tier the same
  key degrades to an in-process double and NEVER throws (mirrors `infrastructure-patterns.md` Test-mode
  isolation).

## Read-vs-Provided Reconciliation (pre-deploy check)

Every REQUIRED key (global or per-capability) in the matrix above MUST have a source in the generated deploy
config for that service. This is verified **statically before deploy** (Test never exercises real runtime
config — the deploy-tier blind spot). It is NOT a shipped tool (the "provided" side is deploy-target
specific); each engagement runs a read-vs-provided grep/diff of app-read keys against IaC-provided keys per
service. A REQUIRED key with no provider is a deploy blocker.
