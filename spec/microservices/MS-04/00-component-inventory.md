# MS-04 Catalog Service — Component Inventory

Legacy Shopizer 2.0.1 components composing the catalog service, grouped by the four Phase-1 segments.
Paths are relative to `initial-source/shopizer/`. `/target/` build output is excluded.

## Segment: Products (core)
| Component | Path | Role |
|-----------|------|------|
| ProductServiceImpl | sm-core/.../catalog/product/service/ProductServiceImpl.java | Aggregate save/delete orchestration |
| ProductDaoImpl | sm-core/.../catalog/product/dao/ProductDaoImpl.java | HQL reads + visibility filter |
| ProductAvailabilityServiceImpl | sm-core/.../catalog/product/service/availability/ProductAvailabilityServiceImpl.java | Availability save routing |
| DigitalProductServiceImpl | sm-core/.../catalog/product/service/file/DigitalProductServiceImpl.java | Digital-file attach/detach |
| DigitalProductDaoImpl | sm-core/.../catalog/product/dao/file/DigitalProductDaoImpl.java | Digital-file uniqueness read |
| ProductRelationshipServiceImpl | sm-core/.../catalog/product/service/relationship/ProductRelationshipServiceImpl.java | Relationship + group lifecycle |
| ProductRelationshipDaoImpl | sm-core/.../catalog/product/dao/relationship/ProductRelationshipDaoImpl.java | Group queries |
| ProductTypeServiceImpl | sm-core/.../catalog/product/service/type/ProductTypeServiceImpl.java | Type lookup by code |
| Product (entity) | sm-core-model/.../catalog/product/model/Product.java | SKU pattern, defaults, review aggregate columns |
| ProductAvailability (entity) | sm-core-model/.../catalog/product/model/availability/ProductAvailability.java | Availability defaults / ALL_REGIONS |
| ProductRelationship (entity) | sm-core-model/.../catalog/product/model/relationship/ProductRelationship.java | Active default |
| DigitalProduct (entity) | sm-core-model/.../catalog/product/model/file/DigitalProduct.java | Unique {product, file} |
| ProductType (entity) | sm-core-model/.../catalog/product/model/type/ProductType.java | GENERAL, allowAddToCart |
| ProductController (admin) | sm-shop/.../admin/controller/products/ProductController.java | Role + store guards, default price/availability |

## Segment: Categories
| Component | Path | Role |
|-----------|------|------|
| CategoryServiceImpl | sm-core/.../catalog/category/service/CategoryServiceImpl.java | Lineage/depth engine, subtree delete, product reconciliation |
| CategoryDaoImpl | sm-core/.../catalog/category/dao/CategoryDaoImpl.java | Lineage-prefix + ordered queries |
| Category (entity) | sm-core-model/.../catalog/category/model/Category.java | Code unique per store, sort/visible defaults |
| CategoryController | sm-shop/.../admin/controller/categories/CategoryController.java | Save/move/delete/checkCode, sentinels -1/1 |
| ManufacturerServiceImpl | sm-core/.../catalog/product/service/manufacturer/ManufacturerServiceImpl.java | Save routing, delete reload |
| ManufacturerDaoImpl | sm-core/.../catalog/product/dao/manufacturer/ManufacturerDaoImpl.java | Attached-product count |
| Manufacturer (entity) | sm-core-model/.../catalog/product/model/manufacturer/Manufacturer.java | Sort order default |
| ManufacturerController | sm-shop/.../admin/controller/products/ManufacturerController.java | Image validation, delete guard |

## Segment: Options & Attributes
| Component | Path | Role |
|-----------|------|------|
| ProductOptionServiceImpl | sm-core/.../catalog/product/service/attribute/ProductOptionServiceImpl.java | Option save/delete cascade |
| ProductOptionValueServiceImpl | sm-core/.../catalog/product/service/attribute/ProductOptionValueServiceImpl.java | Value save/delete cascade |
| ProductAttributeServiceImpl | sm-core/.../catalog/product/service/attribute/ProductAttributeServiceImpl.java | Attribute save routing |
| ProductOptionDaoImpl | sm-core/.../catalog/product/dao/attribute/ProductOptionDaoImpl.java | Store-scoped option reads |
| ProductOptionValueDaoImpl | sm-core/.../catalog/product/dao/attribute/ProductOptionValueDaoImpl.java | Store-scoped value reads, display-only filter |
| ProductAttributeDaoImpl | sm-core/.../catalog/product/dao/attribute/ProductAttributeDaoImpl.java | By-option/value/product reads |
| ProductOption / ProductOptionValue / *Description / ProductOptionType / ProductAttribute (entities) | sm-core-model/.../catalog/product/model/attribute/ | Codes, uniqueness, flags, variant economics |
| OptionsController | sm-shop/.../admin/controller/products/OptionsController.java | Option save/delete, code guard |
| OptionsValueController | sm-shop/.../admin/controller/products/OptionsValueController.java | Value save/delete, name validation |
| ProductAttributeController | sm-shop/.../admin/controller/products/ProductAttributeController.java | Attribute save, text-option engine, parse validations |

## Segment: Pricing, Media & Reviews
| Component | Path | Role |
|-----------|------|------|
| ProductPriceUtils | sm-core/.../utils/ProductPriceUtils.java | Final-price engine, discount windows, amount parsing |
| ProductPriceServiceImpl | sm-core/.../catalog/product/service/price/ProductPriceServiceImpl.java | Price save/delete |
| ProductPriceDaoImpl | sm-core/.../catalog/product/dao/price/ProductPriceDaoImpl.java | Price reads |
| ProductPriceController | sm-shop/.../admin/controller/products/ProductPriceController.java | Price validation + ownership |
| ProductPrice / ProductPriceDescription / ProductPriceType / FinalPrice (models) | sm-core-model/.../catalog/product/model/price/ + sm-core FinalPrice | Price fields, base code, recurrence type |
| ProductImageServiceImpl | sm-core/.../catalog/product/service/image/ProductImageServiceImpl.java | Image add/save/remove, sized names |
| ProductImageDaoImpl | sm-core/.../catalog/product/dao/image/ProductImageDaoImpl.java | Image reads |
| ProductImagesController | sm-shop/.../admin/controller/products/ProductImagesController.java | Upload validation, gallery listing |
| ProductImage / ProductImageDescription (models) | sm-core-model/.../catalog/product/model/image/ | Default-image flag |
| ProductReviewServiceImpl | sm-core/.../catalog/product/service/review/ProductReviewServiceImpl.java | Running average aggregate |
| ProductReviewDaoImpl | sm-core/.../catalog/product/dao/review/ProductReviewDaoImpl.java | Review queries |
| ProductReviewController (admin) | sm-shop/.../admin/controller/products/ProductReviewController.java | Admin listing/delete |
| CustomerProductReviewController | sm-shop/.../shop/controller/customer/CustomerProductReviewController.java | Storefront submit, one-per-customer |
| ProductReview / ProductReviewDescription (models) | sm-core-model/.../catalog/product/model/review/ | Rating, dormant status |

## Populators (read/write mapping — sm-shop)
| Component | Path | Role |
|-----------|------|------|
| catalog populators | sm-shop/.../web/populator/catalog/ | Persistable/Readable product/review mapping (adjacent; referenced by review + storefront reads) |

## Adjacent / cross-boundary (read-only or external, NOT owned here)
- SearchService (search subsystem) — index/deleteIndex side effects (BR-CATPROD-011)
- ProductFileManager / ContentService (CMS content store) — image + digital-file binaries
- CustomerFacade (customer service) — review author resolution (BR-CATREV-004)
- TaxClass (tax service) — referenced by product as an id only; no tax logic here
