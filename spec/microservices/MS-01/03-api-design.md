# reference-data (MS-01) — API Design

**Base path:** `/api/v1/reference` · **Port:** 8001
**Naming:** paths kebab-case, JSON fields snake_case, enum values PascalCase (locked in
`04-api-contract.yaml` `x-naming-conventions`).
**Global headers:** no `x-tenant-id` / `x-store-id` (reference data is global, not tenant-scoped —
documented Concern B exception, ADR-006); only `x-correlation-id` (+ optional auth) applies. Reference
lookups are shared across tenants.

> reference-data is a **leaf provider**: it exposes read endpoints only. There is no create/update/delete
> API for reference entities — the legacy system has no admin CRUD for them; they are seed-once,
> read-thereafter (see Data Access Patterns in the Phase 1 summary). The seed is an internal startup
> process, not an endpoint.

## Endpoints

### Countries
| Method | Path | Purpose | Driven by |
|--------|------|---------|-----------|
| GET | `/api/v1/reference/countries` | List countries for a language, name-sorted; optional `iso_codes` subset filter; optional `as=map` | BR-REF-LST-001, BR-REF-LST-004, BR-REF-LST-005 |
| GET | `/api/v1/reference/countries/{isoCode}` | Resolve one country by ISO code | BR-REF-RES-001 |
| GET | `/api/v1/reference/countries/{isoCode}/name` | Localized display name, echoes code if unresolved | BR-REF-API-002 |
| GET | `/api/v1/reference/countries/{isoCode}/zones` | List a country's zones for a language, name-sorted | BR-REF-LST-002 |

### Zones
| Method | Path | Purpose | Driven by |
|--------|------|---------|-----------|
| GET | `/api/v1/reference/zones/{code}` | Resolve one zone by code | BR-REF-RES-004 |
| GET | `/api/v1/reference/zones/{code}/name` | Localized zone display name, echoes code if unresolved | BR-REF-API-002 |
| POST | `/api/v1/reference/provinces` | Address-form province lookup: country code (+optional lang) → zones as {name,code,id}, fail-soft | BR-REF-API-001, BR-REF-LNG-003 |

### Currencies
| Method | Path | Purpose | Driven by |
|--------|------|---------|-----------|
| GET | `/api/v1/reference/currencies` | List all currencies, code-sorted | BR-REF-LST-006 |
| GET | `/api/v1/reference/currencies/{code}` | Resolve one currency by code | BR-REF-RES-003 |

### Languages
| Method | Path | Purpose | Driven by |
|--------|------|---------|-----------|
| GET | `/api/v1/reference/languages` | List all configured languages | BR-REF-LST-003 |
| GET | `/api/v1/reference/languages/{code}` | Resolve one language by code | BR-REF-RES-002 |
| GET | `/api/v1/reference/languages/resolve` | Map a locale/Accept-Language to a configured language (204 if none) | BR-REF-LNG-002, BR-REF-LNG-001 |

### Form-support lists (card expiry)
| Method | Path | Purpose | Driven by |
|--------|------|---------|-----------|
| GET | `/api/v1/reference/credit-card-years` | Rolling 10-year expiry list (current year .. +9), cached | BR-REF-API-003 |
| GET | `/api/v1/reference/months-of-year` | Months "01".."12", cached | BR-REF-API-003 |

## Endpoint Coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| `/countries` | GET | COVERED | BR-REF-LST-001, LST-004, LST-005 |
| `/countries/{isoCode}` | GET | COVERED | BR-REF-RES-001 |
| `/countries/{isoCode}/name` | GET | COVERED | BR-REF-API-002 |
| `/countries/{isoCode}/zones` | GET | COVERED | BR-REF-LST-002 |
| `/zones/{code}` | GET | COVERED | BR-REF-RES-004 |
| `/zones/{code}/name` | GET | COVERED | BR-REF-API-002 |
| `/provinces` | POST | COVERED | BR-REF-API-001, LNG-003 |
| `/currencies` | GET | COVERED | BR-REF-LST-006 |
| `/currencies/{code}` | GET | COVERED | BR-REF-RES-003 |
| `/languages` | GET | COVERED | BR-REF-LST-003 |
| `/languages/{code}` | GET | COVERED | BR-REF-RES-002 |
| `/languages/resolve` | GET | COVERED | BR-REF-LNG-001, LNG-002 |
| `/credit-card-years` | GET | COVERED | BR-REF-API-003 |
| `/months-of-year` | GET | COVERED | BR-REF-API-003 |

All 14 endpoints are COVERED by at least one business rule (no CRUD-only, no uncovered endpoints).
`GET /countries` carries the map/subset behaviors via query params (`as`, `isoCodes`) rather than
separate paths (`as`, `iso_codes`), matching the legacy service methods `getCountriesMap` /
`getCountries(isoCodes,...)`.

## Deliberately absent endpoints
- **No geo-zone endpoints** — geo-zones ship empty and have no legacy service (BR-REF-SEED-GEO). Add only
  when the capability is genuinely implemented.
- **No write endpoints** — no create/update/delete for reference entities (no legacy admin CRUD path).
- **No seed endpoint** — the bootstrap (BR-REF-SEED-001..005) is an internal startup process.
