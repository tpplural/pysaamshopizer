# MS-06 Cart Service — FINAL EXTRACTION COMPLETE

**Service ID**: MS-06 · **Status**: 🟢 COMPLETE (Phase 4, Direct Source mode)
**Legacy**: Shopizer 2.0.1 (Java / Spring MVC / JPA-Hibernate / QueryDSL)

## Final reconciled counts

| Metric | Count |
|--------|-------|
| Business rules | 24 |
| — BR-CART | 24 (BR-CART-001..024) |
| Owned tables | 3 |
| API endpoints (operations) | 11 |
| Data invariants | 6 |

These counts are identical across `INDEX.md`, `06-completion-summary.md`, and this file.

## Files written (8 of the 9-file package; `05-dependencies.md` is Stage 1.5)
- [x] INDEX.md
- [x] 00-component-inventory.md
- [x] 01-business-rules.md
- [x] 02-domain-model.md
- [x] 03-api-design.md
- [x] 04-api-contract.yaml
- [x] 06-completion-summary.md
- [x] extraction-evidence.md
- [x] FINAL-EXTRACTION-COMPLETE.md

## Architectural decisions reflected
- **BV-3** — authoritative cart total (subtotal roll-up + tax + shipping + promotions) is DELEGATED to the
  Order service (MS-09) via a cross-service call. The cart keeps only a per-line subtotal PREVIEW and owns no
  order/tax/shipping tables. (BR-CART-014, 015, 016)
- **Cart merge on login** — modeled as inbound from MS-05 (login flow, BR-CUST-022); the cart owns the merge
  mechanics (BR-CART-022/023).
- **Item pricing / product guards** — cross-service reads to Catalog/Pricing (MS-04); store ref to MS-03.

## Net-new findings (carried to Phase 4a Human Clarification)
1. Virtual-product duplicate add is a silent no-op (BR-CART-011).
2. Quantity-minimum guard on update but not add (BR-CART-017) — hardened by INV-CART-003.
3. No abandoned-cart TTL; obsolete = empty/products-gone, cleaned on read (BR-CART-021).
4. Merge duplicate condition inverted vs add-to-cart (BR-CART-022).
5. Merge attribute lookup uses cart-attribute-item id instead of product-attribute id (BR-CART-023).
6. By-customer/by-code tolerate duplicate rows, return first (BR-CART-005) — hardened by INV-CART-005.

No genuinely-greenfield rules. Ready for Phase 4a.
