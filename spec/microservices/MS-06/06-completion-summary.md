# Cart Service (MS-06) — Completion Summary

**Service ID**: MS-06 · **Port**: 8006 · **Schema**: `cart_schema`
**Target**: Python / FastAPI + PostgreSQL 15+ · **Analysis Mode**: Direct Source (no CAST)
**Status**: 🟢 Extraction complete (Phase 4)

## Counts (reconciled across INDEX / this file / FINAL)

| Metric | Count |
|--------|-------|
| Business rules (`### BR-` headers) | 24 |
| — BR-CART | 24 (BR-CART-001..024, contiguous) |
| Owned tables | 3 |
| API endpoints (operations) | 11 |
| Data invariants (INV- rows) | 6 |

## Decomposition outcome (anti-number-chasing)

24 rules = **16 source components read**, decomposed along the cart's behavioral seams: identity/lookup
(001–005), line-item lifecycle (006–012, 016–020), pricing/subtotal preview (009, 013, 018), total
delegation to MS-09 (014–016), obsolete cleanup (021), and login merge (022–024). This maps 1:1 to the
Phase-1 catalog BR-CART-001..024 because P1's grouping for this bounded single-aggregate segment was already
faithful — the deep read did NOT split by proc or pad the count.

The deep read produced **6 net-new findings** P1 flagged only as clarifications, now pinned to specific rules
with source lines:
1. **BR-CART-011** — virtual-product duplicate add is a silent no-op (`ShoppingCartFacadeImpl` ~131-133).
2. **BR-CART-017** — quantity-minimum guard exists on update but NOT on add (asymmetry). Closed in target by DB CHECK (INV-CART-003).
3. **BR-CART-021** — there is NO abandoned-cart TTL; "obsolete" is empty-or-products-gone, cleaned lazily on read.
4. **BR-CART-022** — merge duplicate condition (`user item HAS attributes`) is inverted vs add-to-cart (`item has NO attributes`).
5. **BR-CART-023** — merge passes the cart-attribute-item id to a product-attribute lookup (likely drops attributes).
6. **BR-CART-005** — by-customer / by-code tolerate >1 row and return the first despite the unique token index. Hardened by INV-CART-005.

No genuinely-greenfield rules were introduced; all 24 trace to legacy source.

## Semantic Preservation

Every rule carries an 8-dimension Semantic Preservation table. All dimensions are OK (source ≈ spec). No
CRITICAL (source>0, spec==0) dimension; no condensation flags. Control-flow counts exclude infrastructure
(transaction management, logging, null guards on framework params) per the extraction protocol.

| Source Component | Flagged Dimensions | Status | Notes |
|------------------|-------------------|--------|-------|
| ShoppingCartServiceImpl.java | none | OK | merge/obsolete/shipping fully preserved |
| ShoppingCartFacadeImpl.java | none | OK | add/update/remove/duplicate-merge preserved |
| ShoppingCartCalculationServiceImpl.java | none | OK | total delegation (BV-3) modeled as MS-09 integration |
| ShoppingCartDataPopulator.java | none | OK | item-count roll-up + summary passthrough |
| ShoppingCartDaoImpl.java | none | OK | store-scoped lookups |
| Entities (ShoppingCart/Item/AttributeItem) | none | OK | defaults, price snapshot, attribute binding |

## Endpoint Coverage

All 11 endpoints are COVERED by ≥1 BR-ID (see `03-api-design.md`). No pure-CRUD endpoints — every read carries
obsolete-cleanup and/or cross-service total/pricing behavior.

## Cross-service boundaries (confirmed, not owned)

| Boundary | Direction | Decision | Rules |
|----------|-----------|----------|-------|
| MS-09 Order (authoritative total) | cart → order | **BV-3** — cart keeps line subtotal preview only; total/tax/shipping/promotions owned by order | BR-CART-014, 015, 016 |
| MS-04 Catalog/Pricing | cart → catalog | price snapshot/reprice, product/attribute guards, virtual/shippable flags | BR-CART-007, 008, 009, 010, 018, 023, 024 |
| MS-03 Reference/Store | cart → reference | store id reference | BR-CART-003 |
| MS-05 Customer (login) | customer → cart | login triggers cart merge; cart owns merge mechanics | BR-CART-022, 023 |

## Data Model

3 owned tables with DDL, one entity state machine (`shopping_cart`: Anonymous → CustomerOwned → Deleted,
closed), and 6 data invariants (INV-CART-001..006). No DB logic objects (all logic app-tier; totals are MS-09).

## Deliverables present
- [x] 00-component-inventory.md
- [x] 01-business-rules.md (24 rules)
- [x] 02-domain-model.md (3 tables, 6 invariants, state model)
- [x] 03-api-design.md (11 endpoints)
- [x] 04-api-contract.yaml (OpenAPI 3.1, 11 operations, unique operationIds, refs resolve)
- [x] 06-completion-summary.md
- [x] extraction-evidence.md
- [x] INDEX.md
- [x] FINAL-EXTRACTION-COMPLETE.md

(Note: `05-dependencies.md` is intentionally NOT produced here — generated in Stage 1.5.)
