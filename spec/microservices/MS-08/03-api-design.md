# MS-08 Shipping Service — API Design

**Service ID**: MS-08
**Port**: 8008
**Base path**: `/api/v1/shipping`
**Naming**: fields snake_case, query params snake_case, paths kebab-case, enum values PascalCase (National/International, Billing/Shipping, Least/Highest/All, Item/Box) — shared-convention reconciliation, 2026-09-19. ShippingReturnCode status codes stay UPPER_CASE (external/legacy status codes, not domain enum values).

All endpoints require `x-tenant-id` (store scope). Admin (configuration/authoring) endpoints additionally
require the `SHIPPING` role (BR-SHIP-030). The single legacy endpoint missing the role guard is preserved
and flagged (see BR-SHIP-030 / CI-12); the modernized delete endpoint is gated for safety and the gap is
documented.

## Endpoints

| # | Method | Endpoint | Description | Driven by |
|---|--------|----------|-------------|-----------|
| 1 | POST | /api/v1/shipping/quotes | Compute shipping options for a delivery + items (full quote pipeline) | BR-SHIP-002..018, 026..029 |
| 2 | POST | /api/v1/shipping/summary | Build the shipping summary from the customer-selected option | BR-SHIP-019 |
| 3 | POST | /api/v1/shipping/packages | Compute shippable packages (box or per-item) for items | BR-SHIP-009, 020..025 |
| 4 | POST | /api/v1/shipping/requires-shipping | Determine whether a set of cart items requires shipping | BR-SHIP-020 (virtual/shippable) |
| 5 | GET | /api/v1/shipping/configuration | Get the store shipping configuration | BR-SHIP-001 |
| 6 | PUT | /api/v1/shipping/configuration | Save the store shipping mode (type) | BR-SHIP-001 |
| 7 | PUT | /api/v1/shipping/options | Save free-shipping, handling, tax, price-type options | BR-SHIP-033 |
| 8 | PUT | /api/v1/shipping/packaging | Save box dimensions + package type (weight rounded 2dp) | BR-SHIP-034 |
| 9 | GET | /api/v1/shipping/supported-countries | List supported destination countries | BR-SHIP-004 |
| 10 | PUT | /api/v1/shipping/supported-countries | Replace the supported destination countries | BR-SHIP-004 |
| 11 | GET | /api/v1/shipping/methods | List region-eligible shipping methods for the store | BR-SHIP-007 |
| 12 | PUT | /api/v1/shipping/providers | Save (validate + store encrypted) a shipping provider configuration | BR-SHIP-031 |
| 13 | DELETE | /api/v1/shipping/providers/{moduleCode} | Remove a shipping provider configuration | BR-SHIP-030 (flagged), 031 |
| 14 | GET | /api/v1/shipping/providers/weight-based/configuration | Get the custom weight-based configuration | BR-SHIP-026 |
| 15 | POST | /api/v1/shipping/providers/weight-based/regions | Add a custom weight-based region | BR-SHIP-032 |
| 16 | DELETE | /api/v1/shipping/providers/weight-based/regions/{regionName} | Delete a custom weight-based region | BR-SHIP-032 |
| 17 | POST | /api/v1/shipping/providers/weight-based/regions/{regionName}/countries | Add a country to a region | BR-SHIP-032 |
| 18 | DELETE | /api/v1/shipping/providers/weight-based/regions/{regionName}/countries/{countryCode} | Remove a country from a region | BR-SHIP-032 |
| 19 | POST | /api/v1/shipping/providers/weight-based/regions/{regionName}/prices | Add a weight→price bracket | BR-SHIP-032 |
| 20 | DELETE | /api/v1/shipping/providers/weight-based/regions/{regionName}/prices/{maximumWeight} | Remove a weight bracket | BR-SHIP-032 |

**Endpoint count: 20** (matches 04-api-contract.yaml operations and metadata).

## Notes

- **Quote pipeline (endpoint 1)** is the hot path invoked by the ORDER service (MS-09) during checkout and
  the CART service (MS-06) for shipping eligibility. Product weight/dimensions/virtual flags and final
  prices are supplied in the request payload by the caller (catalog reads happen caller-side, MS-04).
- **Extension point:** the request may reference which provider handles the quote; the service resolves
  the first active configured provider (BR-SHIP-006). New quote providers plug in behind the same
  provider interface (see `spec/shared/extensibility-model.md`, EXT-SHIP-001/002).
- **CRUD-only note:** endpoints 5, 9, 11, 14 are reads with no business branching beyond store scoping;
  they are included because each surfaces a configuration document a rule depends on.
- **External carrier gateways (UPS/USPS/CanadaPost)** are out of scope: they are additional provider
  plug-ins reached through the same provider interface but their internals are not modelled here.
