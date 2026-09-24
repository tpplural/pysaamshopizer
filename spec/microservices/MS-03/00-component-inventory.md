# MS-03 merchant-store — Component Inventory

Legacy components in scope for MS-03 (store half of Phase-1 Segment 11). CMS content components (Content/ContentDescription/file managers, CMS controllers) belong to MS-11 content-cms and are excluded.

| # | Legacy Component | Layer | LOC | Disposition | Notes |
|---|------------------|-------|-----|-------------|-------|
| 1 | `MerchantStore.java` | Model (sm-core-model) | 346 | EXTRACTED | Store entity — identity, config, defaults, languages M2M, branding metadata (BR-MS-IDENT/FIELD/DFLT/BRAND) |
| 2 | `MeasureUnit.java` | Constants (sm-core-model) | 8 | ACCOUNTED | Unit enum {KG,LB,CM,IN}; feeds BR-MS-DFLT-001 (no standalone rule — enum-only) |
| 3 | `MerchantStoreServiceImpl.java` | Service (sm-core) | 158 | EXTRACTED | saveOrUpdate routing, getByCode, delete cascade (BR-MS-PERS-001/003, BR-MS-LIFE-002) |
| 4 | `MerchantStoreDaoImpl.java` | DAO (sm-core) | 160 | EXTRACTED | Eager fetch-join loads (BR-MS-PERS-002/003). `getProducts` HQL = legacy product listing, OUT_OF_SCOPE (owned by MS-04 catalog) |
| 5 | `MerchantStoreController.java` | Admin controller (sm-shop) | 449 | EXTRACTED | Store CRUD, code check, zone/state guard, new-store email, superadmin delete, edit-own guard (BR-MS-IDENT/FIELD/LIFE) |
| 6 | `StoreBrandingController.java` | Admin controller (sm-shop) | 190 | EXTRACTED | Logo filename + template store-side (BR-MS-BRAND-001/002). Logo BYTES → MS-11 (xref) |
| 7 | `StoreLandingController.java` | Admin controller (sm-shop) | 216 | EXTRACTED | Landing SECTION provisioning trigger (BR-MS-LAND-001). Content body/descriptions → MS-11 (xref) |

## Out-of-Scope / Cross-Service (xref, not extracted here)

| Component / Behavior | Owner | Reason |
|----------------------|-------|--------|
| Logo/image byte storage (`ContentService.addLogo`, `contentFileManager`, Infinispan) | MS-11 content-cms | Binary blob storage; MS-03 keeps only the filename |
| Landing content body (`Content`, `ContentDescription`, `contentType=SECTION`) | MS-11 content-cms | CMS content entity; MS-03 only orchestrates & anchors to the store |
| Cascade delete targets (Manufacturer, MerchantConfiguration, TaxClass, Category/Product, User, Customer, Order) | MS-04/05/07/09/etc. | Each owner purges its own store-scoped data on `merchant.deleted` |
| Reference resolution (country/zone/currency/language) | MS-01 reference-data | xref codes validated via REST, not local FKs |
| `MerchantStoreDaoImpl.getProducts` | MS-04 catalog | Legacy product listing HQL; product aggregate is MS-04's |

## Disposition Summary
- Components in scope: 7 · EXTRACTED: 5 · ACCOUNTED: 1 (MeasureUnit enum) · Unaccounted: 0
- Cross-service xrefs documented: 5 · Files NOT FOUND: 0
