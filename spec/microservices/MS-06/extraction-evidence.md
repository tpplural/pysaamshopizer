# Cart Service (MS-06) — Extraction Evidence

**Analysis Mode**: Direct Source (no CAST). All files read in this Phase-4 session.
Root: `initial-source/shopizer/`.

## Source Files Processed

| # | File | Lines | Sections Read | Rules Extracted | Vectors Counted |
|---|------|-------|---------------|-----------------|-----------------|
| 1 | sm-core-model/.../shoppingcart/model/ShoppingCart.java | 155 | full (entity: code/store/customer/lineItems/obsolete) | BR-CART-001,002,003,004 (contributing) | ✅ |
| 2 | sm-core-model/.../shoppingcart/model/ShoppingCartItem.java | 233 | full (qty default, price/subtotal/virtual transients, attributes) | BR-CART-006,009,013 (contributing) | ✅ |
| 3 | sm-core-model/.../shoppingcart/model/ShoppingCartAttributeItem.java | 118 | full (product-attr binding) | BR-CART-010 (contributing) | ✅ |
| 4 | sm-core/.../shoppingcart/service/ShoppingCartServiceImpl.java | 542 | full multi-pass (getBy*, populate, merge, shipping/free) | BR-CART-002,005,006,009,012,013,016,021,022,023,024 | ✅ |
| 5 | sm-core/.../shoppingcart/service/ShoppingCartCalculationServiceImpl.java | 130 | full (calculate → OrderService, updateCartModel) | BR-CART-014,015,016 | ✅ |
| 6 | sm-core/.../shoppingcart/dao/ShoppingCartDaoImpl.java | 168 | full (by-id/by-code/by-customer, store filter, remove) | BR-CART-002,003,005 | ✅ |
| 7 | sm-shop/.../shoppingCart/facade/ShoppingCartFacadeImpl.java | 513 | full multi-pass (add/create/duplicate-merge/update/remove) | BR-CART-001,007,008,009,010,011,012,016,017,018,019 | ✅ |
| 8 | sm-shop/.../shoppingCart/ShoppingCartController.java | 400 | full (add/display/remove/update endpoints, empty-cart delete) | BR-CART-001,002,020 | ✅ |
| 9 | sm-shop/.../shoppingCart/MiniCartController.java | 95 | full (mini display/remove, empty-cart delete) | BR-CART-020 | ✅ |
| 10 | sm-shop/.../populator/shoppingCart/ShoppingCartDataPopulator.java | 175 | full (item-count roll-up, calls calculation) | BR-CART-013,014,015 | ✅ |
| 11 | sm-shop/.../populator/shoppingCart/ShoppingCartModelPopulator.java | 250 | full (DTO→model rebuild, guards, attr reconcile) | BR-CART-007,008,010 (corroborating) | ✅ |
| 12 | sm-shop/.../entity/shoppingcart/ShoppingCartData.java | 82 | full (cart view DTO shape) | — (DTO shape only) | ✅ |
| 13 | sm-core/.../shoppingcart/service/ShoppingCartService.java | (iface) | full | — (contract) | ✅ |
| 14 | sm-core/.../shoppingcart/service/ShoppingCartCalculationService.java | (iface) | full | — (contract) | ✅ |
| 15 | sm-core/.../shoppingcart/dao/ShoppingCartDao.java | (iface) | full | — (contract) | ✅ |
| 16 | sm-core/.../shoppingcart/dao/ShoppingCartItemDaoImpl.java | (empty) | full | — (no logic) | ✅ |

## Extraction Status
- Files total (business-logic + contracts read): 16
- Files processed: 16
- Rules extracted: 24 (BR-CART-001 .. BR-CART-024)
- Source vectors complete: yes (8-dimension table on every rule)

## Source Reference Validation
- All rule `Source Reference` paths resolve to files listed above (verified by directory listing + read).
- Line ranges are approximate (`~`) where the source was read as a whole unit; class:method tokens are exact.

## Session Log
| Session | Files Processed | Rules Added | Notes |
|---------|-----------------|-------------|-------|
| 1 | files 1-16 | 24 rules | Single-session extraction; entities + service + facade + controllers + populators all read before writing. |

## Notes on cross-service boundaries (evidence)
- `ShoppingCartCalculationServiceImpl.calculate()` calls `orderService.calculateShoppingCartTotal(...)` — the
  authoritative total is produced by the Order service (MS-09). Confirmed at lines ~90 and ~103. → BV-3.
- Pricing via `pricingService.calculateProductPrice(...)` and `ProductPriceUtils.getFinalProductPrice(...)`;
  product/attribute lookups via `productService.getById` / `productAttributeService.getById` — Catalog (MS-04).
- `mergeShoppingCarts(...)` is a cart-owned method; its caller is the customer login flow (MS-05, BR-CUST-022).
