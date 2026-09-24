# MS-04 Catalog Service — Business Rules

**Service ID:** MS-04
**Service:** catalog
**Source stack:** Java / Spring MVC / JPA-Hibernate + QueryDSL (Shopizer 2.0.1)
**Extraction mode:** Direct Source Read (Phase 4 deep pass; Phase 1 segment summaries used as file-targeting index)

> Rule groups (Phase-1 group codes preserved): CATPROD (product aggregate/lifecycle),
> CATCAT (category taxonomy), CATMAN (manufacturer/brand), CATOPT (options/values/attributes),
> CATPRICE (pricing engine), CATIMG (images/media), CATREV (reviews).
>
> **D-06 preservation notice:** dead-code / behavioral quirks in the pricing basis and product-price
> selection logic are PRESERVED as-is and flagged, NOT corrected. See BR-CATPRICE-003, -008, -009/-010,
> -011 and the "Preserved quirks" annotations. The same applies to legacy comparison/case-mismatch
> quirks elsewhere (BR-CATOPT-017, BR-CATOPT-021, ownership `!=` comparisons).

Statement fields are semantic (target-domain terms). Legacy table/column/method names appear ONLY in the
Logic and Source Reference fields (traceability), never in the Statement.

---

## BR-CATPROD — Product aggregate & lifecycle (26 rules)

### BR-CATPROD-001: Product save routes to create or update based on identity
**Source Reference:** `ProductServiceImpl.java:saveOrUpdate:241-393`
**Discovery Method:** Direct Source Read
**Statement:** Saving a product is a single aggregate operation: a product that has never been persisted is created (parent first, then its children), while an existing product is updated and its child collections are reconciled against what was previously stored.
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```
if product.id is present and > 0:
    original = load(product.id)          # capture existing child collections for reconciliation
    reconcile children against original (see BR-CATPROD-004), then update(product)
else:
    detach descriptions; create(product) to obtain generated id; re-add each description
always: persist availabilities/attributes/relationships/images; reindex in search
```

**Data Dependencies:**
- Reads: `PRODUCT.id`, child collections (availabilities, attributes, relationships, images, descriptions)
- Writes: `PRODUCT`, `PRODUCT_DESCRIPTION`, `PRODUCT_AVAILABILITY`, `PRODUCT_ATTRIBUTE`, `PRODUCT_RELATIONSHIP`, `PRODUCT_IMAGE`

**Side Effects:**
- Publishes: search index write (`catalog.product.indexed`)
- Calls: availability/attribute/relationship/image sub-services

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 5 | OK |
| Data-flow | 6 | 6 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 6 | 6 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"WIDGET_01","typeCode":"GENERAL","available":true,"availabilities":[{"region":"*","quantity":10}],"descriptions":[{"languageCode":"en","name":"Widget"}]}`
- Success Output: `201 {"id":"5001","sku":"WIDGET_01","available":true,"availabilities":[{"id":"9001","region":"*","quantity":10}]}`
- Error Input: `POST /api/v1/catalog/products {"sku":"WIDGET_01","availabilities":[]}`
- Error Output: `422 {"error":"ValidationError","message":"A product must have at least one availability","statusCode":422}`

### BR-CATPROD-002: A product must have at least one availability to be saved
**Source Reference:** `ProductServiceImpl.java:saveOrUpdate:245-246`
**Discovery Method:** Direct Source Read
**Statement:** A product cannot be persisted unless it has at least one availability record; a product with no availability is rejected before any data is written.
**Intent:** Validation
**Weight:** Medium
**Logic:** `Validate.notNull(product.availabilities); Validate.notEmpty(product.availabilities)` → throws `IllegalArgumentException` when missing/empty; nothing is written.
**Data Dependencies:**
- Reads: product availability collection
- Writes: none (rejects before write)
**Side Effects:** none

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

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"NOAVAIL","availabilities":[]}`
- Success Output: (n/a — this rule only rejects)
- Error Input: same as input
- Error Output: `422 {"error":"ValidationError","message":"A product must have at least one availability","statusCode":422}`

### BR-CATPROD-003: New product descriptions are persisted after the parent to obtain the foreign key
**Source Reference:** `ProductServiceImpl.java:saveOrUpdate:268-278`
**Discovery Method:** Direct Source Read
**Statement:** When creating a new product, the product record is persisted first so it receives an identity, and only then are its localized descriptions attached and stored — each description is linked back to the product it belongs to.
**Intent:** State Transition
**Weight:** Medium
**Logic:** For a new product, temporarily detach descriptions, create the product to obtain the generated id, then add each description with its product back-link set.
**Data Dependencies:**
- Reads: product identity after insert
- Writes: `PRODUCT`, `PRODUCT_DESCRIPTION`
**Side Effects:** Calls: search index (per description add, BR-CATPROD-011/012)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"NEW_1","descriptions":[{"languageCode":"en","name":"New"}],"availabilities":[{"region":"*"}]}`
- Success Output: `201 {"id":"6002","descriptions":[{"id":"7003","languageCode":"en","name":"New"}]}`
- Error Input: `POST /api/v1/catalog/products {"descriptions":[{"name":""}],"availabilities":[{"region":"*"}]}`
- Error Output: `422 {"error":"ValidationError","message":"Description name is required","statusCode":422}`

### BR-CATPROD-004: Child collections are reconciled by identity difference on update
**Source Reference:** `ProductServiceImpl.java:saveOrUpdate:282-388`
**Discovery Method:** Direct Source Read
**Statement:** On update, each child collection of a product (availabilities, attributes, relationships, images) is reconciled: children present on the stored product but absent from the submitted set are removed, while submitted children are inserted or updated.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```
newIds = { child.id for child in submitted children after save }
for orig in original children:
    if orig.id not in newIds: delete(orig)
applied independently per collection: availabilities, attributes, relationships, images
```
**Data Dependencies:**
- Reads: original child ids, submitted child ids
- Writes: `PRODUCT_AVAILABILITY`, `PRODUCT_ATTRIBUTE`, `PRODUCT_RELATIONSHIP`, `PRODUCT_IMAGE`
**Side Effects:** DELETE of orphaned children; INSERT/UPDATE of retained children

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 8 | 6 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 4 | 4 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/products/5001 {"availabilities":[{"id":"9001","quantity":5}]}` (product previously had availabilities 9001 and 9002)
- Success Output: `200 {"id":"5001","availabilities":[{"id":"9001","quantity":5}]}` (9002 removed)
- Error Input: `PUT /api/v1/catalog/products/5001 {"availabilities":[]}`
- Error Output: `422 {"error":"ValidationError","message":"A product must have at least one availability","statusCode":422}`

### BR-CATPROD-005: An image is added when it carries data and has no identity, otherwise updated
**Source Reference:** `ProductServiceImpl.java:saveOrUpdate:359-374`
**Discovery Method:** Direct Source Read
**Statement:** During a product save, an image that carries binary content and has no existing identity is treated as a new upload and stored (metadata plus file), while an image that already has an identity is updated in place.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if image has content and (image.id is null or 0)` build a product-content file and add it; else update the image metadata.
**Data Dependencies:**
- Reads: image content, image.id
- Writes: `PRODUCT_IMAGE`
**Side Effects:** Calls: CMS content store (binary write) for new images

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/images {"defaultImage":true,"content":"<base64>"}`
- Success Output: `201 {"id":"8100","defaultImage":true}`
- Error Input: `POST /api/v1/catalog/products/5001/images {"content":null}`
- Error Output: `422 {"error":"ValidationError","message":"Image content is required","statusCode":422}`

### BR-CATPROD-006: Deleting a product cascades to its dependents and removes it from search
**Source Reference:** `ProductServiceImpl.java:delete:206-229`
**Discovery Method:** Direct Source Read
**Statement:** Deleting a product removes it together with its images, relationships, and availabilities, detaches it from all categories, and removes it from the search index — leaving no orphaned catalog data.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```
require product and its store not null; reload managed product
detach product from categories
remove each image (CMS + row); delete each relationship
delete product (availabilities cascade via orphan removal)
remove product from search index
```
**Data Dependencies:**
- Reads: product graph
- Writes: `PRODUCT`, `PRODUCT_IMAGE`, `PRODUCT_RELATIONSHIP`, `PRODUCT_AVAILABILITY`, `PRODUCT_CATEGORY`
**Side Effects:** Publishes: search index delete; Calls: CMS file removal

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 5 | 5 | OK |
| Integrations | 2 | 2 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/products/5001`
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/products/5001` (product has no owning store)
- Error Output: `422 {"error":"ValidationError","message":"Product store is required for deletion","statusCode":422}`

### BR-CATPROD-007: Deleting a product requires an owning store
**Source Reference:** `ProductServiceImpl.java:delete:208-209`
**Discovery Method:** Direct Source Read
**Statement:** A product deletion is rejected unless the product and its owning store are both present.
**Intent:** Validation
**Weight:** Medium
**Logic:** `Validate.notNull(product); Validate.notNull(product.merchantStore)` → reject if either is null.
**Data Dependencies:**
- Reads: product, product store
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/products/5001` (store missing)
- Success Output: (n/a)
- Error Input: same
- Error Output: `422 {"error":"ValidationError","message":"Product store is required for deletion","statusCode":422}`

### BR-CATPROD-008: Product SKU must be non-empty and alphanumeric with underscores
**Source Reference:** `Product.java:sku:146-149`
**Discovery Method:** Direct Source Read
**Statement:** Every product must carry a stock-keeping code that is not empty and contains only letters, digits, and underscores.
**Intent:** Validation
**Weight:** Medium
**Logic:** SKU is `@NotEmpty` and matches `^[a-zA-Z0-9_]*$`; a violation blocks the save.
**Data Dependencies:**
- Reads: submitted SKU
- Writes: `PRODUCT.SKU`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"ABC_123","availabilities":[{"region":"*"}]}`
- Success Output: `201 {"sku":"ABC_123"}`
- Error Input: `POST /api/v1/catalog/products {"sku":"ABC-123!","availabilities":[{"region":"*"}]}`
- Error Output: `422 {"error":"ValidationError","message":"SKU must contain only letters, digits, and underscores","statusCode":422}`

### BR-CATPROD-009: New product defaults (available, date-available now, sort order zero, physical/non-free)
**Source Reference:** `Product.java:98-135` (`available=true`, `dateAvailable=new Date()`, `sortOrder=0`, virtual/ship/free defaults)
**Discovery Method:** Direct Source Read
**Statement:** A newly created product defaults to available immediately (date-available set to the creation instant), sorts at position zero, and is treated as a physical, non-virtual, non-free product until stated otherwise.
**Intent:** Calculation
**Weight:** Medium
**Logic:** defaults: available=true; dateAvailable=creation instant; sortOrder=0; productVirtual=false; productShipeable=false; productIsFree=false.
**Data Dependencies:**
- Reads: none
- Writes: `PRODUCT.AVAILABLE`, `PRODUCT.DATE_AVAILABLE`, `PRODUCT.SORT_ORDER`, `PRODUCT.PRODUCT_VIRTUAL`, `PRODUCT.PRODUCT_SHIP`, `PRODUCT.PRODUCT_FREE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 6 | 6 | OK |
| Constants | 6 | 6 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 6 | 6 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"DEF_1","availabilities":[{"region":"*"}]}`
- Success Output: `201 {"sku":"DEF_1","available":true,"sortOrder":0,"virtual":false,"shippable":false,"free":false}`
- Error Input: (n/a — defaulting rule)
- Error Output: (n/a)

### BR-CATPROD-010: Storefront visibility requires available and a reached availability date
**Source Reference:** `ProductDaoImpl.java:getBySeUrl~66`, `getProductForLocale`, `getProductsListForLocale` (`p.available=true and p.dateAvailable<=:dt`)
**Discovery Method:** Direct Source Read
**Statement:** A product is visible on the storefront only when it is marked available and its availability date has been reached; products that are unavailable or dated in the future are hidden from public reads.
**Intent:** Validation
**Weight:** Medium
**Logic:** public/locale reads filter `available = true AND dateAvailable <= currentDate`.
**Data Dependencies:**
- Reads: `PRODUCT.AVAILABLE`, `PRODUCT.DATE_AVAILABLE`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/storefront/products/widget-01?languageCode=en`
- Success Output: `200 {"id":"5001","visible":true}`
- Error Input: `GET /api/v1/catalog/storefront/products/future-item?languageCode=en` (date-available in the future)
- Error Output: `404 {"error":"NotFound","message":"Product not found","statusCode":404}`

### BR-CATPROD-011: Product create, description-add, and save keep the search index consistent
**Source Reference:** `ProductServiceImpl.java:create:233-235`, `addProductDescription:83-95`, `saveOrUpdate:393`
**Discovery Method:** Direct Source Read
**Statement:** Whenever a product is created, gains a description, or is saved, it is re-indexed in search so catalog search results stay consistent with the current catalog state.
**Intent:** State Transition
**Weight:** Medium
**Logic:** after create/description-add/save, invoke search index for (store, product).
**Data Dependencies:**
- Reads: product graph
- Writes: none (search subsystem)
**Side Effects:** Publishes: `catalog.product.indexed`

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"IDX_1","availabilities":[{"region":"*"}]}`
- Success Output: `201 {"sku":"IDX_1"}` (search index updated asynchronously)
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPROD-012: Adding a description links it to the product and re-indexes
**Source Reference:** `ProductServiceImpl.java:addProductDescription:83-95`
**Discovery Method:** Direct Source Read
**Statement:** Adding a localized description to a product initializes the product's description set if needed, links the description back to the product, saves it, and re-indexes the product.
**Intent:** State Transition
**Weight:** Medium
**Logic:** if descriptions null → initialize; add description; set description.product; update(product); index.
**Data Dependencies:**
- Reads: product description set
- Writes: `PRODUCT_DESCRIPTION`
**Side Effects:** Publishes: search index write

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/descriptions {"languageCode":"fr","name":"Gadget"}`
- Success Output: `201 {"id":"7010","languageCode":"fr","name":"Gadget"}`
- Error Input: `POST /api/v1/catalog/products/5001/descriptions {"languageCode":"fr","name":""}`
- Error Output: `422 {"error":"ValidationError","message":"Description name is required","statusCode":422}`

### BR-CATPROD-013: A locale-scoped product read is trimmed to the requested region and language
**Source Reference:** `ProductServiceImpl.java:getProductForLocale:140-149` (CatalogServiceHelper.setToAvailability/setToLanguage)
**Discovery Method:** Direct Source Read
**Statement:** When a product is read for a specific locale, its availabilities are trimmed to those matching the requested region and its descriptions to the requested language before it is returned.
**Intent:** Calculation
**Weight:** Medium
**Logic:** after load, prune availabilities to the locale region and descriptions to the language id.
**Data Dependencies:**
- Reads: `PRODUCT_AVAILABILITY.REGION`, `PRODUCT_DESCRIPTION.LANGUAGE_ID`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | GAP |
| Error paths | 0 | 0 | OK |

> GAP note: exact region-matching precedence (country variant vs `*`) resolved in the availability/locale helper; documented as-is, resolution deferred to that boundary.

**Concrete Example:**
- API Input: `GET /api/v1/catalog/storefront/products/5001?languageCode=fr&region=CA`
- Success Output: `200 {"id":"5001","descriptions":[{"languageCode":"fr"}],"availabilities":[{"region":"CA"}]}`
- Error Input: `GET /api/v1/catalog/storefront/products/5001?languageCode=zz`
- Error Output: `200 {"id":"5001","descriptions":[]}` (no matching language)

### BR-CATPROD-014: Listing products for a category expands to the whole category lineage
**Source Reference:** `ProductServiceImpl.java:getProductsForLocale:151-177`
**Discovery Method:** Direct Source Read
**Statement:** Listing products for a category requires a category and returns products belonging to that category or any of its descendant categories in the tree.
**Intent:** Calculation
**Weight:** Medium
**Logic:** if category null → reject; build lineage prefix; list descendant categories; collect their ids plus the category's own id; query products across that id set.
**Data Dependencies:**
- Reads: `CATEGORY.LINEAGE`, `PRODUCT_CATEGORY`, `PRODUCT`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/storefront/categories/300/products?languageCode=en`
- Success Output: `200 {"items":[{"id":"5001"},{"id":"5002"}],"pagination":{"totalItems":2}}`
- Error Input: `GET /api/v1/catalog/storefront/categories//products`
- Error Output: `400 {"error":"BadRequest","message":"Category is required","statusCode":400}`

### BR-CATPROD-015: New availability defaults to the all-regions wildcard, active, zero quantities
**Source Reference:** `ProductAvailability.java:51-78` (region=ALL_REGIONS "*", status=true, quantity=0, order min/max=0)
**Discovery Method:** Direct Source Read
**Statement:** A new availability applies to all regions by default, is active, and starts with zero stock and no minimum or maximum order quantity constraint.
**Intent:** Calculation
**Weight:** Medium
**Logic:** defaults: region="*" (all regions), status=true, quantity=0, orderMin=0, orderMax=0.
**Data Dependencies:**
- Reads: none
- Writes: `PRODUCT_AVAILABILITY.REGION/STATUS/QUANTITY/QUANTITY_ORD_MIN/QUANTITY_ORD_MAX`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 5 | 5 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 5 | 5 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/availabilities {}`
- Success Output: `201 {"id":"9050","region":"*","active":true,"quantity":0,"orderMin":0,"orderMax":0}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPROD-016: Availability save routes to create or update by identity
**Source Reference:** `ProductAvailabilityServiceImpl.java:saveOrUpdate:30-40`
**Discovery Method:** Direct Source Read
**Statement:** Saving an availability creates a new record when it has no identity and updates the existing one when it does.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if availability.id present and > 0 → update else → create`.
**Data Dependencies:**
- Reads: availability.id
- Writes: `PRODUCT_AVAILABILITY`
**Side Effects:** none

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

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/products/5001/availabilities/9050 {"quantity":25}`
- Success Output: `200 {"id":"9050","quantity":25}`
- Error Input: `PUT /api/v1/catalog/products/5001/availabilities/9999 {"quantity":25}`
- Error Output: `404 {"error":"NotFound","message":"Availability not found","statusCode":404}`

### BR-CATPROD-017: Attaching a downloadable file marks the product virtual
**Source Reference:** `DigitalProductServiceImpl.java:addProductFile:38-72`
**Discovery Method:** Direct Source Read
**Statement:** Attaching a downloadable file to a product stores the file, records the digital-product link, and marks the product as virtual so downstream fulfillment treats it as a non-shippable download.
**Intent:** State Transition
**Weight:** Medium
**Logic:** require inputs; link digital product to product; save; store file in downloads content manager; set product virtual=true; update product.
**Data Dependencies:**
- Reads: product, file
- Writes: `PRODUCT_DIGITAL.FILE_NAME`, `PRODUCT.PRODUCT_VIRTUAL`
**Side Effects:** Calls: downloads content manager; search re-index via product update

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 2 | 2 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/digital-file {"fileName":"manual.pdf","content":"<base64>"}`
- Success Output: `201 {"productId":"5001","fileName":"manual.pdf","virtual":true}`
- Error Input: `POST /api/v1/catalog/products/5001/digital-file {"fileName":"manual.pdf"}`
- Error Output: `422 {"error":"ValidationError","message":"File content is required","statusCode":422}`

### BR-CATPROD-018: Removing a downloadable file clears the virtual flag
**Source Reference:** `DigitalProductServiceImpl.java:delete:77-87`
**Discovery Method:** Direct Source Read
**Statement:** Removing a product's downloadable file deletes the file and its link and marks the product as no longer virtual.
**Intent:** State Transition
**Weight:** Medium
**Logic:** require inputs; reload; delete digital product; remove file from content store; set product virtual=false; update product.
**Data Dependencies:**
- Reads: digital product, product
- Writes: `PRODUCT_DIGITAL`, `PRODUCT.PRODUCT_VIRTUAL`
**Side Effects:** Calls: content-store file removal

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/products/5001/digital-file`
- Success Output: `200 {"productId":"5001","virtual":false}`
- Error Input: `DELETE /api/v1/catalog/products/9999/digital-file`
- Error Output: `404 {"error":"NotFound","message":"Digital product not found","statusCode":404}`

### BR-CATPROD-019: A product cannot have two downloadable files with the same name
**Source Reference:** `DigitalProduct.java:@UniqueConstraint:28-29`
**Discovery Method:** Direct Source Read
**Statement:** A product may not carry two downloadable files that share the same file name.
**Intent:** Validation
**Weight:** Medium
**Logic:** unique on {product, file name}; a duplicate insert is rejected by the database.
**Data Dependencies:**
- Reads: product id, file name
- Writes: `PRODUCT_DIGITAL.PRODUCT_ID`, `PRODUCT_DIGITAL.FILE_NAME`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/digital-file {"fileName":"manual.pdf","content":"<base64>"}` (a file named manual.pdf already exists)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"A file with this name already exists for the product","statusCode":409}`

### BR-CATPROD-020: A product has at most one downloadable file
**Source Reference:** `DigitalProductDaoImpl.java:getByProduct:22-42`
**Discovery Method:** Direct Source Read
**Statement:** A product is expected to resolve to at most one downloadable file; encountering more than one is a data-integrity error.
**Intent:** Validation
**Weight:** Medium
**Logic:** query by store+product; empty → none; one → return; more than one → raise a non-unique-result error.
**Data Dependencies:**
- Reads: `PRODUCT_DIGITAL`, product store
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/digital-file`
- Success Output: `200 {"fileName":"manual.pdf"}`
- Error Input: `GET /api/v1/catalog/products/5001/digital-file` (two rows exist — corrupt data)
- Error Output: `500 {"error":"InternalError","message":"Multiple digital files found for product","statusCode":500}`

### BR-CATPROD-021: Relationship save routes to create or update by identity
**Source Reference:** `ProductRelationshipServiceImpl.java:saveOrUpdate:33-42`
**Discovery Method:** Direct Source Read
**Statement:** Saving a product relationship creates a new record when it has no identity and updates the existing one when it does.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if relationship.id present and > 0 → update else → create`.
**Data Dependencies:**
- Reads: relationship.id
- Writes: `PRODUCT_RELATIONSHIP`
**Side Effects:** none

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

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/relationships {"groupCode":"FEATURED","relatedProductId":"5002"}`
- Success Output: `201 {"id":"4001","groupCode":"FEATURED"}`
- Error Input: `PUT /api/v1/catalog/products/5001/relationships/9999 {"groupCode":"FEATURED"}`
- Error Output: `404 {"error":"NotFound","message":"Relationship not found","statusCode":404}`

### BR-CATPROD-022: A relationship group is a store-scoped, named, active record with no bound product
**Source Reference:** `ProductRelationshipServiceImpl.java:addGroup:47-53`,`deleteGroup:61-66`,`deactivateGroup:69-76`,`activateGroup:78-85`; `ProductRelationshipDaoImpl.java:getGroups:170-201`
**Discovery Method:** Direct Source Read
**Statement:** A relationship group is a named, store-scoped grouping that is active by default and has no product bound to the group header itself; a group can be activated, deactivated, or deleted, affecting all rows carrying its code.
**Intent:** State Transition
**Weight:** Medium
**Logic:** group = relationship with code=groupName, active=true, product=null, scoped to store; activate/deactivate flip active on all rows of the code; delete removes them; getGroups returns product-null rows.
**Data Dependencies:**
- Reads: `PRODUCT_RELATIONSHIP.CODE/ACTIVE/PRODUCT_ID/MERCHANT_ID`
- Writes: `PRODUCT_RELATIONSHIP.CODE/ACTIVE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 3 | 3 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/relationship-groups {"code":"FEATURED"}`
- Success Output: `201 {"code":"FEATURED","active":true}`
- Error Input: `PUT /api/v1/catalog/relationship-groups/FEATURED/deactivate`
- Error Output: `200 {"code":"FEATURED","active":false}`

### BR-CATPROD-023: A new relationship is active by default
**Source Reference:** `ProductRelationship.java:active=true:48-50`
**Discovery Method:** Direct Source Read
**Statement:** A newly created product relationship is active unless stated otherwise.
**Intent:** Calculation
**Weight:** Medium
**Logic:** default active=true.
**Data Dependencies:**
- Reads: none
- Writes: `PRODUCT_RELATIONSHIP.ACTIVE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/relationships {"groupCode":"UPSELL","relatedProductId":"5003"}`
- Success Output: `201 {"id":"4002","active":true}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPROD-024: Product types are resolved by code and gate cart eligibility
**Source Reference:** `ProductTypeServiceImpl.java:getProductType:24-28`; `ProductType.java:GENERAL_TYPE="GENERAL":26`, `allowAddToCart:39-40`
**Discovery Method:** Direct Source Read
**Statement:** Products are classified by a product type resolved by its code; the canonical default type is "GENERAL", and each type declares whether products of that type may be added to a cart.
**Intent:** Routing
**Weight:** Medium
**Logic:** resolve type by code; canonical default code "GENERAL"; each type carries an add-to-cart flag consumed by the cart/order boundary.
**Data Dependencies:**
- Reads: `PRODUCT_TYPE.PRD_TYPE_CODE`, `PRODUCT_TYPE.PRD_TYPE_ADD_TO_CART`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/product-types/GENERAL`
- Success Output: `200 {"code":"GENERAL","allowAddToCart":true}`
- Error Input: `GET /api/v1/catalog/product-types/NOPE`
- Error Output: `404 {"error":"NotFound","message":"Product type not found","statusCode":404}`

### BR-CATPROD-025: Product administration is store-scoped and role-gated
**Source Reference:** `ProductController.java` `@PreAuthorize("hasRole('PRODUCTS')")` (100,107,256,545,740,788,826,905,957); ownership guard (145-146,376-377,568-569,805-806,861,973-974)
**Discovery Method:** Direct Source Read
**Statement:** Every administrative product operation requires the products management role, and a product may only be operated on by an administrator whose store matches the product's owning store — enforcing tenant isolation.
**Intent:** Authorization
**Weight:** Critical
**Logic:** require role PRODUCTS on every admin action; reject unless product.store == current admin store.
**Data Dependencies:**
- Reads: `PRODUCT.MERCHANT_ID`, admin session store
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/products/5001 {"sku":"X_1"}` with token lacking PRODUCTS role
- Success Output: (n/a)
- Error Input: same
- Error Output: `403 {"error":"Forbidden","message":"Requires products management role","statusCode":403}`

### BR-CATPROD-026: A product save materializes exactly one all-regions availability with a default price
**Source Reference:** `ProductController.java:saveProduct:395-479`
**Discovery Method:** Direct Source Read
**Statement:** Saving a product through the admin editor guarantees exactly one all-regions availability carrying the submitted stock and order limits, and if that availability has no default price one is created marked as the default from the submitted amount.
**Intent:** State Transition
**Weight:** Medium
**Logic:** locate the all-regions availability and its default price; if no default price, create one marked default with the submitted amount and a per-language price description; set the availability quantity/order-min/order-max from the form.
**Data Dependencies:**
- Reads: submitted amount, stock, order limits
- Writes: `PRODUCT_AVAILABILITY.REGION/QUANTITY/QUANTITY_ORD_MIN/QUANTITY_ORD_MAX`, `PRODUCT_PRICE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 3 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products {"sku":"P_1","price":19.99,"availabilities":[{"region":"*","quantity":100}],"descriptions":[{"languageCode":"en","name":"P"}]}`
- Success Output: `201 {"id":"5010","availabilities":[{"region":"*","quantity":100,"prices":[{"defaultPrice":true,"amount":19.99}]}]}`
- Error Input: `POST /api/v1/catalog/products {"sku":"P_1","price":"abc","availabilities":[{"region":"*"}]}`
- Error Output: `422 {"error":"ValidationError","message":"Price is not a valid amount","statusCode":422}`

---

## BR-CATCAT — Category taxonomy (14 rules)

### BR-CATCAT-001: A category's lineage and depth are derived from its parent on create
**Source Reference:** `CategoryServiceImpl.java:create:42-58`
**Discovery Method:** Direct Source Read
**Statement:** When a category is created, its position in the tree (its lineage path and depth) is derived from its parent — a root category gets an empty path and depth zero, a child gets its parent's path plus the parent's identity and one greater depth.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```
persist category to obtain id
if parent present and valid: lineage = parent.lineage + "/" + parent.id ; depth = parent.depth + 1
else: lineage = "/" ; depth = 0
update category with computed lineage/depth   # second write
```
> Preserved quirk: create builds lineage as `parentLineage + "/" + parentId` (no trailing slash) while addChild uses a trailing slash (see BR-CATCAT-005); addChild's format wins for parented categories. Preserved as-is (clarification C1).
**Data Dependencies:**
- Reads: `CATEGORY.parent.lineage/id/depth`
- Writes: `CATEGORY.LINEAGE`, `CATEGORY.DEPTH`
**Side Effects:** two writes to the category on a single create

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/categories {"code":"BOOKS","parentId":100}`
- Success Output: `201 {"id":"301","code":"BOOKS","depth":1,"lineage":"/100/"}`
- Error Input: `POST /api/v1/catalog/categories {"code":""}`
- Error Output: `422 {"error":"ValidationError","message":"Category code is required","statusCode":422}`

### BR-CATCAT-002: A category with no valid parent is a root
**Source Reference:** `CategoryServiceImpl.java:create:52-53`, `addChild:342-346`
**Discovery Method:** Direct Source Read
**Statement:** A category with no valid parent is a root category, encoded structurally with an empty lineage path and depth zero rather than by any status flag.
**Intent:** State Transition
**Weight:** Medium
**Logic:** no valid parent → lineage="/", depth=0, parent=null.
**Data Dependencies:**
- Reads: parent
- Writes: `CATEGORY.LINEAGE`, `CATEGORY.DEPTH`, `CATEGORY.PARENT_ID`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/categories {"code":"ROOT_CAT"}`
- Success Output: `201 {"id":"400","depth":0,"lineage":"/"}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATCAT-003: Category code is unique within a store
**Source Reference:** `Category.java:@Table uniqueConstraints:34`; `CategoryController.java:checkCategoryCode:420-470`
**Discovery Method:** Direct Source Read
**Statement:** A category code must be unique within its store; attempting to reuse an existing code in the same store is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:** blank code → invalid; if a same-store category with the code exists and this is a new entry → "code already exists"; otherwise allowed.
> Preserved quirk: the edit-mode branch also returns "already exists" when the found category is the entity being edited (clarification C2). Preserved as-is.
**Data Dependencies:**
- Reads: `CATEGORY.CODE`, `CATEGORY.MERCHANT_ID`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/categories/code-available?code=BOOKS`
- Success Output: `200 {"available":true}`
- Error Input: `GET /api/v1/catalog/categories/code-available?code=EXISTING`
- Error Output: `200 {"available":false,"reason":"CODE_ALREADY_EXIST"}`

### BR-CATCAT-004: Category code is required
**Source Reference:** `Category.java:code:@NotEmpty:82-84`
**Discovery Method:** Direct Source Read
**Statement:** Every category must have a non-empty code.
**Intent:** Validation
**Weight:** Low
**Logic:** code is `@NotEmpty`, length 100, not nullable; violation blocks save.
**Data Dependencies:**
- Reads: submitted code
- Writes: `CATEGORY.CODE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/categories {"code":"TOYS"}`
- Success Output: `201 {"code":"TOYS"}`
- Error Input: `POST /api/v1/catalog/categories {"code":""}`
- Error Output: `422 {"error":"ValidationError","message":"Category code is required","statusCode":422}`

### BR-CATCAT-005: Reparenting a category recomputes its lineage and depth
**Source Reference:** `CategoryServiceImpl.java:addChild:331-378`
**Discovery Method:** Direct Source Read
**Statement:** Moving a category under a parent recomputes the category's tree position: moving to root gives an empty path and depth zero, while moving under a parent sets its path to the parent's path plus the parent's identity and its depth to one greater than the parent's.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```
if child or child.store null → reject
if parent null: child.parent=null; depth=0; lineage="/"
else: p=load(parent.id); child.parent=p; depth=p.depth+1; lineage=p.lineage + p.id + "/"
update child ; then propagate to descendants (BR-CATCAT-006)
```
**Data Dependencies:**
- Reads: parent lineage/depth/id
- Writes: `CATEGORY.PARENT_ID`, `CATEGORY.DEPTH`, `CATEGORY.LINEAGE`
**Side Effects:** triggers recursive subtree fix-up

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/categories/301/move {"parentId":100}`
- Success Output: `200 {"id":"301","depth":1,"lineage":"/100/"}`
- Error Input: `PUT /api/v1/catalog/categories/301/move {"parentId":100}` (category has no store)
- Error Output: `422 {"error":"ValidationError","message":"Category store is required","statusCode":422}`

### BR-CATCAT-006: Reparenting propagates the new lineage to the whole subtree
**Source Reference:** `CategoryServiceImpl.java:addChild:366-376`
**Discovery Method:** Direct Source Read
**Statement:** When a category is moved, every descendant in its subtree has its lineage and depth rebuilt so the entire branch stays consistent with the new position.
**Intent:** State Transition
**Weight:** Medium
**[Placement: app-with-strategy (set-based) — PLACE-001]** Do NOT emit a per-descendant loop; issue one set-based `UPDATE ... WHERE lineage LIKE '<oldPrefix>%'` (and rebuild depth) from the app tier.
**Logic:** compute child's lineage prefix; list all descendants by that prefix; for each descendant (skipping self) recompute via the same reparenting rule.
**Data Dependencies:**
- Reads: `CATEGORY.LINEAGE` (prefix match)
- Writes: `CATEGORY.LINEAGE/DEPTH/PARENT_ID` for every descendant
**Side Effects:** one update per descendant

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

> Placement candidate: recursive per-descendant update (N round-trips) — candidate for a set-based `UPDATE ... WHERE lineage LIKE 'prefix%'` (P4b). Preserved quirk: recursion self-skip uses identity comparison on boxed ids (clarification C3).

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/categories/100/move {"parentId":50}` (100 has descendants 301, 302)
- Success Output: `200 {"id":"100","depth":1,"descendantsUpdated":2}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATCAT-007: A root-parent sentinel normalizes a category to a root on save
**Source Reference:** `CategoryController.java:saveCategory:192-198`
**Discovery Method:** Direct Source Read
**Statement:** When a save indicates the special root marker as the parent, the category is normalized to a root category (no parent, empty path, depth zero).
**Intent:** Validation
**Weight:** Medium
**Logic:** if parent id equals the root sentinel (-1) → parent=null, lineage="/", depth=0.
**Data Dependencies:**
- Reads: submitted parent id
- Writes: `CATEGORY.PARENT_ID/LINEAGE/DEPTH`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/categories {"code":"TOP","parentId":-1}`
- Success Output: `201 {"code":"TOP","depth":0,"lineage":"/"}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATCAT-008: Reparenting only runs for a real (non-root) parent on save
**Source Reference:** `CategoryController.java:saveCategory:205-212`
**Discovery Method:** Direct Source Read
**Statement:** After a flat category save, the tree-position recomputation runs only when the category is attached to a real parent; a root category needs no recomputation.
**Intent:** Routing
**Weight:** Medium
**Logic:** if parent present and not the root sentinel → invoke reparenting with a parent reference.
**Data Dependencies:**
- Reads: submitted parent id
- Writes: `CATEGORY.PARENT_ID`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/categories {"code":"CHILD","parentId":100}`
- Success Output: `201 {"code":"CHILD","depth":1}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATCAT-009: Category edit, delete, and move are store-scoped
**Source Reference:** `CategoryController.java:saveCategory:159-163`,`deleteCategory:338-342`,`displayCategory:83-86`,`moveCategory:388-398`
**Discovery Method:** Direct Source Read
**Statement:** A category may only be edited, deleted, moved, or viewed by an administrator whose store matches the category's owning store, enforcing tenant isolation.
**Intent:** Authorization
**Weight:** Critical
**Logic:** reject unless category.store == current admin store.
> Preserved quirk: the save path compares store ids by identity (`!=`) rather than by value like delete/move (clarification C8). Preserved as-is.
**Data Dependencies:**
- Reads: `CATEGORY.MERCHANT_ID`
- Writes: none
**Side Effects:** none

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

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/categories/301` from an administrator of a different store
- Success Output: (n/a)
- Error Input: same
- Error Output: `403 {"error":"Forbidden","message":"Category belongs to another store","statusCode":403}`

### BR-CATCAT-010: Moving a category to its current parent is a no-op
**Source Reference:** `CategoryController.java:moveCategory:378-383`
**Discovery Method:** Direct Source Read
**Statement:** Moving a category under the parent it already has completes immediately without rewriting the subtree.
**Intent:** Routing
**Weight:** Medium
**Logic:** if child's current parent id equals the target parent id → return completed, do nothing.
**Data Dependencies:**
- Reads: `CATEGORY.PARENT_ID`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/categories/301/move {"parentId":100}` (already under 100)
- Success Output: `200 {"id":"301","changed":false}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATCAT-011: Moving under the root target bypasses the store-ownership check
**Source Reference:** `CategoryController.java:moveCategory:385-402`
**Discovery Method:** Direct Source Read
**Statement:** When a category is moved under the global root target, the store-ownership check is skipped; for any other target the check applies.
**Intent:** Authorization
**Weight:** Critical
**Logic:** if target parent id != 1 → run store guard on child and parent; when target is 1 (global root) the guard is skipped.
> Preserved quirk: id 1 is a magic global-root id and bypasses tenant isolation (clarification C4). Preserved as-is.
**Data Dependencies:**
- Reads: `CATEGORY.MERCHANT_ID`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/categories/301/move {"parentId":1}`
- Success Output: `200 {"id":"301","depth":1}`
- Error Input: `PUT /api/v1/catalog/categories/301/move {"parentId":500}` (parent in another store)
- Error Output: `403 {"error":"Forbidden","message":"Category belongs to another store","statusCode":403}`

### BR-CATCAT-012: Deleting a category deletes its whole subtree, leaves first
**Source Reference:** `CategoryServiceImpl.java:delete:225-289`; `Category.java:categories:59-61`
**Discovery Method:** Direct Source Read
**Statement:** Deleting a category deletes its entire subtree, processing descendants before ancestors so no dangling child categories remain.
**Intent:** State Transition
**Weight:** Medium
**Logic:** collect descendants by lineage prefix; add self; reverse order (leaves first); reconcile products (BR-CATCAT-013); delete category (cascade removes children and descriptions).
**Data Dependencies:**
- Reads: `CATEGORY.LINEAGE/ID`
- Writes: `CATEGORY`, `CATEGORY_DESCRIPTION`
**Side Effects:** subtree deletion

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/categories/100` (has descendants 301, 302)
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/categories/99999`
- Error Output: `404 {"error":"NotFound","message":"Category not found","statusCode":404}`

### BR-CATCAT-013: Deleting a category reassigns or deletes its products
**Source Reference:** `CategoryServiceImpl.java:delete:250-283`
**Discovery Method:** Direct Source Read
**Statement:** When a category is deleted, each product in the deleted subtree is detached from the removed categories if it still belongs to another category, but a product whose only category was the deleted one is itself deleted.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```
products = products in (subtree + self)
for each product (refreshed):
    if product belongs to more than one category: remove deleted categories; update; delete if now empty
    else: delete product
```
> Preserved quirk: destructive product deletion on category delete (clarification C5); the empty re-check reads a possibly stale product reference (clarification C6). Preserved as-is.
**Data Dependencies:**
- Reads: `PRODUCT`, `PRODUCT_CATEGORY`
- Writes: `PRODUCT`, `PRODUCT_CATEGORY`
**Side Effects:** cross-aggregate product delete

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/categories/301` (product 5001 in categories 301+302; product 5002 only in 301)
- Success Output: `204` (5001 detached from 301, 5002 deleted)
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATCAT-014: Categories default sort order zero and list ordered by sort then tree position
**Source Reference:** `Category.java:sortOrder:70-71`,`visible:76-77`,`categoryStatus:73-74`; `CategoryDaoImpl.java:listByStore:340-347`
**Discovery Method:** Direct Source Read
**Statement:** A category defaults to sort position zero and, when created through the admin, to visible; category listings are ordered by sort position and then by tree position.
**Intent:** Calculation
**Weight:** Medium
**Logic:** sortOrder default 0; new category visible=true; listings ordered by sortOrder asc then lineage/depth; visible and status are storefront filters.
**Data Dependencies:**
- Reads: `CATEGORY.SORT_ORDER/VISIBLE/CATEGORY_STATUS/LINEAGE/DEPTH`
- Writes: `CATEGORY.SORT_ORDER/VISIBLE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/categories?languageCode=en`
- Success Output: `200 {"items":[{"id":"100","sortOrder":0},{"id":"101","sortOrder":1}]}`
- Error Input: (n/a)
- Error Output: (n/a)

---

## BR-CATMAN — Manufacturer / brand (7 rules)

### BR-CATMAN-001: Manufacturer save routes to create or update by identity
**Source Reference:** `ManufacturerServiceImpl.java:saveOrUpdate:86-96`
**Discovery Method:** Direct Source Read
**Statement:** Saving a manufacturer creates a new record when it has no identity and updates the existing one when it does.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if manufacturer.id present and > 0 → update else → create` (descriptions cascade).
**Data Dependencies:**
- Reads: manufacturer.id
- Writes: `MANUFACTURER`, `MANUFACTURER_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/manufacturers {"code":"ACME","descriptions":[{"languageCode":"en","name":"Acme"}]}`
- Success Output: `201 {"id":"200","code":"ACME"}`
- Error Input: `PUT /api/v1/catalog/manufacturers/9999 {"code":"ACME"}`
- Error Output: `404 {"error":"NotFound","message":"Manufacturer not found","statusCode":404}`

### BR-CATMAN-002: A manufacturer cannot be deleted while products reference it
**Source Reference:** `ManufacturerController.java:deleteManufacturer:390-397`; `ManufacturerDaoImpl.java:getCountManufAttachedProducts:23-38`
**Discovery Method:** Direct Source Read
**Statement:** A manufacturer cannot be deleted while any product still references it; the deletion is refused until those products are reassigned.
**Intent:** Validation
**Weight:** Medium
**Logic:** count products referencing the manufacturer; if > 0 refuse delete; else delete.
**Data Dependencies:**
- Reads: `PRODUCT.MANUFACTURER_ID`
- Writes: `MANUFACTURER`
**Side Effects:** none

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
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/manufacturers/200` (3 products reference it)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"Manufacturer has associated products","statusCode":409}`

### BR-CATMAN-003: Manufacturer operations are store-scoped
**Source Reference:** `ManufacturerController.java:deleteManufacturer:384-388`,`saveManufacturer:250-254`,`displayManufacturer:110-113`
**Discovery Method:** Direct Source Read
**Statement:** A manufacturer may only be edited, deleted, or viewed by an administrator whose store matches the manufacturer's owning store.
**Intent:** Authorization
**Weight:** Critical
**Logic:** reject unless manufacturer.store == current admin store.
**Data Dependencies:**
- Reads: `MANUFACTURER.MERCHANT_ID`
- Writes: none
**Side Effects:** none

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

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/manufacturers/200 {"code":"ACME"}` from a different store's admin
- Success Output: (n/a)
- Error Input: same
- Error Output: `403 {"error":"Forbidden","message":"Manufacturer belongs to another store","statusCode":403}`

### BR-CATMAN-004: Manufacturer delete reloads the managed record first
**Source Reference:** `ManufacturerServiceImpl.java:delete:45-48`
**Discovery Method:** Direct Source Read
**Statement:** Deleting a manufacturer reloads the current record by its identity before removing it and its descriptions.
**Intent:** State Transition
**Weight:** Medium
**Logic:** reload by id; delete (descriptions cascade).
**Data Dependencies:**
- Reads: manufacturer id
- Writes: `MANUFACTURER`, `MANUFACTURER_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/manufacturers/200` (no products attached)
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/manufacturers/9999`
- Error Output: `404 {"error":"NotFound","message":"Manufacturer not found","statusCode":404}`

### BR-CATMAN-005: Manufacturer image must meet configured dimension and size limits
**Source Reference:** `ManufacturerController.java:saveManufacturer:203-238`
**Discovery Method:** Direct Source Read
**Statement:** A manufacturer image is rejected if its height, width, or file size exceeds the store's configured maximums, using the same image limits as products.
**Intent:** Validation
**Weight:** Medium
**Logic:** read max height/width/size from configuration; reject when the uploaded image exceeds any of them.
**Data Dependencies:**
- Reads: configuration image limits, image dimensions/size
- Writes: none
**Side Effects:** Calls: configuration provider

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 3 | 3 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 3 | 3 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/manufacturers/200/image {"content":"<oversized>"}`
- Success Output: (n/a)
- Error Input: same (image height above limit)
- Error Output: `422 {"error":"ValidationError","message":"Image height exceeds allowed maximum","statusCode":422}`

### BR-CATMAN-006: Manufacturer defaults sort order zero
**Source Reference:** `Manufacturer.java:order:46-47`; `ManufacturerController.java:saveManufacturer:280`
**Discovery Method:** Direct Source Read
**Statement:** A manufacturer defaults to sort position zero and is listed by that position.
**Intent:** Calculation
**Weight:** Medium
**Logic:** order default 0; persisted from the submitted value.
**Data Dependencies:**
- Reads: submitted order
- Writes: `MANUFACTURER.SORT_ORDER`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/manufacturers {"code":"NOORDER","descriptions":[{"languageCode":"en","name":"NoOrder"}]}`
- Success Output: `201 {"code":"NOORDER","sortOrder":0}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATMAN-007: Manufacturer descriptions are rebuilt and linked on save
**Source Reference:** `ManufacturerController.java:saveManufacturer:270-282`; `ManufacturerServiceImpl.java:addManufacturerDescription:72-82`
**Discovery Method:** Direct Source Read
**Statement:** Saving a manufacturer replaces its description set with the submitted descriptions, each linked back to the manufacturer and scoped to its language.
**Intent:** State Transition
**Weight:** Medium
**Logic:** for each submitted description set its manufacturer back-link; replace the description set; each description is one per language.
**Data Dependencies:**
- Reads: submitted descriptions
- Writes: `MANUFACTURER_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/manufacturers/200 {"descriptions":[{"languageCode":"en","name":"Acme"},{"languageCode":"fr","name":"Acme FR"}]}`
- Success Output: `200 {"id":"200","descriptions":[{"languageCode":"en"},{"languageCode":"fr"}]}`
- Error Input: (n/a)
- Error Output: (n/a)

---

## BR-CATOPT — Options, values & attributes (27 rules)

### BR-CATOPT-001: A product binds a given option-value pair at most once
**Source Reference:** `ProductAttribute.java:22-30` (unique constraint)
**Discovery Method:** Direct Source Read
**Statement:** A product may bind a specific (option, option value) pair only once; re-binding the same triple is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:** unique on {option, option value, product}; duplicate insert rejected by the database.
**Data Dependencies:**
- Reads: attribute option/value/product ids
- Writes: `PRODUCT_ATTRIBUTE.OPTION_ID/OPTION_VALUE_ID/PRODUCT_ID`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80"}` (already bound)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"This option value is already bound to the product","statusCode":409}`

### BR-CATOPT-002: A product attribute binds an option-value to a product and carries variant economics
**Source Reference:** `ProductAttribute.java:44-79`
**Discovery Method:** Direct Source Read
**Statement:** A product attribute links a product to an (option, option value) pair and carries the variant's price delta, weight delta, sort position, and behavior flags (free, default, required, display-only, discounted).
**Intent:** Calculation
**Weight:** Medium
**Logic:** structural: attribute references product+option+value (all required) plus price/weight/sort/flags.
**Data Dependencies:**
- Reads: attribute columns
- Writes: `PRODUCT_ATTRIBUTE` (all columns)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 6 | 6 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","price":5.00,"default":true}`
- Success Output: `201 {"id":"1000","price":5.00,"default":true}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATOPT-003: Option code must be non-empty and alphanumeric with underscores
**Source Reference:** `ProductOption.java:63-68`
**Discovery Method:** Direct Source Read
**Statement:** An option code must be non-empty and contain only letters, digits, and underscores.
**Intent:** Validation
**Weight:** Medium
**Logic:** `@NotEmpty` and matches `^[a-zA-Z0-9_]*$`.
**Data Dependencies:**
- Reads: submitted code
- Writes: `PRODUCT_OPTION.PRODUCT_OPTION_CODE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/options {"code":"SIZE"}`
- Success Output: `201 {"code":"SIZE"}`
- Error Input: `POST /api/v1/catalog/options {"code":"si ze"}`
- Error Output: `422 {"error":"ValidationError","message":"Option code must contain only letters, digits, and underscores","statusCode":422}`

### BR-CATOPT-004: Option code is unique within a store
**Source Reference:** `ProductOption.java:34-35`
**Discovery Method:** Direct Source Read
**Statement:** An option code is unique within a store; different stores may reuse the same code.
**Intent:** Validation
**Weight:** Medium
**Logic:** unique on {store, option code}.
**Data Dependencies:**
- Reads: option code, store
- Writes: `PRODUCT_OPTION.MERCHANT_ID/PRODUCT_OPTION_CODE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/options {"code":"SIZE"}` (code exists in store)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"Option code already exists in this store","statusCode":409}`

### BR-CATOPT-005: Option-value code must be non-empty, alphanumeric with underscores, unique per store
**Source Reference:** `ProductOptionValue.java:34-35`, `ProductOptionValue.java:52-57`
**Discovery Method:** Direct Source Read
**Statement:** An option-value code must be non-empty, contain only letters, digits, and underscores, and be unique within its store.
**Intent:** Validation
**Weight:** Medium
**Logic:** `@NotEmpty` + `^[a-zA-Z0-9_]*$`; unique on {store, value code}.
**Data Dependencies:**
- Reads: value code, store
- Writes: `PRODUCT_OPTION_VALUE.MERCHANT_ID/PRODUCT_OPTION_VAL_CODE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/option-values {"code":"LARGE"}`
- Success Output: `201 {"code":"LARGE"}`
- Error Input: `POST /api/v1/catalog/option-values {"code":"LARGE"}` (exists in store)
- Error Output: `409 {"error":"Conflict","message":"Option value code already exists in this store","statusCode":409}`

### BR-CATOPT-006: Options and option values are store-scoped
**Source Reference:** `ProductOption.java:57-59`, `ProductOptionValue.java:64-66`
**Discovery Method:** Direct Source Read
**Statement:** Every option and option value belongs to exactly one store, which anchors all per-store read scoping.
**Intent:** Validation
**Weight:** Medium
**Logic:** store reference is mandatory on both entities.
**Data Dependencies:**
- Reads: store reference
- Writes: `PRODUCT_OPTION.MERCHANT_ID`, `PRODUCT_OPTION_VALUE.MERCHANT_ID`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/options {"code":"COLOR"}` (store resolved from context)
- Success Output: `201 {"code":"COLOR","storeScoped":true}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATOPT-007: An option or value has at most one description per language
**Source Reference:** `ProductOptionDescription.java:16-22`, `ProductOptionValueDescription.java:13-20`
**Discovery Method:** Direct Source Read
**Statement:** An option or option value may have at most one localized description per language, and its descriptions are stored and removed together with it.
**Intent:** Validation
**Weight:** Medium
**Logic:** unique on {parent, language}; descriptions cascade with parent.
**Data Dependencies:**
- Reads: parent id, language
- Writes: `PRODUCT_OPTION_DESCRIPTION`, `PRODUCT_OPTION_VALUE_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/options/70/descriptions {"languageCode":"en","name":"Size"}` (en already exists)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"A description already exists for this language","statusCode":409}`

### BR-CATOPT-008: Deleting an option removes all attributes that use it
**Source Reference:** `ProductOptionServiceImpl.java:74-86`
**Discovery Method:** Direct Source Read
**Statement:** Deleting an option first removes every product attribute that references it, so no product is left bound to a deleted option, and then removes the option.
**Intent:** State Transition
**Weight:** Medium
**[Placement: app-with-strategy (set-based) — PLACE-002]** Do NOT emit a row-by-row delete loop; issue one set-based `DELETE FROM product_attribute WHERE option_id = ?` before deleting the option.
**Logic:** load attributes by option; delete each; reload option; delete option.
**Data Dependencies:**
- Reads: `PRODUCT_ATTRIBUTE` by option
- Writes: `PRODUCT_ATTRIBUTE`, `PRODUCT_OPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

> Placement candidate: row-by-row attribute delete loop — candidate for a set-based delete (P4b).

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/options/70`
- Success Output: `204` (attributes using option 70 removed)
- Error Input: `DELETE /api/v1/catalog/options/9999`
- Error Output: `404 {"error":"NotFound","message":"Option not found","statusCode":404}`

### BR-CATOPT-009: Deleting an option value removes all attributes that use it
**Source Reference:** `ProductOptionValueServiceImpl.java:88-101`
**Discovery Method:** Direct Source Read
**Statement:** Deleting an option value first removes every product attribute that references it and then removes the value.
**Intent:** State Transition
**Weight:** Medium
**[Placement: app-with-strategy (set-based) — PLACE-003]** Do NOT emit a row-by-row delete loop; issue one set-based `DELETE FROM product_attribute WHERE option_value_id = ?` before deleting the value.
**Logic:** load attributes by option value; delete each; reload value; delete value.
**Data Dependencies:**
- Reads: `PRODUCT_ATTRIBUTE` by option value
- Writes: `PRODUCT_ATTRIBUTE`, `PRODUCT_OPTION_VALUE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

> Placement candidate: row-by-row attribute delete loop — candidate for a set-based delete (P4b).

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/option-values/80`
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/option-values/9999`
- Error Output: `404 {"error":"NotFound","message":"Option value not found","statusCode":404}`

### BR-CATOPT-010: Attribute save routes to create or update by identity
**Source Reference:** `ProductAttributeServiceImpl.java:64-72`
**Discovery Method:** Direct Source Read
**Statement:** Saving a product attribute creates a new record when it has no identity and updates the existing one when it does.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if id present and > 0 → update else → create`.
**Data Dependencies:**
- Reads: attribute.id
- Writes: `PRODUCT_ATTRIBUTE`
**Side Effects:** none

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

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/products/5001/attributes/1000 {"price":7.50}`
- Success Output: `200 {"id":"1000","price":7.50}`
- Error Input: `PUT /api/v1/catalog/products/5001/attributes/9999 {"price":7.50}`
- Error Output: `404 {"error":"NotFound","message":"Attribute not found","statusCode":404}`

### BR-CATOPT-011: Option save routes to create or update by identity
**Source Reference:** `ProductOptionServiceImpl.java:60-70`
**Discovery Method:** Direct Source Read
**Statement:** Saving an option creates a new record when it has no identity and updates the existing one when it does.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if id present and > 0 → update else → create` (descriptions cascade).
**Data Dependencies:**
- Reads: option.id
- Writes: `PRODUCT_OPTION`
**Side Effects:** none

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

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/options/70 {"code":"SIZE"}`
- Success Output: `200 {"id":"70","code":"SIZE"}`
- Error Input: `PUT /api/v1/catalog/options/9999 {"code":"SIZE"}`
- Error Output: `404 {"error":"NotFound","message":"Option not found","statusCode":404}`

### BR-CATOPT-012: Option-value save routes to create or update by identity
**Source Reference:** `ProductOptionValueServiceImpl.java:69-82`
**Discovery Method:** Direct Source Read
**Statement:** Saving an option value creates a new record when it has no identity and updates the existing one when it does.
**Intent:** Routing
**Weight:** Medium
**Logic:** `if id present and > 0 → update else → create` (descriptions cascade).
**Data Dependencies:**
- Reads: value.id
- Writes: `PRODUCT_OPTION_VALUE`
**Side Effects:** none

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

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/option-values/80 {"code":"LARGE"}`
- Success Output: `200 {"id":"80","code":"LARGE"}`
- Error Input: `PUT /api/v1/catalog/option-values/9999 {"code":"LARGE"}`
- Error Output: `404 {"error":"NotFound","message":"Option value not found","statusCode":404}`

### BR-CATOPT-013: Attribute price is parsed from a formatted amount and validated
**Source Reference:** `ProductAttributeController.java:268-276`
**Discovery Method:** Direct Source Read
**Statement:** A variant's price adjustment is entered as a formatted amount, parsed into a monetary value, and rejected if it cannot be parsed.
**Intent:** Validation
**Weight:** Medium
**Logic:** parse the submitted price string into a monetary amount; on failure add a price validation error and block the save.
**Data Dependencies:**
- Reads: submitted price string
- Writes: `PRODUCT_ATTRIBUTE.PRODUCT_ATRIBUTE_PRICE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","price":"1,299.99"}`
- Success Output: `201 {"id":"1010","price":1299.99}`
- Error Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","price":"abc"}`
- Error Output: `422 {"error":"ValidationError","message":"Price is not a valid amount","statusCode":422}`

### BR-CATOPT-014: Attribute sort order must be an integer
**Source Reference:** `ProductAttributeController.java:279-285`
**Discovery Method:** Direct Source Read
**Statement:** A variant's sort position must be a valid integer; a non-integer value is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:** parse the submitted sort order as an integer; on failure add a numeric validation error.
**Data Dependencies:**
- Reads: submitted sort order
- Writes: `PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_SORT_ORD`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","sortOrder":"2"}`
- Success Output: `201 {"id":"1011","sortOrder":2}`
- Error Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","sortOrder":"x"}`
- Error Output: `422 {"error":"ValidationError","message":"Sort order must be a number","statusCode":422}`

### BR-CATOPT-015: Attribute additional weight must be an integer
**Source Reference:** `ProductAttributeController.java:288-294`
**Discovery Method:** Direct Source Read
**Statement:** A variant's additional weight is entered as an integer and stored as a monetary-precision value; fractional weights are rejected rather than truncated.
**Intent:** Validation
**Weight:** Medium
**Logic:** parse the submitted additional weight as an integer, then widen to a decimal; a decimal input is rejected on parse.
> Preserved quirk: integer-only weight on a decimal column looks incidental but is preserved as-is (clarification: integer-only weight). Preserved.
**Data Dependencies:**
- Reads: submitted weight
- Writes: `PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_WEIGHT`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","additionalWeight":"3"}`
- Success Output: `201 {"id":"1012","additionalWeight":3}`
- Error Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70","optionValueId":"80","additionalWeight":"2.5"}`
- Error Output: `422 {"error":"ValidationError","message":"Additional weight must be a whole number","statusCode":422}`

### BR-CATOPT-016: An attribute requires an option
**Source Reference:** `ProductAttributeController.java:296-300`
**Discovery Method:** Direct Source Read
**Statement:** A product attribute cannot be saved without an option selected.
**Intent:** Validation
**Weight:** Medium
**Logic:** if option is null → add a required-option error and return to the form.
**Data Dependencies:**
- Reads: attribute option
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionValueId":"80"}`
- Success Output: (n/a)
- Error Input: same
- Error Output: `422 {"error":"ValidationError","message":"An option is required","statusCode":422}`

### BR-CATOPT-017: A text-type option auto-creates a hidden display-only value
**Source Reference:** `ProductAttributeController.java:303-352`
**Discovery Method:** Direct Source Read
**Statement:** When the selected option is a free-text option, the system synthesizes a hidden display-only option value from the submitted text rather than requiring the admin to pick a value — reusing the existing value in edit mode or creating a new one otherwise.
**Intent:** State Transition
**Weight:** Medium
**Logic:** if the option type is the text sentinel: in edit mode reuse the existing value and rebuild its descriptions display-only; otherwise create a new display-only value with a generated code; mark the attribute display-only.
> Preserved quirk: the text sentinel is compared case-sensitively (`"text"`) against an enum whose name is `Text`; if types are persisted as enum names this branch is dead at runtime. Preserved as-is (clarification: type case mismatch), NOT corrected.
**Data Dependencies:**
- Reads: `PRODUCT_OPTION.PRODUCT_OPTION_TYPE`
- Writes: `PRODUCT_OPTION_VALUE`, `PRODUCT_OPTION_VALUE_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"71","textValue":"Engraved message"}` (option 71 is text type)
- Success Output: `201 {"id":"1020","displayOnly":true,"optionValueId":"85"}`
- Error Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"71"}` (no value resolved)
- Error Output: `422 {"error":"ValidationError","message":"An option value is required","statusCode":422}`

### BR-CATOPT-018: A text option value's display name is truncated to fifteen characters
**Source Reference:** `ProductAttributeController.java:311,330`
**Discovery Method:** Direct Source Read
**Statement:** For an auto-generated text option value, the display name is the first fifteen characters of the submitted text while the full text is preserved in the description.
**Intent:** Calculation
**Weight:** Medium
**Logic:** name = submitted text if shorter than 15 chars else first 15 chars; description keeps the full text.
**Data Dependencies:**
- Reads: submitted text
- Writes: `PRODUCT_OPTION_VALUE_DESCRIPTION.name` (truncated), `.description` (full)
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"71","textValue":"Happy Birthday To You"}`
- Success Output: `201 {"optionValue":{"name":"Happy Birthday ","description":"Happy Birthday To You"}}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATOPT-019: A generated text option value gets a random ten-character code
**Source Reference:** `ProductAttributeController.java:335-336`
**Discovery Method:** Direct Source Read
**Statement:** An auto-created text option value receives a randomly generated ten-character uppercase alphanumeric code that satisfies the code format and store-uniqueness constraints.
**Intent:** Calculation
**Weight:** Medium
**Logic:** generate a random 10-char uppercase alphanumeric code; rely on the store-uniqueness constraint to reject the rare collision.
**Data Dependencies:**
- Reads: none
- Writes: `PRODUCT_OPTION_VALUE.PRODUCT_OPTION_VAL_CODE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"71","textValue":"Note"}`
- Success Output: `201 {"optionValue":{"code":"A1B2C3D4E5"}}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATOPT-020: An attribute requires a resolved option value before saving
**Source Reference:** `ProductAttributeController.java:356-360`
**Discovery Method:** Direct Source Read
**Statement:** After option handling, a product attribute cannot be saved unless it has a resolved, persisted option value.
**Intent:** Validation
**Weight:** Medium
**Logic:** if the attribute still has no option-value identity → add a required-value error.
**Data Dependencies:**
- Reads: attribute option value id
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/attributes {"optionId":"70"}`
- Success Output: (n/a)
- Error Input: same
- Error Output: `422 {"error":"ValidationError","message":"An option value is required","statusCode":422}`

### BR-CATOPT-021: Saving an option or value rejects a code that already exists in the store
**Source Reference:** `OptionsController.java:167-172`, `OptionsValueController.java:177-182`
**Discovery Method:** Direct Source Read
**Statement:** Saving an option or option value is rejected when a record with the same code already exists in the store.
**Intent:** Validation
**Weight:** Medium
**Logic:** look up by store+code; if a record is found add a code-exists error.
> Preserved quirk: the check does not exclude the entity being edited, so re-saving an existing option/value with its own unchanged code raises a false "code exists" error (clarification: edit self-exclusion). Preserved as-is, NOT corrected.
**Data Dependencies:**
- Reads: `PRODUCT_OPTION.PRODUCT_OPTION_CODE` / `PRODUCT_OPTION_VALUE.PRODUCT_OPTION_VAL_CODE`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/options {"code":"SIZE"}` (code exists)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"Code already exists","statusCode":409}`

### BR-CATOPT-022: An option's type determines the value-entry widget, store-scoped
**Source Reference:** `ProductAttributeController.java:409-472`
**Discovery Method:** Direct Source Read
**Statement:** Given an option, the system reports its type so the admin UI can choose the correct value-entry widget, but only for an option that belongs to the current store.
**Intent:** Routing
**Weight:** Medium
**Logic:** load option; if missing or in another store → unauthorized; else return the option's type.
**Data Dependencies:**
- Reads: `PRODUCT_OPTION.PRODUCT_OPTION_TYPE/MERCHANT_ID`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/options/70/type`
- Success Output: `200 {"type":"Select"}`
- Error Input: `GET /api/v1/catalog/options/500/type` (option in another store)
- Error Output: `403 {"error":"Forbidden","message":"Option belongs to another store","statusCode":403}`

### BR-CATOPT-023: A product's attributes are listed with language-preferred descriptions
**Source Reference:** `ProductAttributeController.java:100-170`
**Discovery Method:** Direct Source Read
**Statement:** Listing a product's attributes resolves each option and value description in the requested language, defaulting to the first available description when the requested language is not present.
**Intent:** Routing
**Weight:** Medium
**Logic:** for each attribute resolve option/value description: default to the first, then override with the entry matching the request language.
**Data Dependencies:**
- Reads: `PRODUCT_ATTRIBUTE`, `PRODUCT_OPTION_DESCRIPTION`, `PRODUCT_OPTION_VALUE_DESCRIPTION`, language
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/attributes?languageCode=fr`
- Success Output: `200 {"items":[{"attributeId":"1000","attribute":"Taille","value":"Grand","price":"5,00 $"}]}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATOPT-024: Option descriptions are language-linked on save
**Source Reference:** `OptionsController.java:174-192`
**Discovery Method:** Direct Source Read
**Statement:** Saving an option resolves each submitted description to its language, links it back to the option, and stamps the option's owning store before the descriptions are stored with the option.
**Intent:** Calculation
**Weight:** Medium
**Logic:** for each description resolve its language, set its option back-link, replace the description set, stamp the store.
**Data Dependencies:**
- Reads: submitted descriptions, language registry
- Writes: `PRODUCT_OPTION_DESCRIPTION.LANGUAGE_ID/PRODUCT_OPTION_ID`, `PRODUCT_OPTION.MERCHANT_ID`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/options {"code":"SIZE","descriptions":[{"languageCode":"en","name":"Size"}]}`
- Success Output: `201 {"code":"SIZE","descriptions":[{"languageCode":"en","name":"Size"}]}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATOPT-025: An option value requires at least one named description
**Source Reference:** `OptionsValueController.java:184-222`
**Discovery Method:** Direct Source Read
**Statement:** An option value cannot be saved without at least one description carrying a non-blank name.
**Intent:** Validation
**Weight:** Low
**Logic:** if descriptions empty → name-required error; each blank-name description adds an error; non-blank descriptions are language-linked and kept.
**Data Dependencies:**
- Reads: submitted descriptions
- Writes: `PRODUCT_OPTION_VALUE_DESCRIPTION.name/LANGUAGE_ID`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/option-values {"code":"SM","descriptions":[{"languageCode":"en","name":"Small"}]}`
- Success Output: `201 {"code":"SM"}`
- Error Input: `POST /api/v1/catalog/option-values {"code":"SM","descriptions":[]}`
- Error Output: `422 {"error":"ValidationError","message":"At least one description name is required","statusCode":422}`

### BR-CATOPT-026: The option delete path is guarded only by store ownership
**Source Reference:** `OptionsController.java:302-338`
**Discovery Method:** Direct Source Read
**Statement:** Deleting an option is protected by a store-ownership check in the operation itself, but — unlike other administrative catalog operations — does not carry the products management role requirement at its boundary.
**Intent:** Authorization
**Weight:** Critical
**Logic:** no role annotation on the delete handler; body still rejects unless the option belongs to the current store.
> Preserved quirk: missing role gate on the option (and option-value) delete endpoints; mitigated only by the store guard (clarification: missing role gate). Preserved as-is — this is documented behavior, NOT a corrected one. The modernized service SHOULD apply the role gate; recorded as a net-new security finding for P4a disposition.
**Data Dependencies:**
- Reads: `PRODUCT_OPTION.MERCHANT_ID`
- Writes: `PRODUCT_OPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/options/70` from an admin of the owning store
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/options/70` from a different store's admin
- Error Output: `403 {"error":"Forbidden","message":"Option belongs to another store","statusCode":403}`

### BR-CATOPT-027: All option, value, and attribute reads are store-scoped
**Source Reference:** `ProductOptionDaoImpl.java:24-113`, `ProductOptionValueDaoImpl.java:22-120`, `ProductAttributeDaoImpl.java:47-121`
**Discovery Method:** Direct Source Read
**Statement:** Every listing and lookup of options, values, and attributes is filtered to the current store (and, for description queries, to the requested language); value pickers additionally hide display-only values, and language-filtered attribute reads omit attributes whose value lacks a description in that language.
**Intent:** Authorization
**Weight:** Critical
**Logic:** all queries filter on store; description queries also filter on language; pickers filter out display-only values; language-scoped attribute reads require a matching-language value description.
**Data Dependencies:**
- Reads: `MERCHANT_ID` on all three tables; `LANGUAGE_ID` on description joins; display-only flag
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/option-values?languageCode=en&includeDisplayOnly=false`
- Success Output: `200 {"items":[{"id":"80","code":"LARGE"}]}` (display-only values hidden)
- Error Input: (n/a)
- Error Output: (n/a)

---

## BR-CATPRICE — Pricing engine (15 rules)

### BR-CATPRICE-001: The base price is the price flagged as default
**Source Reference:** `ProductPriceUtils.java:getPrice:56-72` (also `calculateFinalPrice:476-500`)
**Discovery Method:** Direct Source Read
**Statement:** A product's base price is the price marked as its default price; when computing the final price only the price flagged default becomes the primary price and all others become additional prices.
**Intent:** Calculation
**Weight:** High
**Logic:** iterate availabilities and their prices; the price with the default flag becomes the base/primary; others are additional prices.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE.DEFAULT_PRICE`, `PRODUCT_PRICE.PRODUCT_PRICE_AMOUNT`, `PRODUCT_AVAILABILITY.REGION`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price`
- Success Output: `200 {"finalPrice":19.99,"originalPrice":19.99,"defaultPrice":true}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-002: Only all-regions availabilities are priced
**Source Reference:** `ProductPriceUtils.java:calculateFinalPrice:483`
**Discovery Method:** Direct Source Read
**Statement:** Final-price computation considers only prices attached to the all-regions availability; region-specific availabilities are ignored for pricing.
**Intent:** Routing
**Weight:** High
**Logic:** skip any availability whose region is not the all-regions wildcard when computing the final price.
> Preserved quirk: region-specific pricing is not implemented (source comment "accept a region" pending). Preserved as-is (D-06).
**Data Dependencies:**
- Reads: `PRODUCT_AVAILABILITY.REGION`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (product has an all-regions and a CA-only availability)
- Success Output: `200 {"finalPrice":19.99}` (CA-only prices ignored)
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-003: When no default price exists, the first other price is used
**Source Reference:** `ProductPriceUtils.java:calculateFinalPrice:502-510`
**Discovery Method:** Direct Source Read
**Statement:** When a product has prices but none is flagged as default, the first non-default price is used as the final price.
**Intent:** Calculation
**Weight:** High
**Logic:** if a default-flagged price exists, attach the others as additional; otherwise take the first non-default price as the final price.
> Preserved quirk (D-06): "first non-default price" selection depends on iteration order over an unordered price set — behavior is order-dependent and preserved as-is, NOT corrected.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE`
- Writes: none
**Side Effects:** none

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
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5002/final-price` (two prices, none default)
- Success Output: `200 {"finalPrice":9.99}` (first non-default price)
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-004: A discount is active when today falls within a present start and end window
**Source Reference:** `ProductPriceUtils.java:finalPrice:519-535`
**Discovery Method:** Direct Source Read
**Statement:** When a price has both a special start and end date, its special amount becomes the final price only while the current date is strictly after the start and strictly before the end.
**Intent:** Calculation
**Weight:** High
**Logic:** if start present and before today, and end present and after today → discount active, final = special amount, discount end recorded.
> Preserved quirk (D-06): if start is present but end is null, no discount activates on this branch. Preserved.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE.PRODUCT_PRICE_SPECIAL_ST_DATE/SPECIAL_END_DATE/SPECIAL_AMOUNT/AMOUNT`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (special 14.99, window 2024-01-01..2030-01-01)
- Success Output: `200 {"finalPrice":14.99,"originalPrice":19.99,"discounted":true,"discountEndDate":"2030-01-01"}`
- Error Input: `GET /api/v1/catalog/products/5001/final-price` (window already ended)
- Error Output: `200 {"finalPrice":19.99,"discounted":false}`

### BR-CATPRICE-005: A discount with no start but a future end is active
**Source Reference:** `ProductPriceUtils.java:finalPrice:539-545`
**Discovery Method:** Direct Source Read
**Statement:** When a price has no special start date but a special end date that is still in the future, the special amount is treated as active until that end date.
**Intent:** Calculation
**Weight:** High
**Logic:** if no discount yet and start is null and end is present and after today → discount active, final = special amount.
**Data Dependencies:**
- Reads: special date/amount columns
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (no start, end 2030-01-01, special 14.99)
- Success Output: `200 {"finalPrice":14.99,"discounted":true}`
- Error Input: `GET /api/v1/catalog/products/5001/final-price` (end in the past)
- Error Output: `200 {"finalPrice":19.99,"discounted":false}`

### BR-CATPRICE-006: A special amount with no date window is always active
**Source Reference:** `ProductPriceUtils.java:finalPrice:547-553`
**Discovery Method:** Direct Source Read
**Statement:** When a price carries a positive special amount and no start or end date, the special amount is permanently in effect ("always on sale").
**Intent:** Calculation
**Weight:** High
**Logic:** if both dates null and special amount > 0 → discount active, final = special amount.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE.PRODUCT_PRICE_SPECIAL_AMOUNT`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (special 12.00, no dates)
- Success Output: `200 {"finalPrice":12.00,"discounted":true}`
- Error Input: `GET /api/v1/catalog/products/5001/final-price` (special 0, no dates)
- Error Output: `200 {"finalPrice":19.99,"discounted":false}`

### BR-CATPRICE-007: The final price bundles the final, original, and default indications
**Source Reference:** `ProductPriceUtils.java:finalPrice:555-564`
**Discovery Method:** Direct Source Read
**Statement:** The computed final price records the effective amount (the discounted amount if a discount is active, otherwise the base), the original base amount, whether it is the default price, and — when discounted — the discount details.
**Intent:** Calculation
**Weight:** High
**Logic:** final = discount amount if active else base; original = base; mark default if applicable; if discounted, compute discount details.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE`
- Writes: none
**Side Effects:** none

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
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (discount active)
- Success Output: `200 {"finalPrice":14.99,"originalPrice":19.99,"defaultPrice":true,"discounted":true}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-008: The discount percentage is base minus special as a truncated percent
**Source Reference:** `ProductPriceUtils.java:discountPrice:573-588`
**Discovery Method:** Direct Source Read
**Statement:** When a discount is active, the discount percentage is one hundred minus the ratio of the special amount to the base amount as a percentage, truncated to a whole number, and the discounted price is set to the special amount.
**Intent:** Calculation
**Weight:** High
**Logic:** `arith = special / base ; percent = truncate(100 - arith*100) ; discountedPrice = special`. Example: base 100, special 66.10 → 33.9 → 33.
> Preserved quirk (D-06): the ratio uses floating-point division with NO guard for a zero base amount (yields Infinity/NaN); the percentage is truncated (not rounded). Preserved as-is, NOT corrected.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE.PRODUCT_PRICE_SPECIAL_AMOUNT`, `PRODUCT_PRICE.PRODUCT_PRICE_AMOUNT`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | GAP |

> GAP note: source has no zero-base guard (error path absent by design); preserved rather than added.

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (base 100.00, special 66.10)
- Success Output: `200 {"finalPrice":66.10,"discountPercent":33,"discountedPrice":66.10}`
- Error Input: `GET /api/v1/catalog/products/5003/final-price` (base 0.00, special 5.00)
- Error Output: `200 {"discountPercent":null}` (Infinity/NaN preserved — no guard)

### BR-CATPRICE-009: Default-attribute add-ons raise final and original but not discounted price
**Source Reference:** `ProductPriceUtils.java:getFinalPrice:130-175`
**Discovery Method:** Direct Source Read
**Statement:** When computing the final price with default attributes, the price deltas of default-flagged attributes are added to both the final and original amounts, but the discounted amount is left unchanged.
**Intent:** Calculation
**Weight:** High
**Logic:** compute base final price; sum price deltas of default attributes; add that sum to final and original; do not adjust the discounted amount.
> Preserved quirk (D-06): the asymmetry with BR-CATPRICE-010 (discounted price NOT adjusted here) is preserved as-is.
**Data Dependencies:**
- Reads: `PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_PRICE`, attribute default flag
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/final-price` (base 19.99, default attribute +5.00)
- Success Output: `200 {"finalPrice":24.99,"originalPrice":24.99}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-010: Selected-attribute add-ons raise final, original, and discounted price
**Source Reference:** `ProductPriceUtils.java:getFinalProductPrice:82-120`
**Discovery Method:** Direct Source Read
**Statement:** When computing the final price for a caller-selected set of attributes, every selected attribute's price delta is added to the final and original amounts and, when a discount is active, also to the discounted amount.
**Intent:** Calculation
**Weight:** High
**Logic:** compute base final price; sum price deltas of all passed attributes; add to final and original; if a discounted amount exists, add to it too.
> Preserved quirk (D-06): this variant sums ALL passed attributes (not only defaults) and DOES adjust the discounted amount, unlike BR-CATPRICE-009. Preserved as-is.
**Data Dependencies:**
- Reads: `PRODUCT_ATTRIBUTE.PRODUCT_ATTRIBUTE_PRICE`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/final-price {"selectedAttributeIds":["1000","1001"]}` (discount active, deltas +5.00 +2.00)
- Success Output: `200 {"finalPrice":21.99,"originalPrice":26.99,"discountedPrice":21.99}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-011: The admin discount indicator only recognizes a both-dates window
**Source Reference:** `ProductPriceUtils.java:hasDiscount:400-430`
**Discovery Method:** Direct Source Read
**Statement:** The admin-facing "has discount" indicator reports a discount only when both a start and end date are present and today falls strictly within them.
**Intent:** Validation
**Weight:** High
**Logic:** true only if start present and before today and end present and after today.
> Preserved quirk (D-06): narrower than the final-price engine — does NOT cover the start-null/end-present (BR-CATPRICE-005) or no-window special (BR-CATPRICE-006) cases; the two discount predicates are inconsistent. Preserved as-is.
**Data Dependencies:**
- Reads: special date columns
- Writes: none
**Side Effects:** none

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
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/prices` (admin, special with no-date always-on discount)
- Success Output: `200 {"prices":[{"hasDiscount":false}]}` (admin indicator false even though final-price engine discounts)
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATPRICE-012: A price amount is parsed from a formatted string and must be a positive number
**Source Reference:** `ProductPriceUtils.java:getAmount:340-413`
**Discovery Method:** Direct Source Read
**Statement:** A monetary amount entered by an administrator is parsed by stripping thousands and decimal separators and validating the result as a positive number; an unparseable value is rejected.
**Intent:** Validation
**Weight:** High
**Logic:** strip separators; require the remainder to parse as an integer; for a plain positive integer validate via a currency validator; otherwise validate the decimal/thousand form.
> Preserved quirk (D-06): the decimal/thousand branch is marked "should not go this path in this current release"; preserved as-is (dead/uncertain branch). Formatting constants are hardcoded (decimal '.', thousand ',').
**Data Dependencies:**
- Reads: input string
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 4 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 3 | 3 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/prices {"amount":"1,299.99"}`
- Success Output: `201 {"amount":1299.99}`
- Error Input: `POST /api/v1/catalog/products/5001/prices {"amount":"-5"}`
- Error Output: `422 {"error":"ValidationError","message":"Amount must be a positive number","statusCode":422}`

### BR-CATPRICE-013: Saving a price validates amount, special amount, and dates before ownership-scoped save
**Source Reference:** `ProductPriceController.java:saveProductPrice:349-420`
**Discovery Method:** Direct Source Read
**Statement:** Saving a product price requires the product to belong to the current store, and parses and validates the amount, the optional special amount, and the optional special start and end dates before persisting.
**Intent:** Validation
**Weight:** High
**Logic:** reject unless the product's store matches the current store; parse amount (required); parse special amount if provided; parse each provided date; block on any error, then persist.
**Data Dependencies:**
- Reads: `PRODUCT` (store), submitted price fields
- Writes: `PRODUCT_PRICE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 3 | 3 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/prices {"amount":"19.99","specialAmount":"14.99","specialStartDate":"2024-01-01","specialEndDate":"2030-01-01"}`
- Success Output: `201 {"amount":19.99,"specialAmount":14.99}`
- Error Input: `POST /api/v1/catalog/products/5001/prices {"amount":"19.99","specialStartDate":"not-a-date"}`
- Error Output: `422 {"error":"ValidationError","message":"Invalid date","statusCode":422}`

### BR-CATPRICE-014: Price save routes to create or update and propagates descriptions
**Source Reference:** `ProductPriceServiceImpl.java:saveOrUpdate:37-58` (also `addDescription:26-32`)
**Discovery Method:** Direct Source Read
**Statement:** Saving a price updates the existing record when it has an identity; for a new price the record is created first and each localized price description is then attached. A price code defaults to "base", must be non-empty and alphanumeric with underscores, and a price defaults to a one-time recurrence and zero amount.
**Intent:** State Transition
**Weight:** High
**Logic:** if id present and > 0 → update; else detach descriptions, create, then add each description linked to the price. Defaults: code "base", type one-time, amount 0; code matches `^[a-zA-Z0-9_]*$` and is non-empty.
**Data Dependencies:**
- Reads: price.id
- Writes: `PRODUCT_PRICE`, `PRODUCT_PRICE_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 3 | 3 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/prices {"code":"base","amount":"19.99","descriptions":[{"languageCode":"en","name":"Base"}]}`
- Success Output: `201 {"id":"3001","code":"base","priceType":"ONE_TIME"}`
- Error Input: `POST /api/v1/catalog/products/5001/prices {"code":"ba se","amount":"19.99"}`
- Error Output: `422 {"error":"ValidationError","message":"Price code must contain only letters, digits, and underscores","statusCode":422}`

### BR-CATPRICE-015: Deleting a price reloads the managed record and checks ownership
**Source Reference:** `ProductPriceServiceImpl.java:delete:62-68` (controller `deleteProductPrice:462-490`)
**Discovery Method:** Direct Source Read
**Statement:** Deleting a price is allowed only when the price's product belongs to the current store, and the price is reloaded by its identity before removal to avoid acting on a stale record.
**Intent:** State Transition
**Weight:** High
**Logic:** load price; reject if missing or its product's store is not the current store; reload by id; delete.
**Data Dependencies:**
- Reads: `PRODUCT_PRICE`, `PRODUCT_AVAILABILITY`→`PRODUCT`→store
- Writes: `PRODUCT_PRICE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/products/5001/prices/3001`
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/products/5001/prices/3001` from a different store's admin
- Error Output: `403 {"error":"Forbidden","message":"Price belongs to another store","statusCode":403}`

---

## BR-CATIMG — Images & media (7 rules)

### BR-CATIMG-001: Uploading a product image stores the file and the record together
**Source Reference:** `ProductImageServiceImpl.java:addProductImage:78-115` (also `addProductImages:55-75`)
**Discovery Method:** Direct Source Read
**Statement:** Uploading a product image requires image content, writes the binary to the content store, and persists the image record so the file and its metadata are stored together.
**Intent:** State Transition
**Weight:** Medium
**Logic:** require content; build a product-content file; write to content store; save the image record; always close the input stream; wrap failures.
**Data Dependencies:**
- Reads: image content
- Writes: `PRODUCT_IMAGE`
**Side Effects:** Calls: content store (binary write)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/images {"content":"<base64>","fileName":"front.jpg"}`
- Success Output: `201 {"id":"8200","fileName":"front.jpg"}`
- Error Input: `POST /api/v1/catalog/products/5001/images {"content":null}`
- Error Output: `422 {"error":"ValidationError","message":"Image content is required","statusCode":422}`

### BR-CATIMG-002: Image save routes to create or update and propagates descriptions
**Source Reference:** `ProductImageServiceImpl.java:saveOrUpdate:118-140`
**Discovery Method:** Direct Source Read
**Statement:** Saving an image updates the existing record when it has an identity; for a new image the record is created first and each localized image description is then attached.
**Intent:** State Transition
**Weight:** Medium
**Logic:** if id present and > 0 → update; else detach descriptions, save, then add each description.
**Data Dependencies:**
- Reads: image.id
- Writes: `PRODUCT_IMAGE`, `PRODUCT_IMAGE_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `PUT /api/v1/catalog/products/5001/images/8200 {"descriptions":[{"languageCode":"en","name":"Front"}]}`
- Success Output: `200 {"id":"8200","descriptions":[{"languageCode":"en","name":"Front"}]}`
- Error Input: `PUT /api/v1/catalog/products/5001/images/9999 {}`
- Error Output: `404 {"error":"NotFound","message":"Image not found","statusCode":404}`

### BR-CATIMG-003: Gallery-uploaded images are non-default
**Source Reference:** `ProductImage.java:defaultImage:41`; `ProductImagesController.java:saveProductImages:~205`
**Discovery Method:** Direct Source Read
**Statement:** An image defaults to being the product's primary image at the entity level, but images uploaded through the gallery are explicitly marked non-default since the primary image is set on the product-details screen.
**Intent:** Calculation
**Weight:** Medium
**Logic:** entity default for the primary flag is true; gallery uploads set it false.
**Data Dependencies:**
- Reads: none
- Writes: `PRODUCT_IMAGE.DEFAULT_IMAGE`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/images {"content":"<base64>"}`
- Success Output: `201 {"id":"8201","defaultImage":false}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATIMG-004: Sized image variants are addressed by filename prefix
**Source Reference:** `ProductImageServiceImpl.java:getProductImage:150-170`
**Discovery Method:** Direct Source Read
**Statement:** Large and small variants of a product image are addressed by prefixing the image file name (large with "L-", small with "S-").
**Intent:** Routing
**Weight:** Medium
**Logic:** large → prefix "L-"; small → prefix "S-"; fetch by the prefixed name from the content store.
**Data Dependencies:**
- Reads: image file name (content store)
- Writes: none
**Side Effects:** Calls: content store

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/images/8200?size=LARGE`
- Success Output: `200 {"url":".../L-front.jpg"}`
- Error Input: `GET /api/v1/catalog/products/5001/images/8200?size=HUGE`
- Error Output: `400 {"error":"BadRequest","message":"Unsupported image size","statusCode":400}`

### BR-CATIMG-005: Removing an image deletes the file and the record after an ownership check
**Source Reference:** `ProductImageServiceImpl.java:removeProductImage:190-200` (controller `deleteImage:~250-290`)
**Discovery Method:** Direct Source Read
**Statement:** Removing a product image requires the image's product to belong to the current store, then deletes the binary from the content store and the image record.
**Intent:** State Transition
**Weight:** Medium
**Logic:** load image; reject if missing or its product is in another store; remove file from content store; reload by id; delete.
**Data Dependencies:**
- Reads: `PRODUCT_IMAGE`, product store
- Writes: `PRODUCT_IMAGE`
**Side Effects:** Calls: content store (binary delete)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/products/5001/images/8200`
- Success Output: `204`
- Error Input: `DELETE /api/v1/catalog/products/5001/images/8200` from another store's admin
- Error Output: `403 {"error":"Forbidden","message":"Image belongs to another store","statusCode":403}`

### BR-CATIMG-006: Image upload validates the product and its store ownership
**Source Reference:** `ProductImagesController.java:saveProductImages:180-235`
**Discovery Method:** Direct Source Read
**Statement:** Uploading images requires the target product to exist and belong to the current store; only non-empty uploaded files are stored.
**Intent:** Validation
**Weight:** Medium
**Logic:** load product; reject if missing or in another store; collect non-empty files; delegate to the image upload flow.
> Preserved quirk: store-id comparison uses identity (`!=`) rather than value (clarification: Long `!=`). Preserved as-is.
**Data Dependencies:**
- Reads: `PRODUCT` (store), uploaded files
- Writes: none (delegates)
**Side Effects:** none

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
| Error paths | 2 | 2 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/images` (multipart, 2 files)
- Success Output: `201 {"uploaded":2}`
- Error Input: `POST /api/v1/catalog/products/9999/images`
- Error Output: `404 {"error":"NotFound","message":"Product not found","statusCode":404}`

### BR-CATIMG-007: Listing a product's images builds display paths
**Source Reference:** `ProductImagesController.java:pageProductImages:95-150`
**Discovery Method:** Direct Source Read
**Statement:** Listing a product's images returns, for each image, a display path built from the store, product, and image name, along with the image name and identity.
**Intent:** Calculation
**Weight:** Medium
**Logic:** for each image build a display path via the image path utility and prepend the context path.
**Data Dependencies:**
- Reads: `PRODUCT_IMAGE`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/images`
- Success Output: `200 {"items":[{"id":"8200","name":"front.jpg","url":"/context/.../front.jpg"}]}`
- Error Input: (n/a)
- Error Output: (n/a)

---

## BR-CATREV — Reviews (8 rules)

### BR-CATREV-001: Creating a review updates the product's running average and count
**Source Reference:** `ProductReviewServiceImpl.java:create:57-88`
**Discovery Method:** Direct Source Read
**Statement:** Creating a product review updates the product's review count and average rating incrementally so the new average is the previous average weighted by the previous count plus the new rating, divided by the new count.
**Intent:** Calculation
**Weight:** Medium
**Logic:** `total = avg*count + newRating ; count = count+1 ; avg = total/count`; then persist the review and update the product.
> Preserved quirk (D-06): the average is only recomputed on create; review delete does NOT decrement or recompute (see BR-CATREV-006). Preserved.
**Data Dependencies:**
- Reads: `PRODUCT.REVIEW_AVG`, `PRODUCT.REVIEW_COUNT`, `PRODUCT_REVIEW.REVIEWS_RATING`
- Writes: `PRODUCT.REVIEW_AVG`, `PRODUCT.REVIEW_COUNT`, `PRODUCT_REVIEW`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/reviews {"rating":4,"description":"Great"}` (product avg 3.0 over 2 reviews)
- Success Output: `201 {"id":"6001","rating":4,"productReviewAvg":3.33,"productReviewCount":3}`
- Error Input: `POST /api/v1/catalog/products/5001/reviews {"rating":4,"description":""}`
- Error Output: `422 {"error":"ValidationError","message":"Review description is required","statusCode":422}`

### BR-CATREV-002: A customer may review a product only once
**Source Reference:** `CustomerProductReviewController.java:submitProductReview:200-214`
**Discovery Method:** Direct Source Read
**Statement:** A customer may submit at most one review per product; a second submission is blocked and the existing review is shown instead.
**Intent:** Validation
**Weight:** Medium
**Logic:** load the product's reviews; if any belongs to the current customer, show it and abort creation.
> Preserved quirk (D-06): uniqueness is enforced by an in-app scan, not a database constraint, so it is not race-safe. Preserved.
**Data Dependencies:**
- Reads: `PRODUCT_REVIEW.CUSTOMERS_ID`, `PRODUCT_ID`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/reviews {"rating":5,"description":"Again"}` (customer already reviewed)
- Success Output: (n/a)
- Error Input: same
- Error Output: `409 {"error":"Conflict","message":"You have already reviewed this product","statusCode":409}`

### BR-CATREV-003: A review must have a non-blank description
**Source Reference:** `CustomerProductReviewController.java:submitProductReview:189-192`
**Discovery Method:** Direct Source Read
**Statement:** A review cannot be submitted with a blank description.
**Intent:** Validation
**Weight:** Low
**Logic:** if the description is blank → add a required-description error; block persistence.
**Data Dependencies:**
- Reads: submitted description
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/reviews {"rating":4,"description":""}`
- Success Output: (n/a)
- Error Input: same
- Error Output: `422 {"error":"ValidationError","message":"Review description is required","statusCode":422}`

### BR-CATREV-004: Review submission requires an authenticated customer and a matching store
**Source Reference:** `CustomerProductReviewController.java:submitProductReview:178-186`
**Discovery Method:** Direct Source Read
**Statement:** Submitting a review requires an authenticated customer, an existing product, and that the product belongs to the current store.
**Intent:** Authorization
**Weight:** Critical
**Logic:** require the customer role; resolve the customer (else redirect); resolve the product (else redirect); reject if the product is in another store.
**Data Dependencies:**
- Reads: session store, customer, `PRODUCT` store
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 3 | 3 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/reviews {"rating":4,"description":"Nice"}` (anonymous)
- Success Output: (n/a)
- Error Input: same
- Error Output: `401 {"error":"Unauthorized","message":"Authentication required","statusCode":401}`

### BR-CATREV-005: A review is persisted with its date, customer, and rating
**Source Reference:** `CustomerProductReviewController.java:submitProductReview:216-228`
**Discovery Method:** Direct Source Read
**Statement:** A submitted review is stored with the submission date, the submitting customer, and the rating, and triggers the product's aggregate recomputation.
**Intent:** State Transition
**Weight:** Medium
**Logic:** set review date to now; set customer; populate the review; create it (which recomputes the product aggregate).
**Data Dependencies:**
- Reads: customer, product
- Writes: `PRODUCT_REVIEW` (REVIEW_DATE, CUSTOMERS_ID, REVIEWS_RATING), `PRODUCT_REVIEW_DESCRIPTION`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `POST /api/v1/catalog/products/5001/reviews {"rating":5,"description":"Excellent"}`
- Success Output: `201 {"id":"6002","rating":5,"date":"2024-06-01"}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATREV-006: Deleting a review is store-scoped and does not recompute the aggregate
**Source Reference:** `ProductReviewController.java:deleteProductReview:168-205`
**Discovery Method:** Direct Source Read
**Statement:** An administrator may delete a review only when its product belongs to the current store; deleting a review removes it but does not recompute the product's review average or count.
**Intent:** State Transition
**Weight:** Medium
**Logic:** require the products role; load the review; reject if missing or its product is in another store; delete without touching the product aggregate.
> Preserved quirk (D-06): the aggregate drifts after deletion because it is not recomputed here; and ownership uses identity comparison. Preserved.
**Data Dependencies:**
- Reads: `PRODUCT_REVIEW`, `PRODUCT` store
- Writes: `PRODUCT_REVIEW`
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Concrete Example:**
- API Input: `DELETE /api/v1/catalog/products/5001/reviews/6001`
- Success Output: `204` (product review average unchanged)
- Error Input: `DELETE /api/v1/catalog/products/5001/reviews/6001` from another store's admin
- Error Output: `403 {"error":"Forbidden","message":"Review belongs to another store","statusCode":403}`

### BR-CATREV-007: Reviews can be listed by product, by customer, and by language
**Source Reference:** `ProductReviewDaoImpl.java:getByProduct:51-83`, `getByCustomer:29-48`, `getByProduct(Product,Language):113-147`, `getByProductAndCustomer:87-110`
**Discovery Method:** Direct Source Read
**Statement:** Reviews can be retrieved for a product, for a customer, for a product filtered to a language, and for a specific product-and-customer pair (the intended one-review lookup).
**Intent:** Routing
**Weight:** Medium
**Logic:** query reviews joined to customer and product; the language variant filters descriptions by language; the product-and-customer variant returns the single matching review.
**Data Dependencies:**
- Reads: `PRODUCT_REVIEW`, `PRODUCT_REVIEW_DESCRIPTION`, `PRODUCT`, customer
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 4 | 4 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/products/5001/reviews?languageCode=en`
- Success Output: `200 {"items":[{"id":"6001","rating":4,"description":"Great"}]}`
- Error Input: (n/a)
- Error Output: (n/a)

### BR-CATREV-008: Admin review listing shows the truncated rating and first description
**Source Reference:** `ProductReviewController.java:pageProductReviews:88-160`
**Discovery Method:** Direct Source Read
**Statement:** The administrative review listing shows each review's rating as a whole number and its first available description regardless of language.
**Intent:** Calculation
**Weight:** Medium
**Logic:** after an ownership check, for each review present the rating truncated to a whole number and the first description.
> Preserved quirk (D-06): the language-match logic is disabled, so the first description is used regardless of language. Preserved as-is (low-confidence behavior).
**Data Dependencies:**
- Reads: `PRODUCT_REVIEW`, `PRODUCT_REVIEW_DESCRIPTION`
- Writes: none
**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Concrete Example:**
- API Input: `GET /api/v1/catalog/admin/products/5001/reviews`
- Success Output: `200 {"items":[{"id":"6001","rating":4,"description":"Great"}]}`
- Error Input: (n/a)
- Error Output: (n/a)
