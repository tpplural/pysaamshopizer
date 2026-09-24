# Cart Service (MS-06) — Component Inventory

**Service ID**: MS-06 · **Analysis Mode**: Direct Source (no CAST)
Legacy: Shopizer 2.0.1 (Java / Spring MVC, JPA/Hibernate + QueryDSL).

Scope = the shopping-cart aggregate: cart identity, line-item management, per-line subtotal preview,
obsolete-cart cleanup, and login merge. The authoritative order total (tax/shipping/promotions) is the
Order service's (MS-09, decision BV-3) — not in scope here.

## Legacy components in scope

| # | Component | Layer | Path (under `initial-source/shopizer/`) | Role in cart |
|---|-----------|-------|------------------------------------------|--------------|
| 1 | ShoppingCart.java | Entity | sm-core-model/.../business/shoppingcart/model/ShoppingCart.java | Cart aggregate root (code, store, customer, line items, transient obsolete) |
| 2 | ShoppingCartItem.java | Entity | sm-core-model/.../business/shoppingcart/model/ShoppingCartItem.java | Line item (qty, product ref, price snapshot, subtotal, virtual flag) |
| 3 | ShoppingCartAttributeItem.java | Entity | sm-core-model/.../business/shoppingcart/model/ShoppingCartAttributeItem.java | Selected product option on a line |
| 4 | ShoppingCartService.java | Service (iface) | sm-core/.../business/shoppingcart/service/ShoppingCartService.java | Cart service contract |
| 5 | ShoppingCartServiceImpl.java | Service | sm-core/.../business/shoppingcart/service/ShoppingCartServiceImpl.java | Cart CRUD, obsolete sweep, price snapshot, merge mechanics, shipping/free derivations |
| 6 | ShoppingCartCalculationService.java | Service (iface) | sm-core/.../business/shoppingcart/service/ShoppingCartCalculationService.java | Calculation contract |
| 7 | ShoppingCartCalculationServiceImpl.java | Service | sm-core/.../business/shoppingcart/service/ShoppingCartCalculationServiceImpl.java | Delegates total to Order service (BV-3), re-persists |
| 8 | ShoppingCartDao.java | DAO (iface) | sm-core/.../business/shoppingcart/dao/ShoppingCartDao.java | DAO contract |
| 9 | ShoppingCartDaoImpl.java | DAO | sm-core/.../business/shoppingcart/dao/ShoppingCartDaoImpl.java | By-code / by-id / by-customer lookups (store-scoped), remove |
| 10 | ShoppingCartItemDao.java | DAO (iface) | sm-core/.../business/shoppingcart/dao/ShoppingCartItemDao.java | Item DAO contract (empty) |
| 11 | ShoppingCartItemDaoImpl.java | DAO | sm-core/.../business/shoppingcart/dao/ShoppingCartItemDaoImpl.java | Item DAO impl (no business logic) |
| 12 | ShoppingCartFacade.java | Facade (iface) | sm-shop/.../shop/controller/shoppingCart/facade/ShoppingCartFacade.java | Facade contract |
| 13 | ShoppingCartFacadeImpl.java | Facade | sm-shop/.../shop/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java | add/update/remove orchestration, cart-model creation, duplicate-merge, reprice |
| 14 | ShoppingCartController.java | Controller | sm-shop/.../shop/controller/shoppingCart/ShoppingCartController.java | HTTP endpoints (add/display/remove/update), empty-cart auto-delete |
| 15 | MiniCartController.java | Controller | sm-shop/.../shop/controller/shoppingCart/MiniCartController.java | Mini-cart display + remove, empty-cart auto-delete |
| 16 | ShoppingCartDataPopulator.java | Populator | sm-shop/.../populator/shoppingCart/ShoppingCartDataPopulator.java | Builds cart view DTO: item-count roll-up, calls calculation service |
| 17 | ShoppingCartModelPopulator.java | Populator | sm-shop/.../populator/shoppingCart/ShoppingCartModelPopulator.java | Rebuilds cart model from DTO (guards, attribute reconciliation) |
| 18 | ShoppingCartData.java | DTO | sm-shop/.../entity/shoppingcart/ShoppingCartData.java | Cart view DTO (code, quantity, subtotal, total, totals, items) |
| 19 | CartModificationException.java | Exception | sm-shop/.../entity/order/CartModificationException.java | Thrown on quantity/unknown-entry update violations |

## Owned tables (3)
- `shopping_cart` (legacy `SHOPPING_CART`)
- `shopping_cart_item` (legacy `SHOPPING_CART_ITEM`)
- `shopping_cart_attribute_item` (legacy `SHOPPING_CART_ATTR_ITEM`)

Plus `SM_SEQUENCER` (id allocation) → replaced by native identity columns in target.

## External reads (not owned)
- `PRODUCT`, `PRODUCT_ATTRIBUTE` — Catalog/Pricing (MS-04), id refs.
- `MERCHANT_STORE` — Reference/Store (MS-03), id ref.
- Order/tax/shipping totals — Order (MS-09) via cross-service call (BV-3).

## Excluded / out of scope
- `ShoppingCartTestCase.java` (test fixture, not business logic).
- `webapp/resources/js/functions.js` (client-side AJAX cart cookie handling) — noted for the frontend spec, not backend scope.
- Order-total pipeline (`OrderServiceImpl.caculateOrder`) — owned by MS-09.
