# MS-03 merchant-store — Extraction Evidence

**Service:** MS-03 merchant-store · **Analysis mode:** Direct Source (no CAST) · **Phase:** 4 deep extraction.
**Scope:** the STORE record, its config/defaults/branding-metadata, store lifecycle, supported languages, and multi-tenancy anchoring. CMS content bytes (logo image bytes, landing content body) are MS-11 content-cms — captured here only as cross-service xrefs.

## Source Files Processed

| # | File | Lines | Tier / Passes | Sections Read | Rules Extracted | Vectors |
|---|------|-------|---------------|---------------|-----------------|---------|
| 1 | `sm-core-model/.../business/merchant/model/MerchantStore.java` | 346 | ≤500, 1 pass | Full entity: id/table-gen (43-48), storename/code/phone/address/city/postal (50-74), country/zone/state (76-93), weight/seize unit defaults (83-87), inBusinessSince default + transient dateBusinessSince (89-96), defaultLanguage + languages M2M (98-108), useCache/template/invoice/domain/continueUrl (110-118), email (120-124), storeLogo (126), currency + currencyFormatNational (128-134); accessors | 9 (IDENT, FIELD, DFLT groups) | ✅ |
| 2 | `sm-core-model/.../constants/MeasureUnit.java` | 8 | ≤500, 1 pass | enum `{KG, LB, CM, IN}` | 0 (feeds BR-MS-DFLT-001) | ✅ |
| 3 | `sm-core/.../business/merchant/service/MerchantStoreServiceImpl.java` | 158 | ≤500, 1 pass | `getMerchantStore(code)` (72-74), `saveOrUpdate` id==null insert/update (76-84), `getByCode` (94-97), `delete` cascade over manufacturers→configurations→taxClasses→content files→categories→users→customers→orders→store (99-155) | 4 (PERS, LIFE groups) | ✅ |
| 4 | `sm-core/.../business/merchant/dao/MerchantStoreDaoImpl.java` | 160 | ≤500, 1 pass | `getProducts` (legacy HQL, out-of-scope note), `getById` eager fetch-join (77-95), `getMerchantStore(String)` fetch-join uniqueResult (97-121), `getMerchantStore(Integer)` NON-fetch lazy (123-141) | 2 (PERS group) | ✅ |
| 5 | `sm-shop/.../admin/controller/merchant/MerchantStoreController.java` | 449 | ≤500, 1 pass | `pageStores` DEFAULT hidden (95-130), `displayMerchantStore` date default (170-174), `saveMerchantStore` edit-own guard (213-223), date parse (225-234), zone/state guard (264-270), hasErrors (272-274), reference re-resolve (277-315), template from session (318), saveOrUpdate (329), new-store email on code mismatch (331-360), session refresh (362-366), `checkStoreCode` (373-411), `removeMerchantStore` superadmin guard + delete (415-461) | 6 (IDENT, FIELD, LIFE groups) | ✅ |
| 6 | `sm-shop/.../admin/controller/merchant/StoreBrandingController.java` | 190 | ≤500, 1 pass | `saveStoreBranding` logo upload → addLogo(code) → store.storeLogo=filename → update (88-115), `saveTemplate` sets session store template → saveOrUpdate (129-150), `removeImage` removeFile(LOGO)+storeLogo=null (159-181) | 2 (BRAND group) | ✅ |
| 7 | `sm-shop/.../admin/controller/merchant/StoreLandingController.java` | 216 | ≤500, 1 pass | `displayStoreLanding` load LANDING_PAGE content (52-95), `saveStoreLanding` create SECTION if absent + per-language description upsert → contentService.saveOrUpdate (98-200) | 1 (LAND group — store-side orchestration only) | ✅ |

## Extraction Status
- Files total: 7 · Files processed: 7 · Files NOT FOUND: 0
- Rules extracted: 19 (BR-MS-*)
- Source vectors complete: yes (all 19 rules carry an 8-dimension Semantic Preservation table)

## Cross-Service Boundary Notes (captured as xref, NOT extracted here)
- **Logo bytes** (`ContentService.addLogo`, `FileContentType.LOGO`, Infinispan) → owned by MS-11 content-cms. MS-03 stores only the logo **filename** on the store record and triggers the content call. See BR-MS-BRAND-001.
- **Landing content body** (`Content`/`ContentDescription`, `contentType=SECTION`, `code=LANDING_PAGE`) → owned by MS-11. MS-03 captures only the store-side orchestration trigger. See BR-MS-LAND-001.
- **Decommission cascade targets** (Manufacturer, MerchantConfiguration, TaxClass, Category, User, Customer, Order, CMS files) → owned by MS-04/MS-05/MS-07/MS-09/MS-11/etc. MS-03 emits `merchant.deleted`; each owner deletes its own store-scoped data. See BR-MS-LIFE-002.
- **Reference data** (country ISO, zone code, currency code, language code) → owned by MS-01 reference-data. MS-03 stores codes as xref (not FK), resolves via REST at save. See BR-MS-FIELD-001, BR-MS-PERS-002.

## Session Log
| Session | Files Processed | Rules Added | Notes |
|---------|-----------------|-------------|-------|
| 1 | files 1-7 | 19 | Single-session extraction; all files ≤500 LOC, single-pass each. |
