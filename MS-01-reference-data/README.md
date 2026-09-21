# MS-01 — reference-data

Global, read-only reference provider for the modernized Shopizer platform: countries, zones
(states/provinces), currencies, and languages. Python 3.12 / FastAPI, PostgreSQL (schema
`reference_data`), Redis-backed read-through cache.

reference-data is **global / tenant-neutral** — it carries no `x-store-id` / `x-tenant-id` header
(documented ADR-006 exception). Only `x-correlation-id` (optional) and optional auth apply.

## Layout

```
src/reference_data/
  config.py          # pydantic-settings: DATABASE_URL, REDIS_URL, SERVICE_PORT
  database.py        # SQLAlchemy 2.x engine/session (Base)
  models.py          # ORM models (schema reference_data) — the 02-domain-model.md DDL
  repository.py      # data-access queries (resolve-by-code, localized name-sorted lists, ...)
  cache.py           # Redis read-through cache, fail-soft (BR-REF-CAC-001/002)
  seed_data.py       # pinned language/country/zone/currency catalogs (deterministic seed)
  service.py         # ALL 26 BR-IDs, one annotated method per rule
  errors.py          # shared ErrorResponse handlers (404/400/422/500)
  dependencies.py    # FastAPI DI wiring
  routers/           # 14 endpoints under /api/v1/reference
  main.py            # app, health probes, one-time startup seed
  dto/               # Pydantic v2 DTOs copied VERBATIM from spec/.../08-dtos
migrations/          # Alembic: 0001 creates schema + all tables/constraints/indexes
tests/               # pytest unit tests (in-memory SQLite — tests only)
```

## Configuration

Copy `.env.example` to `.env` and adjust. Required keys (see `spec/shared/env-schema.md`):

| Key | Purpose |
|-----|---------|
| `DATABASE_URL` | SQLAlchemy DSN (PostgreSQL) — **primary** runtime persistence |
| `REDIS_URL` | Read-through cache for reference lists + card-expiry lists |
| `SERVICE_PORT` | HTTP port (8001) |

## Run locally

```bash
# 1. Start infra (from sourcecode/)
docker compose up -d postgres redis

# 2. Install
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"

# 3. Create the schema + tables
alembic upgrade head

# 4. Run — the one-time seed runs automatically on startup when the DB is empty
uvicorn reference_data.main:app --host 0.0.0.0 --port 8001
```

Health: `GET /health`, `GET /health/alive`, `GET /health/ready` (503 if the DB is unreachable).

## Docker

```bash
docker build -t ms01-reference-data .
docker run --rm -p 8001:8001 \
  -e DATABASE_URL=postgresql+psycopg://saam:saam_local@host.docker.internal:5432/shopizer_dev \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  ms01-reference-data
```

## Endpoints (all under `/api/v1/reference`)

| Method | Path | Driving BR-IDs |
|--------|------|----------------|
| GET | `/countries?language&iso_codes&as` | LST-001, LST-004, LST-005 |
| GET | `/countries/{isoCode}` | RES-001 |
| GET | `/countries/{isoCode}/name?language` | API-002 |
| GET | `/countries/{isoCode}/zones?language` | LST-002 |
| GET | `/zones/{code}` | RES-004 |
| GET | `/zones/{code}/name?language` | API-002 |
| POST | `/provinces` `{country_code, lang?}` | API-001, LNG-003 |
| GET | `/currencies` | LST-006 |
| GET | `/currencies/{code}` | RES-003 |
| GET | `/languages` | LST-003 |
| GET | `/languages/resolve?locale` | LNG-001, LNG-002 (204 if no match) |
| GET | `/languages/{code}` | RES-002 |
| GET | `/credit-card-years` | API-003 |
| GET | `/months-of-year` | API-003 |

Envelopes (per `04-api-contract.yaml`): `{items:[...]}` for lists; a map keyed by `iso_code` for
`/countries?as=Map`; `{status, items}` (Success/Failure) for `/provinces`; `{value}` for the name
endpoints. Fields are snake_case. Reference reads are **fail-soft**: a missing list returns
`200 {items:[]}` (never 5xx). Resolve-by-code returns `404` on an unknown code (the name endpoints
echo the code at `200` instead).

## Seeding

On startup, if the database is empty (`language` count == 0, BR-REF-SEED-001) the service runs a
single atomic seed (BR-REF-SEED-002): languages (en, fr) → countries (localizable ISO catalog) →
zones (country/language catalog) → currencies (with real display names, NF-2). `geozone` ships
**empty** (BR-REF-SEED-GEO). The default store / tax class / product type / integration modules are
**moved out** to their owning services (BR-REF-SEED-006/007). A completed seed permanently disables
re-seed.

## Tests

```bash
pytest
```

Unit tests use an in-memory SQLite database (test-only — PostgreSQL via `DATABASE_URL` is the
runtime). They cover the seed guard, code resolution, localized name-sorted ordering, subset/map
forms, locale defaulting, provinces/name fail-soft, and card-expiry lists. They are NOT the
comprehensive suite (that is the separate Phase 4c quality gate).
