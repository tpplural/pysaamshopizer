# MS-11 Content / CMS Service — Component Inventory

**Service ID**: MS-11
**Analysis Mode**: Direct Source Read (no CAST)
**Legacy system**: Shopizer 2.0.1 (Java / Spring, JPA/Hibernate + QueryDSL, Infinispan CMS file store)

> Scope note: the source assessment `assessment/merchant-content-extraction-summary.md` is a COMBINED
> merchant+content segment. Only the **content / CMS half** is in scope here (BR-CMS-001..024). The merchant
> store half (BR-MERCH-001..016, MerchantStore config/branding/delete) was extracted into **MS-03
> merchant-store** and is OUT OF SCOPE for MS-11.

## Legacy Components (in scope)

| Component | Module | Type | Role | Disposition |
|-----------|--------|------|------|-------------|
| `Content.java` | sm-core-model | Entity (CONTENT) | Content row: code, visible, position, type, sortOrder, descriptions | EXTRACTED (→ content table; BR-CMS-001,003,006,007,008) |
| `ContentDescription.java` | sm-core-model | Entity (CONTENT_DESCRIPTION) | Localized description: name, seUrl, SEO meta, body | EXTRACTED (→ content_description table; BR-CMS-010,011) |
| `ContentType.java` | sm-core-model | Enum | BOX / PAGE / SECTION | EXTRACTED (BR-CMS-003) |
| `ContentPosition.java` | sm-core-model | Enum | LEFT / RIGHT | EXTRACTED (BR-CMS-006) |
| `FileContentType.java` | sm-core-model | Enum | STATIC_FILE/IMAGE/LOGO/PRODUCT/PRODUCTLG/PROPERTY/MANUFACTURER/PRODUCT_DIGITAL | EXTRACTED (BR-CMS-019,020,022) |
| `ContentFile.java` / `StaticContentFile.java` / `InputContentFile.java` / `OutputContentFile.java` / `ImageContentFile.java` | sm-core-model | POJO carriers (NOT entities) | File byte DTOs moved between controller ↔ service ↔ file SPI | ACCOUNTED (shape of file API; BR-CMS-019,022) |
| `ContentServiceImpl.java` | sm-core | Service (complex) | Content CRUD + file-type routing + logo/option image + delete-reload | EXTRACTED (BR-CMS-017,018,019,020,021,022) |
| `ContentService.java` | sm-core | Service interface | Contract only | ACCOUNTED |
| `ContentDaoImpl.java` | sm-core | DAO | listByType (4), getByCode (2), getByLanguage, getById, getBySeUrl, listNameByType | EXTRACTED (BR-CMS-008,014,015,016) |
| `ContentDao.java` | sm-core | DAO interface | Contract only | ACCOUNTED |
| `StaticContentFileManager.java` | sm-core-modules | Abstract SPI (FileGet+FilePut+FileRemove) | Pluggable file/object store contract | EXTRACTED (EXT-CMS-001; BR-CMS-019) |
| `FileGet.java` / `FilePut.java` / `FileRemove.java` | sm-core-modules | SPI interfaces | get/put/remove file(s) contract | ACCOUNTED (EXT-CMS-001 operations) |
| `ContentImageGet.java` / `ContentImageRemove.java` / `ImagePut.java` | sm-core-modules | SPI interfaces | image-variant contract | ACCOUNTED (EXT-CMS-001 image path) |
| `ContentBoxesController.java` | sm-shop | Controller (admin) | Box create/details/save; forces BOX; position options | EXTRACTED (BR-CMS-004,005,006,012,013) |
| `ContentPagesController.java` | sm-shop | Controller (admin) | Page create/details/save/remove; checkContentCode; forces PAGE | EXTRACTED (BR-CMS-002,004,005,007,012,013,018) |
| `ContentImageController.java` | sm-shop | Controller (admin) | Image paging/upload/remove (multipart → IMAGE) | EXTRACTED (BR-CMS-021,022) |
| `StaticContentController.java` | sm-shop | Controller (admin) | Static file paging/upload/remove (multipart → STATIC_FILE) | EXTRACTED (BR-CMS-019,021,022) |
| `ShopContentController.java` | sm-shop | Controller (storefront) | Friendly-URL page render (visible only) | EXTRACTED (BR-CMS-016,023) |
| `LandingController.java` | sm-shop | Controller (storefront) | Landing render; LANDING_PAGE lookup; template suffix | EXTRACTED (BR-CMS-023,024) — featured-items path OUT_OF_SCOPE (MS-04) |
| `StoreLandingController.java` | sm-shop | Controller (admin) | Landing SECTION authoring (the CONTENT half) | EXTRACTED (BR-CMS-009,012,024) — store-config half is MS-03 |
| `CmsStaticContentFileManagerInfinispanImpl.java` | sm-core-modules | SPI impl (Infinispan) | Legacy physical store | OUT_OF_SCOPE (external/Infinispan internals — SPI-contract evidence only; replaced by object store per ADR-006/CMS) |
| `StoreBrandingController.java` | sm-shop | Controller (admin) | Logo upload/remove entry point | OUT_OF_SCOPE for store record (MS-03); logo BYTE storage is inbound to this service (BR-CMS-020) |

## Owned Tables (target)

| Target table | Legacy origin |
|--------------|---------------|
| `content` | CONTENT |
| `content_description` | CONTENT_DESCRIPTION |

Object store (bytes) is owned but NOT a relational table — see 02-domain-model.md (EXT-CMS-001).

## Cross-service / external (NOT owned)

- MERCHANT_STORE (id, code, template, languages) → MS-03 (reference read; store code partitions the object store).
- LANGUAGE (id, code) → MS-01 reference-data (description language binding).
- Store LOGO bytes → inbound from MS-03 (this service owns the bytes; BV-5, BR-CMS-020).
- Product image bytes (PRODUCT/PRODUCTLG) → inbound from MS-04 (this service owns the bytes; BV-5, BR-CMS-022).
- Featured items on the landing page → MS-04 catalog (LandingController featured-items path, OUT_OF_SCOPE here).
- Physical file backend (Infinispan legacy → object store target) → EXT-CMS-001 plug-in.
