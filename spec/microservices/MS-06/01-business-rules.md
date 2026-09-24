# Cart Service (MS-06) — Business Rules

**Version**: 1.0
**Service ID**: MS-06
**Status**: 🟢 Extraction complete (Phase 4, Direct Source mode)
**Legacy system**: Shopizer 2.0.1 (Java / Spring MVC / JPA-Hibernate / QueryDSL)
**Group**: `BR-CART` (shopping-cart aggregate — cart identity, line-item management, line subtotal preview, obsolete-cart cleanup, login merge) — 24 rules
**Total**: 24 rules

> Statements are architecture-agnostic (domain terms only). Legacy class/table/column names appear ONLY in Logic and Source Reference. All source paths are under `initial-source/shopizer/`.

## Architectural boundaries (reflected in the rules below)

- **Authoritative order total is owned by the Order service (MS-09) — decision BV-3.** The cart computes and keeps a per-line **subtotal preview** (`item price × quantity`) for display, but the authoritative grand total (subtotal roll-up + tax + shipping + promotions) is DELEGATED to the order service via a cross-service call. In legacy this is `ShoppingCartCalculationServiceImpl.calculate()` → `orderService.calculateShoppingCartTotal(...)`. The cart does NOT own tax/shipping/promotion logic and owns no order/tax/shipping tables. See BR-CART-014, BR-CART-015, BR-CART-016.
- **Item pricing is owned by the Catalog/Pricing service (MS-04).** Snapshotting a line item's unit price calls the catalog pricing service (`pricingService.calculateProductPrice`). Product existence, virtual/shippable flags and product-attribute ownership are catalog reads (MS-04). See BR-CART-007..010, BR-CART-013, BR-CART-018, BR-CART-024.
- **Store scoping is a reference read (MS-03).** A cart is bound to a merchant store; store identity is an id reference only.
- **Login merge is triggered by the Customer service (MS-05).** `mergeShoppingCarts(...)` is invoked from the customer login flow (MS-05, BR-CUST-022). The cart OWNS the merge mechanics (BR-CART-022/023); MS-05 is the caller.

---

### BR-CART-001: Cart identity token generation

**Source Reference:** `ShoppingCartFacadeImpl.java:createCartModel:~289-311`; `ShoppingCartController.java:addShoppingCartItem:~161-166`; `ShoppingCart.java:shoppingCartCode:57-64`
**Discovery Method:** Direct Source Read
**Statement:** Every cart is assigned a unique, client-facing identity token when it is created. If the client supplies a token, that token is honored; otherwise a fresh opaque 32-character token is generated. This token — not the internal numeric id — is what the client uses to fetch its cart later.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
createCartModel(shoppingCartCode, store, customer):
    cart = new ShoppingCart()
    IF isNotBlank(shoppingCartCode): cart.shoppingCartCode = shoppingCartCode
    ELSE: cart.shoppingCartCode = UUID.randomUUID().toString().replaceAll("-", "")   // 32 hex chars, no dashes
    cart.merchantStore = store
    IF customer != null: cart.customerId = customer.id
    shoppingCartService.create(cart)   // INSERT SHOPPING_CART
```
The identical generation is duplicated in the controller when no cart exists yet (`ShoppingCartController.java:164`).
**Data Dependencies:**
- Reads: (request) supplied cart code, store id, customer id
- Writes: shopping_cart.cart_code, shopping_cart.merchant_id, shopping_cart.customer_id
**Side Effects:** INSERT into `shopping_cart`.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (32-char hex token) |
| State transitions | 1 | 1 | OK (none → created) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts {"storeId":1}` (no code supplied)
- Success: `201 {"code":"5f3c2a1b9d8e4f70a1b2c3d4e5f60718","id":"...","storeId":1,"items":[],"quantity":0}`
- Error Input: `POST /api/v1/carts {}` (no store context header)
- Error Output: `400 {"error":"BadRequest","message":"Store context is required"}`

---

### BR-CART-002: Cart is retrieved by its client token, scoped to the store

**Source Reference:** `ShoppingCartDaoImpl.java:getByCode:~103-124`; `ShoppingCartServiceImpl.java:getByCode:~157-192`; `ShoppingCart.java:shoppingCartCode:57-64`
**Discovery Method:** Direct Source Read
**Statement:** A cart is looked up by its client-facing token together with the owning store. A token is only ever resolved within its store, so a token issued by one store can never return another store's cart.
**Intent:** Routing
**Weight:** High
**Statement note:** This is the read counterpart of the tenant-scoping guard in BR-CART-003.
**Logic:**
```pseudocode
getByCode(code, store):
    results = query.where(shoppingCartCode == code AND merchantStore.id == store.id).list()
    IF results.isEmpty(): return null
    ELSE return results.get(0)   // tolerates >1, returns first — see BR-CART-005 note
```
**Data Dependencies:**
- Reads: shopping_cart.cart_code, shopping_cart.merchant_id
**Side Effects:** None (read).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/carts/5f3c2a1b9d8e4f70a1b2c3d4e5f60718` (`x-store-id: 1`)
- Success: `200 {"code":"5f3c...0718","items":[...],"quantity":2}`
- Error Input: `GET /api/v1/carts/5f3c...0718` (`x-store-id: 2` — token belongs to store 1)
- Error Output: `404 {"error":"NotFound","message":"No cart for this code in this store"}`

---

### BR-CART-003: A cart always belongs to exactly one store (tenant isolation)

**Source Reference:** `ShoppingCart.java:merchantStore:66-68`; `ShoppingCartDaoImpl.java:getById:~78-99`; `ShoppingCartDaoImpl.java:getByCode:~103-124`
**Discovery Method:** Direct Source Read
**Statement:** A cart must be associated with a single merchant store, and that association is mandatory. Every cart lookup filters by store, guaranteeing carts are never shared or leaked across stores.
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
// ShoppingCart.merchantStore @JoinColumn(nullable=false)
// every by-id / by-code lookup adds: .and(qShoppingCart.merchantStore.id.eq(store.getId()))
```
**Data Dependencies:**
- Reads: shopping_cart.merchant_id
**Side Effects:** None (persistence constraint + read filter).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts {"storeId":1}`
- Success: `201 {"code":"...","storeId":1}`
- Error Input: `POST /api/v1/carts {"storeId":null}`
- Error Output: `422 {"error":"Unprocessable","message":"A cart must belong to a store"}`

---

### BR-CART-004: A cart may optionally be owned by a shopper

**Source Reference:** `ShoppingCart.java:customerId:70-73`; `ShoppingCartFacadeImpl.java:createCartModel:~298-306`
**Discovery Method:** Direct Source Read
**Statement:** A cart can be anonymous (session-only) or owned by a signed-in shopper. An anonymous cart has no owner; once a shopper is known, the cart carries that shopper's identity so it can be retrieved on their next visit.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
// ShoppingCart.customerId nullable=true (indexed)
createCartModel(...): IF customer != null: cart.customerId = customer.id
```
**Data Dependencies:**
- Reads: (request) customer id
- Writes: shopping_cart.customer_id
**Side Effects:** INSERT/UPDATE `shopping_cart.customer_id`.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (anonymous → owned) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts {"storeId":1,"customerId":"cust-42"}`
- Success: `201 {"code":"...","customerId":"cust-42"}`
- Error Input: `POST /api/v1/carts {"storeId":1,"customerId":"not-a-customer"}` (referential — validated by caller)
- Error Output: `201` (legacy does not validate customer existence here; ownership is set as supplied)

---

### BR-CART-005: Retrieve the single active cart for a shopper

**Source Reference:** `ShoppingCartServiceImpl.java:getByCustomer:~200-213`; `ShoppingCartDaoImpl.java:getByCustomer:~128-147`
**Discovery Method:** Direct Source Read
**Statement:** A shopper has at most one active cart. When a shopper's cart is requested, the system returns their cart if one exists and nothing otherwise; if more than one is found it returns one of them rather than failing.
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
getByCustomer(customer):
    results = query.where(customerId == customer.id).list()
    IF results.isEmpty(): return null
    ELSE return results.get(0)   // >1 tolerated — silently returns first
```
**Data Dependencies:**
- Reads: shopping_cart.customer_id
**Side Effects:** None (read).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Note (modernization):** legacy returns `results.get(0)` when >1 row exists despite the token unique index. Target SHOULD enforce one active cart per (store, customer) — see INV-CART-005.

**Concrete Example:**
- Input: `GET /api/v1/carts?customerId=cust-42` (`x-store-id: 1`)
- Success: `200 {"code":"...","customerId":"cust-42","items":[...]}`
- Error Input: `GET /api/v1/carts?customerId=cust-999` (no cart)
- Error Output: `404 {"error":"NotFound","message":"No cart for this shopper"}`

---

### BR-CART-006: A new line item defaults to a quantity of one

**Source Reference:** `ShoppingCartItem.java:quantity:52`; `ShoppingCartItem.java:ShoppingCartItem:~81-96`; `ShoppingCartServiceImpl.java:populateShoppingCartItem:~245-272`
**Discovery Method:** Direct Source Read
**Statement:** When a line item is first created it holds a quantity of one until the requested quantity is applied. A line item never starts empty.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
// ShoppingCartItem.quantity initialized to 1 in field + all constructors
item = new ShoppingCartItem(product)   // quantity == 1
item.quantity = requestedQuantity      // overwritten by caller
```
**Data Dependencies:**
- Writes: shopping_cart_item.quantity
**Side Effects:** None (in-memory default).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (default 1) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {"productId":"prod-10"}` (quantity omitted)
- Success: `201 {"items":[{"productId":"prod-10","quantity":1}]}`
- Error Input: `POST /api/v1/carts/{code}/items {}` (no product)
- Error Output: `422 {"error":"Unprocessable","message":"productId is required"}`

---

### BR-CART-007: Adding an item requires the product to exist

**Source Reference:** `ShoppingCartFacadeImpl.java:createCartItem:~157-166`; `ShoppingCartServiceImpl.java:getShoppingCartItems:~404-411`; `ShoppingCartModelPopulator.java:createCartItem:~232-238`
**Discovery Method:** Direct Source Read
**Statement:** An item can only be added to a cart if it refers to a product that actually exists in the catalog. A request for a non-existent product is rejected and nothing is added.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
product = productService.getById(item.productId)   // CROSS-SERVICE read → MS-04 catalog
IF product == null: throw "Item with id " + productId + " does not exist"
```
**Data Dependencies:**
- Reads: product (via catalog service, MS-04) — id only
**Side Effects:** None; throws and aborts the add.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-04 product lookup) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {"productId":"prod-10","quantity":1}`
- Success: `201 {"items":[{"productId":"prod-10","quantity":1}]}`
- Error Input: `POST /api/v1/carts/{code}/items {"productId":"prod-does-not-exist","quantity":1}`
- Error Output: `422 {"error":"Unprocessable","message":"Item with id prod-does-not-exist does not exist"}`

---

### BR-CART-008: An item must belong to the cart's store

**Source Reference:** `ShoppingCartFacadeImpl.java:createCartItem:~168-172`; `ShoppingCartServiceImpl.java:getShoppingCartItems:~412-417`; `ShoppingCartModelPopulator.java:createCartItem:~240-244`
**Discovery Method:** Direct Source Read
**Statement:** A product can only be added to a cart when that product is sold by the same store the cart belongs to. Cross-store items are rejected.
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
IF product.merchantStore.id != store.id:   // product.store from MS-04
    throw "Item with id " + productId + " does not belong to merchant " + store.id
```
**Data Dependencies:**
- Reads: product.store (via catalog, MS-04), shopping_cart.merchant_id
**Side Effects:** None; throws and aborts the add.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-04 product/store) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {"productId":"prod-store1","quantity":1}` (cart in store 1)
- Success: `201 {"items":[...]}`
- Error Input: same call where `prod-store1` actually belongs to store 2
- Error Output: `422 {"error":"Unprocessable","message":"Item does not belong to this store"}`

---

### BR-CART-009: Line item captures a unit-price snapshot when added

**Source Reference:** `ShoppingCartServiceImpl.java:populateShoppingCartItem:~245-272`; `ShoppingCartItem.java:itemPrice:66`
**Discovery Method:** Direct Source Read
**Statement:** When an item is added, its unit price is captured from the catalog's current final price (inclusive of any rebates) and stored on the line. The line also records whether the product is virtual (non-shippable digital good).
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
item = new ShoppingCartItem(product)
item.productVirtual = product.isProductVirtual()
FinalPrice price = pricingService.calculateProductPrice(product)   // CROSS-SERVICE → MS-04 pricing
item.itemPrice = price.getFinalPrice()                             // final price incl. rebates
```
**Data Dependencies:**
- Reads: product, product final price (via MS-04 pricing)
- Writes: shopping_cart_item.item_price (transient snapshot persisted on save), shopping_cart_item.product_virtual (transient)
**Side Effects:** None directly (sets line fields; persisted on cart save).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (MS-04 pricing) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {"productId":"prod-10","quantity":2}` (catalog final price 12.50)
- Success: `201 {"items":[{"productId":"prod-10","quantity":2,"unitPrice":12.50,"subTotal":25.00}]}`
- Error Input: pricing service unavailable
- Error Output: `502 {"error":"BadGateway","message":"Unable to price item"}`

---

### BR-CART-010: Selected attributes must belong to the product; others are ignored

**Source Reference:** `ShoppingCartFacadeImpl.java:createCartItem:~176-192`; `ShoppingCartAttributeItem.java:ShoppingCartAttributeItem:~52-60`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper selects product options for a line item, each selected option is bound to the line only if it is a valid option of that product. Selections that do not belong to the product are silently ignored rather than rejecting the whole add.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
FOR attribute IN item.shoppingCartAttributes:
    productAttribute = productAttributeService.getById(attribute.attributeId)   // MS-04
    IF productAttribute != null AND productAttribute.product.id == product.id:
        item.addAttributes(new ShoppingCartAttributeItem(item, productAttribute))
    // attributes not belonging to the product are skipped
```
**Data Dependencies:**
- Reads: product_attribute (via MS-04), product id
- Writes: shopping_cart_attribute_item (on save)
**Side Effects:** INSERT rows into `shopping_cart_attribute_item` on cart save.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (MS-04 attribute) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {"productId":"prod-10","quantity":1,"attributes":[{"attributeId":"attr-5"}]}` (attr-5 belongs to prod-10)
- Success: `201 {"items":[{"productId":"prod-10","attributes":[{"attributeId":"attr-5"}]}]}`
- Error Input: attributes:[{"attributeId":"attr-999"}] (belongs to a different product)
- Error Output: `201 {"items":[{"productId":"prod-10","attributes":[]}]}` (invalid attribute silently dropped)

---

### BR-CART-011: Adding a duplicate plain item increments its quantity

**Source Reference:** `ShoppingCartFacadeImpl.java:addItemsToShoppingCart:~119-140`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper adds a product that already sits in the cart as a plain line (no options selected on either side), the existing line's quantity is increased instead of creating a second line. Items with selected options are always added as new lines. A virtual product that matches an existing plain line is neither merged nor re-added.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
duplicateFound = false
IF item.shoppingCartAttributes is empty:                 // only merge plain items
   FOR cartItem IN cartModel.lineItems:
      IF cartItem.product.id == newItem.product.id AND cartItem.attributes is empty:
         IF NOT duplicateFound:
            IF NOT newItem.isProductVirtual():
                cartItem.quantity = cartItem.quantity + newItem.quantity   // increment
            duplicateFound = true; break
IF NOT duplicateFound:
    cartModel.lineItems.add(newItem)                     // otherwise add as a new line
```
**Data Dependencies:**
- Reads: shopping_cart_item.product_id, shopping_cart_item.quantity, product_virtual
- Writes: shopping_cart_item.quantity (increment) or INSERT new line
**Side Effects:** UPDATE existing line quantity, or INSERT new line, on save.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 3 | 3 | OK (increment / new line / virtual-suppressed) |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

> **Net-new finding (defect flag):** a matching **virtual** product marks `duplicateFound=true` but never increments (`ShoppingCartFacadeImpl.java:~131-133`) — the add is silently a no-op. Carried to Human Clarification; target behavior TBD by BA.

**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {"productId":"prod-10","quantity":1}` when prod-10 (no attributes) already has quantity 2
- Success: `200 {"items":[{"productId":"prod-10","quantity":3}]}` (incremented, not duplicated)
- Error Input: adding a matching **virtual** product already in the cart
- Error Output: `200 {"items":[{"productId":"prod-virtual","quantity":1}]}` (quantity unchanged — flagged no-op)

---

### BR-CART-012: Persisting a cart decides insert vs update by identity

**Source Reference:** `ShoppingCartServiceImpl.java:saveOrUpdate:~88-96`
**Discovery Method:** Direct Source Read
**Statement:** Saving a cart creates a new record when the cart has never been persisted, and updates the existing record otherwise. The whole cart aggregate (its lines and their selected options) is persisted together.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
saveOrUpdate(cart):
    IF cart.id == null OR cart.id == 0: create(cart)   // INSERT
    ELSE: update(cart)                                 // UPDATE (cascades lines + attributes)
```
**Data Dependencies:**
- Writes: shopping_cart (+ cascade shopping_cart_item, shopping_cart_attribute_item)
**Side Effects:** INSERT or UPDATE the cart aggregate.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/carts/{code}/items {...}` on an existing cart
- Success: `200` (UPDATE path — existing cart retained)
- Error Input: `POST /api/v1/carts/{code}/items` on a code that never existed
- Error Output: `404 {"error":"NotFound","message":"Cart not found"}`

---

### BR-CART-013: Line subtotal preview equals unit price times quantity

**Source Reference:** `ShoppingCartServiceImpl.java:populateItem:~313-316`; `ShoppingCartItem.java:subTotal:69`
**Discovery Method:** Direct Source Read
**Statement:** Each line item shows a subtotal preview equal to its captured unit price multiplied by its quantity. This is a display-side preview only; the authoritative order total is produced by the order service.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
lineSubTotal(item) = item.itemPrice.multiply(BigDecimal(item.quantity))   // item.itemPrice from MS-04 pricing
item.subTotal = lineSubTotal
```
**Data Dependencies:**
- Reads: shopping_cart_item.item_price, shopping_cart_item.quantity
- Writes: shopping_cart_item.sub_total (transient preview)
**Side Effects:** None (transient preview field).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/carts/{code}` with a line unit price 12.50, quantity 2
- Success: `200 {"items":[{"unitPrice":12.50,"quantity":2,"subTotal":25.00}]}`
- Error Input: (n/a — pure derivation)
- Error Output: (n/a)

---

### BR-CART-014: Authoritative cart total is delegated to the order service (BV-3)

**Source Reference:** `ShoppingCartCalculationServiceImpl.java:calculate:~62-108`; `ShoppingCartFacadeImpl.java:addItemsToShoppingCart:~148-150`
**Discovery Method:** Direct Source Read
**Statement:** The cart's authoritative money total — the subtotal roll-up plus tax, shipping and promotions — is computed by the order-total service, not by the cart. The cart supplies its lines and store/shopper context and receives back a complete total summary. Tax, shipping and promotion logic are never owned by the cart.
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
calculate(cart, [customer,] store, language):
    Validate.notNull(cart); Validate.notNull(cart.lineItems); Validate.notNull(store)
    summary = orderService.calculateShoppingCartTotal(cart, [customer,] store, language)  // CROSS-SERVICE → MS-09
    updateCartModel(cart)   // re-persist (see BR-CART-016)
    return summary          // subtotal, grand total, per-code totals (shipping/tax/promo)
```
**Data Dependencies:**
- Reads: whole cart aggregate (lines + line prices)
- External: order-total service (MS-09) — returns OrderTotalSummary
**Side Effects:** Cross-service call to MS-09; cart re-persisted (BR-CART-016).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (MS-09 total — single source of truth) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/carts/{code}/summary` (`x-store-id: 1`)
- Success: `200 {"subTotal":"$25.00","total":"$30.50","totals":[{"code":"subtotal","value":25.00},{"code":"shipping","value":5.50}]}`
- Error Input: order service unavailable
- Error Output: `502 {"error":"BadGateway","message":"Unable to compute cart total"}`

---

### BR-CART-015: Cart item-count roll-up for display

**Source Reference:** `ShoppingCartDataPopulator.java:populate:~82-136`
**Discovery Method:** Direct Source Read
**Statement:** The cart view reports a total item count equal to the sum of the quantities of all its lines, along with the display-formatted subtotal and total obtained from the order service. This roll-up is presentation data only.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
cartQuantity = Σ over line items of item.quantity            // count roll-up
cart.subTotal = displayAmount(orderSummary.subTotal, store)  // from MS-09 summary
cart.total    = displayAmount(orderSummary.total, store)     // from MS-09 summary
cart.totals   = [ {code, value} for each orderSummary.totals ]
cart.quantity = cartQuantity
```
**Data Dependencies:**
- Reads: shopping_cart_item.quantity; OrderTotalSummary (from MS-09)
**Side Effects:** None (builds the cart view DTO).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-09 summary) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/carts/{code}` with two lines quantity 2 and 3
- Success: `200 {"quantity":5,"subTotal":"$62.50","total":"$68.00"}`
- Error Input: order-summary call fails during populate
- Error Output: `502 {"error":"BadGateway","message":"Unable to build cart view"}`

---

### BR-CART-016: Every mutation recalculates and re-persists the cart

**Source Reference:** `ShoppingCartCalculationServiceImpl.java:calculate:~62-70`; `ShoppingCartCalculationServiceImpl.java:updateCartModel:~120-123`; `ShoppingCartFacadeImpl.java:addItemsToShoppingCart:~144-150`
**Discovery Method:** Direct Source Read
**Statement:** After any change to a cart (add, update, remove), the cart is recalculated through the order service and then re-persisted so its stored state reflects the change. Recalculation and persistence always happen together.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
onMutation(cart, store, language):
    saveOrUpdate(cart)                                   // persist the structural change
    cart = getById(cart.id, store)                       // re-read (triggers obsolete sweep, BR-CART-021)
    summary = calculate(cart, store, language)           // → MS-09 (BR-CART-014)
    updateCartModel(cart) → saveOrUpdate(cart)           // re-persist recomputed state
```
**Data Dependencies:**
- Writes: shopping_cart (+ items)
- External: MS-09 (via calculate)
**Side Effects:** UPDATE `shopping_cart` on every recalculation.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (MS-09) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `PATCH /api/v1/carts/{code}/items/{itemId} {"quantity":4}`
- Success: `200 {"items":[{"id":"{itemId}","quantity":4,"subTotal":50.00}],"total":"$55.50"}` (recomputed + persisted)
- Error Input: recalculation fails after the structural save
- Error Output: `502 {"error":"BadGateway","message":"Cart saved but total could not be recomputed"}`

---

### BR-CART-017: Updating a line quantity requires at least one

**Source Reference:** `ShoppingCartFacadeImpl.java:updateCartItem:~322-325`; `ShoppingCartFacadeImpl.java:updateCartItems:~360-364`; `CartModificationException.java`
**Discovery Method:** Direct Source Read
**Statement:** A line item's quantity can never be set below one. Any update — single-item or batch — requesting a quantity of zero or less is rejected. To remove a line the shopper must delete it, not set its quantity to zero.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
// single: IF newQuantity < 1: throw CartModificationException("Quantity must not be less than one")
// batch:  IF item.getQuantity() < 1: throw CartModificationException("Quantity must not be less than one")
```
**Data Dependencies:**
- Reads: (request) quantity
**Side Effects:** Throws `CartModificationException`; aborts the update.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (minimum 1) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Net-new finding (asymmetry):** the minimum-quantity guard exists only on the update paths, NOT on add (BR-CART-011 accepts the item's quantity as-is). Flagged for Human Clarification.

**Concrete Example:**
- Input: `PATCH /api/v1/carts/{code}/items/{itemId} {"quantity":3}`
- Success: `200 {"items":[{"id":"{itemId}","quantity":3}]}`
- Error Input: `PATCH /api/v1/carts/{code}/items/{itemId} {"quantity":0}`
- Error Output: `422 {"error":"Unprocessable","message":"Quantity must not be less than one"}`

---

### BR-CART-018: Updating a line rejects an unknown entry and re-prices it

**Source Reference:** `ShoppingCartFacadeImpl.java:updateCartItem:~326-348`; `ShoppingCartFacadeImpl.java:getEntryToUpdate:~231-248`
**Discovery Method:** Direct Source Read
**Statement:** A quantity update must target a line that actually exists in the cart; an update to an unknown line is rejected. On a valid update the line is re-priced against the product's current price, so an updated line reflects present pricing rather than the price captured when it was first added.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
entryToUpdate = getEntryToUpdate(itemId, cartModel)   // linear scan by line id
IF entryToUpdate == null: throw CartModificationException("Unknown entry number.")
entryToUpdate.quantity = newQuantity
finalPrice = productPriceUtils.getFinalProductPrice(entry.product, entry.product.attributes)  // reprice, MS-04
entryToUpdate.itemPrice = finalPrice.getFinalPrice()
shoppingCartService.saveOrUpdate(cartModel)
```
**Data Dependencies:**
- Reads: shopping_cart_item (by id), product current price (via MS-04)
- Writes: shopping_cart_item.quantity, shopping_cart_item.item_price
**Side Effects:** UPDATE `shopping_cart_item`; throws on unknown entry.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (MS-04 reprice) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `PATCH /api/v1/carts/{code}/items/{knownItemId} {"quantity":2}`
- Success: `200 {"items":[{"id":"{knownItemId}","quantity":2,"unitPrice":13.00}]}` (repriced to current 13.00)
- Error Input: `PATCH /api/v1/carts/{code}/items/unknown-line {"quantity":2}`
- Error Output: `422 {"error":"Unprocessable","message":"Unknown entry number."}`

---

### BR-CART-019: Removing a line item drops it from the cart

**Source Reference:** `ShoppingCartFacadeImpl.java:removeCartItem:~299-330`
**Discovery Method:** Direct Source Read
**Statement:** Removing a line item rebuilds the cart's line set to exclude that line and persists the change; the removed line and its selected options are deleted. Lines other than the target are unaffected.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
cartModel = getByCode(cartId, store)
newSet = { i IN cartModel.lineItems : i.id != itemID }   // exclude the target
cartModel.setLineItems(newSet)
shoppingCartService.saveOrUpdate(cartModel)              // orphanRemoval deletes the dropped row(s)
```
**Data Dependencies:**
- Writes: shopping_cart_item (delete via orphan removal), shopping_cart_attribute_item (cascade)
**Side Effects:** DELETE the removed `shopping_cart_item` (+ its attribute items) on save.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `DELETE /api/v1/carts/{code}/items/{itemId}`
- Success: `200 {"items":[/* remaining lines */],"quantity":1}`
- Error Input: `DELETE /api/v1/carts/{code}/items/not-in-cart`
- Error Output: `200 {"items":[/* unchanged */]}` (legacy no-op when line id not present)

---

### BR-CART-020: The cart is deleted when its last item is removed

**Source Reference:** `ShoppingCartController.java:removeShoppingCartItem:~370-374`; `MiniCartController.java:removeShoppingCartItem:~74-82`
**Discovery Method:** Direct Source Read
**Statement:** When removing an item empties the cart, the cart itself is deleted and its session reference cleared. An empty cart is never left behind.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
data = removeCartItem(...)
IF data.shoppingCartItems is empty:
    deleteShoppingCart(data.id, store)          // hard delete cart
    (mini-cart) session.removeAttribute(SHOPPING_CART)
    redirect /shop
```
**Data Dependencies:**
- Writes: shopping_cart (delete)
**Side Effects:** DELETE `shopping_cart`; clears the client's cart reference.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (Active → Deleted) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `DELETE /api/v1/carts/{code}/items/{lastItemId}` (cart's only line)
- Success: `204` (cart deleted, no body) or `200 {"items":[],"deleted":true}`
- Error Input: `DELETE /api/v1/carts/{code}/items/{itemId}` where other lines remain
- Error Output: `200 {"items":[/* remaining */],"deleted":false}` (cart retained)

---

### BR-CART-021: An obsolete cart is cleaned up on read

**Source Reference:** `ShoppingCartServiceImpl.java:populateShoppingCart:~218-270`; `ShoppingCartServiceImpl.java:populateItem:~276-311`; `ShoppingCartServiceImpl.java:getByCode:~157-192`
**Discovery Method:** Direct Source Read
**Statement:** Whenever a cart is read, lines whose product no longer exists are treated as obsolete and dropped, and if that leaves the cart empty the whole cart is considered obsolete and deleted. There is no time-based expiry — a cart becomes obsolete only when it is empty or all its products have been removed from the catalog, and it is cleaned up lazily on the next read.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
populateItem(item): product = productService.getById(item.productId)   // MS-04
                    IF product == null: item.obsolete = true; return
populateShoppingCart(cart):
    IF cart.lineItems empty: cart.obsolete = true; return
    FOR item IN items: populateItem(item); IF !item.obsolete: cartIsObsolete = false
    refreshedItems = { item : !item.obsolete }
    IF any obsolete: cart.setLineItems(refreshedItems); update(cart)   // drop obsolete lines
    IF all items obsolete: cart.obsolete = true
getBy*(...): populate; IF cart.isObsolete(): delete(cart); return null
```
**Data Dependencies:**
- Reads: product existence (MS-04)
- Writes: shopping_cart (drop lines / delete)
**Side Effects:** UPDATE cart (drop obsolete lines) and/or DELETE `shopping_cart`.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 2 | 2 | OK (Active → line-dropped → Obsolete/Deleted) |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (MS-04 existence) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Net-new finding:** the `obsolete` flag is transient (recomputed each read, never persisted). There is NO abandoned-cart TTL anywhere in this segment. Carried to Human Clarification (is a scheduled abandoned-cart sweep expected elsewhere?).

**Concrete Example:**
- Input: `GET /api/v1/carts/{code}` where the cart's only product was deleted from the catalog
- Success: `404 {"error":"NotFound","message":"Cart no longer available"}` (obsolete → deleted on read)
- Error Input: `GET /api/v1/carts/{code}` with a mix of valid + deleted-product lines
- Error Output: `200 {"items":[/* only valid lines; obsolete dropped */]}`

---

### BR-CART-022: Merge an anonymous cart into the shopper's cart on login

**Source Reference:** `ShoppingCartServiceImpl.java:mergeShoppingCarts:~354-399`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper signs in, the items from their anonymous session cart are merged into their saved cart. If a session cart already belongs to the same signed-in shopper and both carts hold items, the saved cart is kept as-is. Otherwise each session line is added to the saved cart — increasing quantity where the same product already matches, or added as a new line. After the merge the saved cart is persisted and the session cart is discarded. This is triggered by the customer login flow (MS-05); the cart owns the merge mechanics.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
mergeShoppingCarts(userCart, sessionCart, store):
    IF sessionCart.customerId != null AND sessionCart.customerId == userCart.customerId:
        IF userCart.lineItems non-empty AND sessionCart.lineItems non-empty: return userCart   // short-circuit
    IF sessionCart.lineItems non-empty:
        sessionItems = getShoppingCartItems(sessionCart, store, userCart)   // re-hydrate + re-price + guard (BR-CART-023)
        duplicateFound = false
        FOR sItem IN sessionItems:
           FOR uItem IN userCart.lineItems:
              IF uItem.product.id == sItem.product.id:
                 IF uItem.attributes non-empty AND NOT duplicateFound:
                    uItem.quantity += sItem.quantity; duplicateFound = true; break
           IF NOT duplicateFound: userCart.lineItems.add(sItem)
    saveOrUpdate(userCart)
    removeShoppingCart(sessionCart)   // session cart destroyed
    return userCart
```
**Data Dependencies:**
- Reads: session + user cart lines, product (MS-04)
- Writes: shopping_cart (merged user cart), shopping_cart (delete session cart)
- External: caller MS-05 (login flow)
**Side Effects:** UPDATE user cart, DELETE session cart.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 2 | 2 | OK (session → merged; session → deleted) |
| Outcomes | 3 | 3 | OK (kept / merged-increment / merged-new-line) |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK (MS-05 caller / MS-04 read) |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Net-new finding (inconsistency):** the merge increments quantity only when the **user** item HAS attributes (`:~378`), whereas add-to-cart merges only when the item has NO attributes (BR-CART-011). The two conditions are inverted. Flagged for Human Clarification.

**Concrete Example:**
- Input: `POST /api/v1/carts/merge {"userCartCode":"userAAA","sessionCartCode":"sessBBB"}` (`x-store-id: 1`) — triggered by MS-05 login
- Success: `200 {"code":"userAAA","items":[/* union of both carts */]}`
- Error Input: `POST /api/v1/carts/merge {"userCartCode":"userAAA","sessionCartCode":"belongs-to-store-2"}`
- Error Output: `422 {"error":"Unprocessable","message":"Session item does not belong to this store"}`

---

### BR-CART-023: Session items are re-validated and re-priced during merge

**Source Reference:** `ShoppingCartServiceImpl.java:getShoppingCartItems:~402-451`
**Discovery Method:** Direct Source Read
**Statement:** While merging, every session line is rebuilt from scratch: its product must still exist and belong to the store, it is re-priced from the catalog, and only its options that genuinely belong to the product are kept. A session line whose product is missing or belongs to another store aborts the merge.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
FOR sItem IN sessionCart.lineItems:
    product = productService.getById(sItem.productId)   // MS-04
    IF product == null: throw "Item with id ... does not exist"
    IF product.merchantStore.id != store.id: throw "... does not belong to merchant ..."
    item = populateShoppingCartItem(product)            // re-price (MS-04)
    item.quantity = sItem.quantity; item.shoppingCart = userCart
    FOR attr IN sItem.attributes:
        productAttribute = productAttributeService.getById(attr.id)   // NOTE: passes cart-attr-item id
        IF productAttribute != null AND productAttribute.product.id == product.id:
            add ShoppingCartAttributeItem(item, productAttribute)
```
**Data Dependencies:**
- Reads: product, product_attribute (MS-04)
- Writes: builds new persistent lines for the user cart
**Side Effects:** New line items constructed; throws on invalid product.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (MS-04 product/attribute) |
| Error paths | 2 | 2 | OK |
**Preservation:** OK

> **Net-new finding (potential lookup bug):** `productAttributeService.getById(shoppingCartAttributeItem.getId())` (`:~429`) passes the cart-attribute-item id where a product-attribute id is expected — likely silently drops attributes on merge. Flagged for Human Clarification.

**Concrete Example:**
- Input: (internal to BR-CART-022 merge) session line for prod-10 in store 1
- Success: rebuilt line `{"productId":"prod-10","quantity":2,"unitPrice":13.00}` added to user cart
- Error Input: session line references a product deleted from the catalog
- Error Output: `422 {"error":"Unprocessable","message":"Item with id prod-10 does not exist"}`

---

### BR-CART-024: Cart shipping-eligibility and free-cart derivations

**Source Reference:** `ShoppingCartServiceImpl.java:requiresShipping:~335-351`; `ShoppingCartServiceImpl.java:isFreeShoppingCart:~318-333`; `ShoppingCartServiceImpl.java:createShippingProduct:~298-318`
**Discovery Method:** Direct Source Read
**Statement:** From a cart's lines the system derives three checkout-facing facts: whether the cart requires shipping (any line's product is shippable), whether the cart is entirely free (every line prices at zero or less), and the set of shippable physical products with their quantities. These feed the checkout/shipping flow; they are derivations, not stored state.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
requiresShipping(cart)  = ∃ item : item.product.isProductShipeable()
isFreeShoppingCart(cart)= ∀ item : pricingService.calculateProductPrice(product).finalPrice <= 0   // MS-04
createShippingProduct(cart) = [ ShippingProduct(product, item.quantity)
                                for item where !product.isProductVirtual() AND product.isProductShipeable() ]
```
**Data Dependencies:**
- Reads: product flags (virtual, shippable), product price (MS-04)
**Side Effects:** None (derivations feeding checkout/shipping).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (free threshold 0) |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (MS-04 pricing/flags) |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/carts/{code}/shipping-eligibility`
- Success: `200 {"requiresShipping":true,"freeCart":false,"shippableItems":[{"productId":"prod-10","quantity":2}]}`
- Error Input: `GET /api/v1/carts/unknown/shipping-eligibility`
- Error Output: `404 {"error":"NotFound","message":"Cart not found"}`

---

## BR-ID Coverage Note

All 24 rules map to the Phase-1 catalog BR-CART-001..024 (contiguous). Deep source read confirmed each as a distinct decision point (no merges/splits were warranted); it added **6 net-new findings** documented inline as `> Net-new finding` notes: the virtual-product add no-op (BR-CART-011), the add-vs-update quantity-minimum asymmetry (BR-CART-017), the absence of any abandoned-cart TTL (BR-CART-021), the inverted merge-duplicate condition vs add (BR-CART-022), the cart-attribute-item-id lookup bug on merge (BR-CART-023), and the tolerate-duplicate first-row selection (BR-CART-005). No genuinely-greenfield rules were introduced.
