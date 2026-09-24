# MS-04 Catalog Service — API Design

**Service ID:** MS-04
**Base path:** `/api/v1/catalog`
**Port:** 8004
**Naming:** snake_case JSON fields, kebab-case paths, PascalCase enum values.

Global headers on every request: `x-tenant-id` (store isolation — **documented Concern B exception:
catalog uses `x-tenant-id` ONLY, store == tenant, no separate `x-store-id`**), `x-correlation-id`. Admin-mutating
operations additionally require `Authorization: Bearer <token>` with the products management role
(BR-CATPROD-025). Storefront review submission requires an authenticated customer (BR-CATREV-004).

## Products

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /products | Create a product aggregate | BR-CATPROD-001,002,003,008,009,026 |
| PUT | /products/{id} | Update a product and reconcile children | BR-CATPROD-001,004,005 |
| GET | /products/{id} | Get a product by id | CRUD |
| DELETE | /products/{id} | Delete a product and cascade dependents | BR-CATPROD-006,007 |
| GET | /products | List store products (paged) | CRUD |
| POST | /products/{id}/descriptions | Add a localized description | BR-CATPROD-012 |
| POST | /products/{id}/availabilities | Add an availability | BR-CATPROD-015 |
| PUT | /products/{id}/availabilities/{availabilityId} | Update an availability | BR-CATPROD-016 |
| POST | /products/{id}/digital-file | Attach a downloadable file (marks virtual) | BR-CATPROD-017,019 |
| DELETE | /products/{id}/digital-file | Remove the downloadable file | BR-CATPROD-018 |
| GET | /products/{id}/digital-file | Get the product's downloadable file | BR-CATPROD-020 |
| POST | /products/{id}/relationships | Create a product relationship | BR-CATPROD-021,023 |
| PUT | /products/{id}/relationships/{relationshipId} | Update a relationship | BR-CATPROD-021 |
| GET | /storefront/products/{seUrl} | Storefront product read (visibility-gated, locale-trimmed) | BR-CATPROD-010,013 |
| GET | /storefront/categories/{categoryId}/products | List products in a category lineage | BR-CATPROD-014 |
| GET | /product-types/{code} | Resolve a product type by code | BR-CATPROD-024 |

## Relationship groups

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /relationship-groups | Create a group | BR-CATPROD-022 |
| PUT | /relationship-groups/{code}/activate | Activate a group | BR-CATPROD-022 |
| PUT | /relationship-groups/{code}/deactivate | Deactivate a group | BR-CATPROD-022 |
| DELETE | /relationship-groups/{code} | Delete a group | BR-CATPROD-022 |
| GET | /relationship-groups | List groups | BR-CATPROD-022 |

## Categories

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /categories | Create a category (derives lineage/depth) | BR-CATCAT-001,002,004,007,008 |
| PUT | /categories/{id} | Update a category | BR-CATCAT-009 |
| DELETE | /categories/{id} | Delete a category subtree, reconcile products | BR-CATCAT-012,013 |
| PUT | /categories/{id}/move | Reparent a category and its subtree | BR-CATCAT-005,006,010,011 |
| GET | /categories | List categories (ordered) | BR-CATCAT-014 |
| GET | /categories/code-available | Check code uniqueness | BR-CATCAT-003 |

## Manufacturers

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /manufacturers | Create a manufacturer | BR-CATMAN-001,006,007 |
| PUT | /manufacturers/{id} | Update a manufacturer | BR-CATMAN-001,003,007 |
| DELETE | /manufacturers/{id} | Delete a manufacturer (blocked if referenced) | BR-CATMAN-002,003,004 |
| GET | /manufacturers | List manufacturers | CRUD |
| POST | /manufacturers/{id}/image | Upload/validate a manufacturer image | BR-CATMAN-005 |

## Options / Values / Attributes

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /options | Create an option | BR-CATOPT-003,004,006,011,021,024 |
| PUT | /options/{id} | Update an option | BR-CATOPT-011,021,024 |
| DELETE | /options/{id} | Delete an option (cascade attributes) | BR-CATOPT-008,026 |
| GET | /options | List options (store-scoped) | BR-CATOPT-027 |
| GET | /options/{id}/type | Get an option's value-widget type | BR-CATOPT-022 |
| POST | /option-values | Create an option value | BR-CATOPT-005,006,012,021,025 |
| PUT | /option-values/{id} | Update an option value | BR-CATOPT-012,021 |
| DELETE | /option-values/{id} | Delete an option value (cascade attributes) | BR-CATOPT-009 |
| GET | /option-values | List option values (store-scoped) | BR-CATOPT-027 |
| POST | /products/{id}/attributes | Bind an option/value to a product | BR-CATOPT-001,002,010,013,014,015,016,017,018,019,020 |
| PUT | /products/{id}/attributes/{attributeId} | Update an attribute | BR-CATOPT-010 |
| DELETE | /products/{id}/attributes/{attributeId} | Delete an attribute | CRUD |
| GET | /products/{id}/attributes | List a product's attributes (language-preferred) | BR-CATOPT-023,027 |

## Pricing

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /products/{id}/prices | Create a price (validated) | BR-CATPRICE-012,013,014 |
| PUT | /products/{id}/prices/{priceId} | Update a price | BR-CATPRICE-013,014 |
| DELETE | /products/{id}/prices/{priceId} | Delete a price | BR-CATPRICE-015 |
| GET | /products/{id}/prices | List a product's prices (admin, has_discount indicator) | BR-CATPRICE-011 |
| GET | /products/{id}/final-price | Compute final price with default attributes | BR-CATPRICE-001..009 |
| POST | /products/{id}/final-price | Compute final price for selected attributes | BR-CATPRICE-010 |

## Images

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /products/{id}/images | Upload product images (non-default) | BR-CATIMG-001,002,003,006 |
| PUT | /products/{id}/images/{imageId} | Update image metadata/descriptions | BR-CATIMG-002 |
| DELETE | /products/{id}/images/{imageId} | Remove an image (file + record) | BR-CATIMG-005 |
| GET | /products/{id}/images | List product images (display paths) | BR-CATIMG-007 |
| GET | /products/{id}/images/{imageId} | Get a sized image variant | BR-CATIMG-004 |

## Reviews

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | /products/{id}/reviews | Submit a customer review (one per customer) | BR-CATREV-001,002,003,004,005 |
| GET | /products/{id}/reviews | List reviews for a product | BR-CATREV-007,008 |
| DELETE | /products/{id}/reviews/{reviewId} | Delete a review (admin, no aggregate recompute) | BR-CATREV-006 |

## Standard responses
- Success: 200 (read/update), 201 (create), 204 (delete).
- Errors: 400 bad request, 401 unauthorized, 403 forbidden, 404 not found, 409 conflict, 422 validation, 500 internal.
- List responses use `{ items: [...], pagination: {...} }`.
