# MS-11 Content / CMS Service — Extraction Evidence

**Analysis Mode**: Direct Source Read (no CAST)
**Session**: Phase 4 deep extraction
**Scope**: content / CMS half of the combined merchant+content segment ONLY (BR-CMS). BR-MERCH was extracted into MS-03.

## Source Files Processed

| # | File | Read | Rules Extracted | Vectors Counted |
|---|------|------|-----------------|-----------------|
| 1 | `sm-core-model/.../content/model/Content.java` | full: id (CONTENT_SEQ), unique(MERCHANT_ID,CODE), code @NotEmpty, visible, contentPosition, contentType, sortOrder=0, getDescription() | BR-CMS-001, 003, 006, 007, 008 (entity → content table) | ✅ |
| 2 | `sm-core-model/.../content/model/ContentDescription.java` | full: unique(CONTENT_ID,LANGUAGE_ID), CONTENT_ID not null, SEF_URL(120), META_KEYWORDS/TITLE/DESCRIPTION | BR-CMS-010, 011 (entity → content_description table) | ✅ |
| 3 | `sm-core-model/.../content/model/ContentType.java` | full: enum BOX, PAGE, SECTION | BR-CMS-003 | ✅ |
| 4 | `sm-core-model/.../content/model/ContentPosition.java` | full: enum LEFT, RIGHT | BR-CMS-006 | ✅ |
| 5 | `sm-core-model/.../content/model/FileContentType.java` | full: enum STATIC_FILE/IMAGE/LOGO/PRODUCT/PRODUCTLG/PROPERTY/MANUFACTURER/PRODUCT_DIGITAL (8) | BR-CMS-019, 020, 022 | ✅ |
| 6 | `sm-core-model/.../content/model/InputContentFile.java` + `StaticContentFile.java` | full: byte-carrier POJOs (fileContentType, file InputStream) | supports BR-CMS-019, 022 | ✅ |
| 7 | `sm-core/.../content/service/ContentServiceImpl.java` | full: saveOrUpdate(id>0), delete(reload), addContentFile routing, addLogo(LOGO), addOptionImage(PROPERTY), addContentFiles, removeFile(s), getContentFile(s)/Names, getBySeUrl | BR-CMS-017, 018, 019, 020, 021, 022 | ✅ |
| 8 | `sm-core/.../content/dao/ContentDaoImpl.java` | full: listByType×4, listNameByType(visible), getByCode(store), getByCode(store,language first-row), getByLanguage, getById, getBySeUrl(visible, dead-code fallback) | BR-CMS-008, 014, 015, 016 | ✅ |
| 9 | `sm-core/.../modules/cms/content/StaticContentFileManager.java` + `FileGet/FilePut/FileRemove.java` | full: abstract SPI + get/put/remove file(s) contracts | BR-CMS-019 (EXT-CMS-001) | ✅ |
| 10 | `sm-shop/.../admin/controller/content/ContentPagesController.java` | full: createPage(PAGE + seed descriptions), getContentDetails(guards), saveContent(force PAGE, sortOrder default), checkContentCode, removeContent(ownership) | BR-CMS-002, 004, 005, 007, 012, 013, 018 | ✅ |
| 11 | `sm-shop/.../shop/controller/content/ShopContentController.java` | full: displayContent(getBySeUrl → PageInformation, template suffix) | BR-CMS-016, 023 | ✅ |

## Files read as evidence only (not separately extracted)

- `ContentBoxesController.java` — box create/save (force BOX, position options); folded into BR-CMS-004/005/006/012/013 alongside pages controller.
- `ContentImageController.java` / `StaticContentController.java` — multipart → InputContentFile upload paths; folded into BR-CMS-021/022.
- `StoreLandingController.java` — landing SECTION authoring (content half); folded into BR-CMS-009/012/024. Store-config half belongs to MS-03.
- `LandingController.java` — storefront landing render + template suffix; folded into BR-CMS-023/024. Featured-items path OUT_OF_SCOPE (MS-04).
- `CmsStaticContentFileManagerInfinispanImpl.java` — Infinispan physical impl; read as SPI-contract evidence only, OUT_OF_SCOPE internals.

## Extraction Status

- Files processed (in-scope): 11 primary + 5 evidence-only
- Rules extracted: 24 (BR-CMS-001..024, contiguous)
- Source vectors complete: yes (8-dimension per rule)
- Owned relational tables: 2 (content, content_description)
- Owned object store: 1 (bytes, behind EXT-CMS-001 — not a relational table)

## Black-Box Call Register

| Called Unit | Called By (BR-ID) | Disposition | Rationale |
|-------------|-------------------|-------------|-----------|
| staticContentFileManager / contentFileManager (get/put/remove) | BR-CMS-019, 020, 021, 022 | OUT_OF_SCOPE (internals) | Pluggable file/object store SPI (EXT-CMS-001); legacy Infinispan replaced by object store (ADR-006/CMS) |
| CmsStaticContentFileManagerInfinispanImpl | BR-CMS-019 | OUT_OF_SCOPE | External/Infinispan internals — SPI-contract evidence only |
| languageService.getLanguagesMap | BR-CMS-012 | OUT_OF_SCOPE (reference) | Language reference owned by MS-01 |
| store.getCode / getStoreTemplate / getLanguages | BR-CMS-013, 021, 023 | OUT_OF_SCOPE (reference) | Merchant store owned by MS-03 (reference read) |
| MS-03 store branding (logo name record) | BR-CMS-020 | OUT_OF_SCOPE (caller) | MS-03 records logo file name on its store record; this service owns the bytes (BV-5) |
| MS-04 product image upload | BR-CMS-022 | OUT_OF_SCOPE (caller) | MS-04 stores PRODUCT/PRODUCTLG bytes via this service (BV-5) |
| productRelationshipService (featured items) | (LandingController) | OUT_OF_SCOPE | Catalog featured-items belong to MS-04 |

No unresolved black-box callees.
