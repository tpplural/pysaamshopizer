# MS-06 Cart Service — Spec Index

| Attribute | Value |
|-----------|-------|
| Service Name | Cart Service |
| Service ID | MS-06 |
| Port | 8006 |
| Database Schema | `cart_schema` |
| Target Stack | Python / FastAPI + PostgreSQL 15+ |
| Analysis Mode | Direct Source (no CAST) |
| Legacy System | Shopizer 2.0.1 (Java / Spring MVC / JPA-Hibernate / QueryDSL) |

## Metrics

| Metric | Count |
|--------|-------|
| Business rules | 24 |
| — BR-CART | 24 |
| Owned tables | 3 |
| API endpoints (operations) | 11 |
| Data invariants | 6 |

## Files
- `00-component-inventory.md` — 19 legacy components in scope
- `01-business-rules.md` — 24 business rules (BR-CART-001..024)
- `02-domain-model.md` — DDL (3 tables), state model, 6 invariants
- `03-api-design.md` — 11 endpoints
- `04-api-contract.yaml` — OpenAPI 3.1 (11 operations)
- `06-completion-summary.md` — counts + coverage
- `extraction-evidence.md` — source files read
- `FINAL-EXTRACTION-COMPLETE.md` — sign-off

## Scope
The shopping-cart aggregate: cart identity token, store/shopper binding, line-item add/update/remove, per-line
subtotal preview, obsolete-cart cleanup on read, and merge of an anonymous session cart into a shopper's cart
on login. Owns 3 tables: `shopping_cart`, `shopping_cart_item`, `shopping_cart_attribute_item`.

## Cross-service boundaries (not owned here)
- **MS-09 order (totals) — decision BV-3.** The authoritative grand total (subtotal roll-up + tax + shipping +
  promotions) is delegated to the order service. The cart keeps only a per-line subtotal PREVIEW and owns no
  order/tax/shipping tables.
- **MS-04 catalog/pricing.** Item price snapshot/reprice, product existence, store-ownership, virtual/shippable
  flags, and product-attribute ownership are catalog reads.
- **MS-03 reference/store.** Store identity (id reference only).
- **MS-05 customer (caller).** Cart merge on login (`POST /carts/merge`) is triggered by the customer login
  flow (BR-CUST-022); the cart owns the merge mechanics (BR-CART-022/023).
