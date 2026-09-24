# MS-07 (tax) — API Design

**Version**: 1.0
**Service ID**: MS-07
**Base path**: `/api/v1/tax`
**Port**: 8007
**Auth**: all endpoints require role `TAX` (legacy `@PreAuthorize("hasRole('TAX')")`); calculation is a
service-to-service call from MS-09 (order) at checkout.

Naming conventions: JSON fields `snake_case`, query params `snake_case`, paths `kebab-case`, enum values `PascalCase` (shared-convention reconciliation, 2026-09-19).

## Endpoints

| # | Method | Endpoint | Description | Driven by |
|---|--------|----------|-------------|-----------|
| 1 | POST | `/api/v1/tax/calculate` | Calculate tax over an order (the calculation engine). Returns tax lines or null. | BR-TAX-002,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,019,020,021,022,023,024 |
| 2 | GET | `/api/v1/tax/configuration` | Get the current store's tax configuration (defaults if none saved). | BR-TAX-001,002 |
| 3 | PUT | `/api/v1/tax/configuration` | Create or update the store's tax configuration. | BR-TAX-001,003 |
| 4 | GET | `/api/v1/tax/tax-classes` | List the store's tax classes (DEFAULT hidden from the list). | BR-TAX-025 (list; hides DEFAULT) |
| 5 | POST | `/api/v1/tax/tax-classes` | Create a tax class. | BR-TAX-025 |
| 6 | GET | `/api/v1/tax/tax-classes/{id}` | Get a tax class by id (store-ownership guard). | CRUD — no BR-ID (read with ownership guard) |
| 7 | PUT | `/api/v1/tax/tax-classes/{id}` | Update a tax class. | BR-TAX-025 |
| 8 | DELETE | `/api/v1/tax/tax-classes/{id}` | Delete a tax class (blocked if products reference it). | BR-TAX-026 |
| 9 | GET | `/api/v1/tax/tax-rates` | List the store's tax rates (rate displayed to 3 decimals). | BR-TAX-028 (3dp display) |
| 10 | POST | `/api/v1/tax/tax-rates` | Create a tax rate. | BR-TAX-027 |
| 11 | GET | `/api/v1/tax/tax-rates/{id}` | Get a tax rate by id (store-ownership guard; rate displayed to 3 decimals). | BR-TAX-028 |
| 12 | PUT | `/api/v1/tax/tax-rates/{id}` | Update a tax rate. | BR-TAX-027 |
| 13 | DELETE | `/api/v1/tax/tax-rates/{id}` | Delete a tax rate. | CRUD — no BR-ID (id guard then delete) |

## Endpoint Detail

### POST /api/v1/tax/calculate
The calculation engine. Request carries the order context (items with unit price, quantity, tax-class
code; shipping + handling; the customer billing/delivery jurisdiction; the store; language). Applies
BR-TAX-002 through BR-TAX-024. Returns a list of tax lines (`label`, `code`, `rate`, `amount`) or `null`
when no tax applies. **Preserved behavior:** jurisdiction is always the billing address (BR-TAX-007);
shipping+handling always taxed under DEFAULT class (BR-TAX-014); tax-class does not filter rates
(BR-TAX-019); duplicate-code lines deduped to first (BR-TAX-023); null vs empty-list distinction
(BR-TAX-024).

### GET / PUT /api/v1/tax/configuration
Get returns the store's configuration, defaulting to `ShippingAddress` basis with province collection on
and cross-country off when none is saved (BR-TAX-001/002/010). Put upserts the configuration.
**Preserved behavior:** the two collection flags are accepted but not round-tripped by the legacy
serialization (BR-TAX-003) — documented and flagged.

### Tax classes (list/create/get/update/delete)
List hides the reserved DEFAULT class. Create rejects the reserved code DEFAULT and duplicate codes;
update rejects a duplicate code belonging to a different class (BR-TAX-025). Delete is blocked when any
product references the class (BR-TAX-026). Get by id enforces the store-ownership guard.

### Tax rates (list/create/get/update/delete)
Create/update validate a present+parseable rate, a store-unique code, default priority 0, resolve
zone/country to reference entities, and clear the parent link for non-piggyback rates (BR-TAX-027). List
and get display the rate to three decimals (BR-TAX-028). Get by id enforces the store-ownership guard.

## Endpoint Coverage Summary
- Total endpoints: 13
- COVERED by ≥1 BR-ID: 11
- CRUD-only (no BR-ID): 2 — `GET /tax-classes/{id}` (read with ownership guard), `DELETE /tax-rates/{id}` (id guard then delete)
