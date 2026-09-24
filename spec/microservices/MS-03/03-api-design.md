# MS-03 merchant-store — API Design

**Base path:** `/api/v1` · **Port:** 8003 · Field naming snake_case, paths kebab-case, enums PascalCase.
Global headers: `x-tenant-id` (present on every request), `x-correlation-id`, `Authorization` (Bearer).

## Endpoints

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| GET | `/api/v1/stores` | List merchant stores (paginated), excluding the reserved DEFAULT store | BR-MS-IDENT-003 |
| POST | `/api/v1/stores` | Create a store (validates fields, location, defaults; allocates id; emits `store.created`) | BR-MS-IDENT-001, BR-MS-FIELD-001, BR-MS-FIELD-002, BR-MS-DFLT-001..004, BR-MS-PERS-001, BR-MS-LIFE-001 |
| GET | `/api/v1/stores/{code}` | Get a single fully-resolved store by code | BR-MS-PERS-002, BR-MS-PERS-003, BR-MS-IDENT-003 |
| PUT | `/api/v1/stores/{code}` | Update an existing store (own-store guard; template not editable here) | BR-MS-PERS-001, BR-MS-LIFE-004, BR-MS-BRAND-002 |
| DELETE | `/api/v1/stores/{code}` | Decommission a store (superadmin only; starts `merchant.deleted` saga) | BR-MS-LIFE-002, BR-MS-LIFE-003 |
| GET | `/api/v1/stores/code-availability` | Check whether a store code is available | BR-MS-IDENT-002 |
| PUT | `/api/v1/stores/{code}/logo` | Upload/replace the store logo (bytes to content-cms, filename recorded) | BR-MS-BRAND-001 |
| DELETE | `/api/v1/stores/{code}/logo` | Remove the store logo | BR-MS-BRAND-001 |
| PUT | `/api/v1/stores/{code}/template` | Set the store presentation template | BR-MS-BRAND-002 |
| PUT | `/api/v1/stores/{code}/landing` | Provision/update the store landing area (content body to content-cms) | BR-MS-LAND-001 |
| GET | `/api/v1/stores/{code}/landing` | Get the store landing area metadata | BR-MS-LAND-001 |

## Notes

- `{code}` is the store business key (BR-MS-IDENT-001), used as the tenant-facing identifier in all sub-resources.
- Create/update validate xref codes (country, zone, currency, language) against MS-01 reference-data; unknown codes return 422.
- `POST /stores` returns 201 with the allocated id; `DELETE /stores/{code}` returns 202 (asynchronous decommission saga).
- `PUT /stores/{code}/logo` and `PUT /stores/{code}/landing` orchestrate cross-service writes to MS-11 content-cms; only the store-side metadata (logo filename, landing existence) is persisted in this service.
- The DEFAULT store is never returned by list and returns 404 on direct fetch (BR-MS-IDENT-003); it cannot be deleted (409).

## Events

| Event | Trigger | Consumers |
|-------|---------|-----------|
| `store.created` | store created (BR-MS-LIFE-001) | notification |
| `merchant.deleted` | store decommissioned (BR-MS-LIFE-002) | MS-04, MS-05, MS-07, MS-08, MS-09, MS-10, MS-11, MS-02 |
