# Cart Service (MS-06) — API Design

**Service ID**: MS-06 · **Port**: 8006 · **Base path**: `/api/v1/carts`
**Naming**: fields snake_case, paths kebab-case, enums PascalCase (Python/FastAPI + PostgreSQL 15+).
**Global headers**: `x-tenant-id` (required), `x-store-id` (required — cart is store-scoped, BR-CART-003).

The authoritative money total is delegated to the Order service (MS-09) — the `summary` endpoint is the
cart's façade over that cross-service call (BV-3, BR-CART-014/015). Item pricing and product/attribute
guards read the Catalog service (MS-04). Cart merge is invoked by the Customer login flow (MS-05).

## Endpoints (11 operations)

| # | Method | Path | operationId | Description | Driven by |
|---|--------|------|-------------|-------------|-----------|
| 1 | POST | `/carts` | createCart | Create a cart; honor a supplied token or mint one; bind store, optional shopper | BR-CART-001, BR-CART-003, BR-CART-004 |
| 2 | GET | `/carts/{code}` | getCart | Fetch a cart by its client token within the store; obsolete-cleanup on read | BR-CART-002, BR-CART-021 |
| 3 | GET | `/carts` | getCartByCustomer | Fetch the shopper's single active cart (query `customer_id`) | BR-CART-005 |
| 4 | POST | `/carts/{code}/items` | addCartItem | Add an item (existence/store/attribute guards, price snapshot, duplicate-merge) | BR-CART-006, BR-CART-007, BR-CART-008, BR-CART-009, BR-CART-010, BR-CART-011, BR-CART-012, BR-CART-016 |
| 5 | PATCH | `/carts/{code}/items/{itemId}` | updateCartItem | Update one line's quantity (min-1 guard, reprice) | BR-CART-017, BR-CART-018, BR-CART-016 |
| 6 | PUT | `/carts/{code}/items` | updateCartItems | Batch update line quantities (min-1 guard, reprice) | BR-CART-017, BR-CART-018, BR-CART-016 |
| 7 | DELETE | `/carts/{code}/items/{itemId}` | removeCartItem | Remove a line; auto-delete the cart if it becomes empty | BR-CART-019, BR-CART-020 |
| 8 | DELETE | `/carts/{code}` | deleteCart | Delete the whole cart | BR-CART-020 |
| 9 | GET | `/carts/{code}/summary` | getCartSummary | Cart view with authoritative totals (delegated to MS-09) + item-count roll-up | BR-CART-014, BR-CART-015 |
| 10 | GET | `/carts/{code}/shipping-eligibility` | getCartShippingEligibility | Derive requires-shipping / free-cart / shippable items | BR-CART-024 |
| 11 | POST | `/carts/merge` | mergeCarts | Merge an anonymous session cart into the shopper's cart (called by MS-05 login) | BR-CART-022, BR-CART-023 |

## Endpoint coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /carts | POST | COVERED | BR-CART-001, BR-CART-003, BR-CART-004 |
| /carts/{code} | GET | COVERED | BR-CART-002, BR-CART-021 |
| /carts | GET | COVERED | BR-CART-005 |
| /carts/{code}/items | POST | COVERED | BR-CART-006..012, BR-CART-016 |
| /carts/{code}/items/{itemId} | PATCH | COVERED | BR-CART-016, BR-CART-017, BR-CART-018 |
| /carts/{code}/items | PUT | COVERED | BR-CART-016, BR-CART-017, BR-CART-018 |
| /carts/{code}/items/{itemId} | DELETE | COVERED | BR-CART-019, BR-CART-020 |
| /carts/{code} | DELETE | COVERED | BR-CART-020 |
| /carts/{code}/summary | GET | COVERED | BR-CART-014, BR-CART-015 |
| /carts/{code}/shipping-eligibility | GET | COVERED | BR-CART-024 |
| /carts/merge | POST | COVERED | BR-CART-022, BR-CART-023 |

Every endpoint is driven by ≥1 business rule; there are no pure-CRUD endpoints in this service (all reads
carry obsolete-cleanup or cross-service total/pricing behavior).

## Cross-service calls (consumer perspective — detailed in Stage 1.5 `05-dependencies.md`)

| Target | Why | Triggered by |
|--------|-----|--------------|
| MS-09 Order (totals) | authoritative subtotal/tax/shipping/promotion total — BV-3 | BR-CART-014, BR-CART-015, BR-CART-016 |
| MS-04 Catalog/Pricing | product existence, store-ownership, price snapshot/reprice, attribute ownership, virtual/shippable flags | BR-CART-007, BR-CART-008, BR-CART-009, BR-CART-010, BR-CART-018, BR-CART-023, BR-CART-024 |
| MS-03 Reference/Store | store existence (id ref) | BR-CART-003 |

## Inbound cross-service (this service is the provider)

| Caller | Operation | Rule |
|--------|-----------|------|
| MS-05 Customer (login flow) | `POST /carts/merge` | BR-CART-022 (cart owns merge mechanics; MS-05 is the caller) |
