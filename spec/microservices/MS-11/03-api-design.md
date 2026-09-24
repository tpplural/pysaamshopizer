# MS-11 Content / CMS Service — API Design

**Service ID**: MS-11
**Base path**: `/api/v1/content`
**Port**: 8011
**Naming**: snake_case fields, snake_case query params, kebab-case paths, PascalCase enum values (shared-convention reconciliation, 2026-09-19)
**Global headers**: `x-tenant-id` (required on every request); `x-store-id` (required on all authoring, file, and store-scoped operations). Store-scoped file ops also use `{store_code}` path params.

## Endpoints (18)

| # | Method | Endpoint | Description | Driven by |
|---|--------|----------|-------------|-----------|
| 1 | GET | /api/v1/content/pages | List the store's content pages (ordered, language-aware) | BR-CMS-014 |
| 2 | POST | /api/v1/content/pages | Create a content page (forced Page kind) | BR-CMS-001, 003, 004, 007, 010, 011, 012, 013, 017 |
| 3 | GET | /api/v1/content/pages/{contentId} | Get a content page for editing (store + type guarded) | BR-CMS-005 |
| 4 | PUT | /api/v1/content/pages/{contentId} | Update a content page and its descriptions | BR-CMS-011, 012, 017 |
| 5 | DELETE | /api/v1/content/pages/{contentId} | Delete a content page (cascade descriptions) | BR-CMS-018 |
| 6 | GET | /api/v1/content/boxes | List the store's content boxes (ordered, language-aware) | BR-CMS-014 |
| 7 | POST | /api/v1/content/boxes | Create a content box (forced Box kind, optional position) | BR-CMS-004, 006, 007, 010, 011, 012, 013, 017 |
| 8 | GET | /api/v1/content/code-available | Check content-code availability (create/edit aware) | BR-CMS-002 |
| 9 | PUT | /api/v1/content/landing | Author the store landing section (reserved code) | BR-CMS-009, 012, 024 |
| 10 | GET | /api/v1/content/storefront/landing | Storefront landing content (template-suffixed view) | BR-CMS-023, 024 |
| 11 | GET | /api/v1/content/storefront/pages/{friendlyUrl} | Storefront page by friendly URL (visible only) | BR-CMS-008, 016, 023 |
| 12 | GET | /api/v1/content/stores/{storeCode}/files | List a store's static file names | BR-CMS-021 |
| 13 | POST | /api/v1/content/stores/{storeCode}/files | Upload static files (batch) | BR-CMS-019, 021, 022 |
| 14 | DELETE | /api/v1/content/stores/{storeCode}/files/{fileName} | Remove a static file | BR-CMS-019, 021 |
| 15 | GET | /api/v1/content/stores/{storeCode}/images | List a store's image names | BR-CMS-021 |
| 16 | POST | /api/v1/content/stores/{storeCode}/images | Upload images (batch) | BR-CMS-019, 021, 022 |
| 17 | POST | /api/v1/content/stores/{storeCode}/logo | Store a store logo (inbound from MS-03) | BR-CMS-019, 020, 022 |
| 18 | DELETE | /api/v1/content/stores/{storeCode}/logo | Remove a store logo (inbound from MS-03) | BR-CMS-019, 020 |

## Notes

- Endpoints 2, 4, 5, 7, 9 mutate `content` / `content_description`. The kind is fixed by the endpoint
  (BR-CMS-004): the pages endpoints record Page, the boxes endpoint records Box, the landing endpoint records
  a Section under the reserved code `LANDING_PAGE` (BR-CMS-024).
- Endpoints 1, 6 are store-scoped, language-aware, ordered listings (BR-CMS-014). Endpoint 8 is a read-only
  code-availability check (BR-CMS-002).
- Endpoints 10, 11 are storefront reads. They apply the visibility gate (BR-CMS-008/016) and resolve a
  template-suffixed view name (BR-CMS-023). The landing read uses the reserved code (BR-CMS-024).
- Endpoints 12–18 operate on the binary object store behind EXT-CMS-001, partitioned by store code
  (BR-CMS-021). File type routes the target store (BR-CMS-019). Uploads (13, 16, 17) build typed file objects
  from multipart parts (BR-CMS-022). The empty-upload silent no-op is preserved (BR-CMS-022, D-06).
- Endpoints 17, 18 (logo) are inbound calls from MS-03 (store-service); this service owns the bytes (BV-5).
  Product-image byte storage from MS-04 uses endpoints 15/16 with `file_type=Product|ProductLarge`.

## Object-store / file-store extension point (EXT-CMS-001)

Physical byte storage is data-driven behind the file-store SPI (get/put/remove + image variants). Adding or
swapping a backend (Infinispan → object store) does not add endpoints — it registers a new SPI
implementation. The API surface is unchanged; only the resolver's target differs per deployment.
