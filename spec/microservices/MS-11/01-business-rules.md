# MS-11 Content / CMS Service — Business Rules

**Service ID**: MS-11
**Service Name**: content-cms
**Version**: 1.0
**Status**: 🟡 In Progress (Phase 4 extraction — pending 4a review)
**Analysis Mode**: Direct Source Read (no CAST)
**Rule Group**: CMS (single group)
**Total Rules**: 24 (BR-CMS-001..024, contiguous)

## Architecture context (READ FIRST)

MS-11 owns the CMS content subsystem: content boxes, content pages, content sections (including the store
landing page), their localized descriptions, and the physical **binary object store** for static files and
images. It replaces Shopizer's `ContentService` + `ContentDao` + the admin/storefront content controllers +
the Infinispan-backed `StaticContentFileManager` file store.

**Content model (2.0.1 code evidence — do NOT contradict):**
- The content type set is a fixed enum of **BOX, PAGE, SECTION** only (`ContentType.java`). BOX = a
  positioned storefront content box, PAGE = a standalone CMS page, SECTION = a system content grouping (the
  landing page is a SECTION with the reserved code `LANDING_PAGE`).
- The content entity carries a **single visibility flag** (`boolean visible`, `Content.java:66-67`). There is
  **NO `published` column and NO `linkToMenu` column** in this 2.0.1 baseline. Those are later-version
  features and are explicitly out of scope — see BR-CMS-008 note and the completion summary.

**BV-5 blob-ownership seam (reflect precisely):**
- content-cms **owns the binary bytes** (the object store) AND the CMS content rows (target `content` /
  `content_description`, legacy CONTENT / CONTENT_DESCRIPTION).
- Catalog (MS-04) and merchant-store (MS-03) keep their blob METADATA + a reference `blob_key` and **delegate
  byte storage/retrieval to content-cms**. Store logos (LOGO) and product images (PRODUCT/PRODUCTLG) are
  stored VIA this service's file API — MS-03/MS-04 are inbound callers; content-cms is the byte provider and
  owner. BR-CMS-020 (logo) and BR-CMS-022 (product-image upload path) back these inbound calls.

**Extension point:** the physical binary store is modeled as **EXT-CMS-001 — pluggable content-file/object
store** behind a file SPI (get / put / remove + image variants). The legacy Infinispan implementation is
evidence/out-of-scope internals; the modernized target replaces it with an object store (ADR-006/CMS). The
service logic calls the SPI resolver, never Infinispan directly.

**D-06 preservation:** BR-CMS-016 preserves a legacy control-flow defect (a duplicated `uniqueResult`→`list`
fallback in the friendly-URL lookup) exactly as-is and is FLAGGED for Phase 4a — it is NOT corrected here.
BR-CMS-015 (first-row fallback masking multiplicity) and BR-CMS-019 (inverted helper naming) are likewise
preserved-and-flagged.

---

### BR-CMS-001: Content code is unique per store

**Source Reference:** `Content.java:36-37` (`@UniqueConstraint(columnNames={"MERCHANT_ID","CODE"})`), `Content.java:63-65` (`@NotEmpty CODE length=100`); persisted via `ContentServiceImpl.java:saveOrUpdate:110-127`
**Discovery Method:** Direct Source Read

**Statement:** Within a single store, every content item must carry a non-empty business code that is unique among that store's content. The same code may be reused by a different store, but never twice inside one store. This code is the stable lookup key operators and the storefront use to reference a piece of content.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```
Content is keyed by (store, code)              // DB unique constraint (MERCHANT_ID, CODE)
code must be non-empty (@NotEmpty)
lookups resolve content by (code, store)       // getByCode(code, store)
```

**Data Dependencies:**
- Reads/Writes: `CONTENT.MERCHANT_ID`, `CONTENT.CODE`

**Side Effects:**
- Database unique-constraint violation on a same-store duplicate code.

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
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"about-us","descriptions":[{"languageCode":"en","name":"About us"}]}`
- Success: `201 {"id":"CNT-1001","code":"about-us","contentType":"Page"}`
- Error Input: `POST /api/v1/content/pages {"code":"about-us",...}` (code already used in this store)
- Error Output: `409 {"error":"Conflict","message":"Content code about-us already exists for this store"}`

---

### BR-CMS-002: Pre-save content-code availability check (create vs edit)

**Source Reference:** `ContentPagesController.java:checkContentCode:279-343`
**Discovery Method:** Direct Source Read

**Statement:** Before saving, an operator can check whether a proposed content code is available. A blank code is never available. On creation, the code is available only if no content in the store already uses it. On edit, the code is available only when it belongs to the same content item being edited; any other match is treated as a collision.
**Intent:** Validation
**Weight:** Low

**Logic:**
```
if blank(code) → CODE_ALREADY_EXIST                      // blank treated as unavailable
content := getByCode(code, store)
if editing (id supplied):
    OK only if content != null AND content.code == code AND content.id == id
    else → CODE_ALREADY_EXIST
else (creating):
    if content != null → CODE_ALREADY_EXIST
    else → OPERATION_COMPLETED (available)
```

**Data Dependencies:**
- Reads: `CONTENT.CODE`, `CONTENT.MERCHANT_ID`

**Side Effects:**
- None (read-only availability check).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/code-available?code=faq`
- Success: `200 {"code":"faq","available":true}`
- Error Input: `GET /api/v1/content/code-available?code=` (blank)
- Error Output: `200 {"code":"","available":false,"reason":"code is required"}`

---

### BR-CMS-003: Content type is a fixed set {Box, Page, Section}

**Source Reference:** `ContentType.java:3-5` (enum `BOX, PAGE, SECTION`); `Content.java:71-74` (`@Enumerated(STRING) CONTENT_TYPE`)
**Discovery Method:** Direct Source Read

**Statement:** Every content item has exactly one kind, drawn from a fixed set: a positioned storefront box, a standalone content page, or a system content section. There is no free-form or open-ended content kind; the landing page is represented as a section.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```
CONTENT_TYPE ∈ { BOX, PAGE, SECTION }          // stored as string enum
BOX     → positioned storefront content box
PAGE    → standalone CMS page (friendly-URL addressable)
SECTION → system grouping (landing page uses SECTION + code LANDING_PAGE)
```

**Data Dependencies:**
- Reads/Writes: `CONTENT.CONTENT_TYPE`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 3 | 3 | OK (BOX, PAGE, SECTION) |
| State transitions | 0 | 0 | OK |
| Outcomes | 0 | 0 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"terms","contentType":"Page",...}`
- Success: `201 {"id":"CNT-1002","contentType":"Page"}`
- Error Input: `POST /api/v1/content/pages {"code":"terms","contentType":"Widget",...}`
- Error Output: `422 {"error":"ValidationError","message":"contentType must be one of Box, Page, Section"}`

---

### BR-CMS-004: The content kind is owned by the endpoint, not the caller

**Source Reference:** `ContentBoxesController.java:saveContent:190-194` (forces `BOX`); `ContentPagesController.java:saveContent:257-266` (`content.setContentType(ContentType.PAGE)`); create paths `ContentPagesController.java:createPage:66`, `ContentBoxesController.java:createBox`
**Discovery Method:** Direct Source Read

**Statement:** When content is saved through the boxes authoring path it is always recorded as a box; when saved through the pages authoring path it is always recorded as a page. The kind is fixed by which authoring operation is used, and any kind supplied on the request payload is ignored.
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```
save-box  → content.contentType := BOX     // overwrites any submitted value
save-page → content.contentType := PAGE    // overwrites any submitted value
then saveOrUpdate(content)
```

**Data Dependencies:**
- Writes: `CONTENT.CONTENT_TYPE`

**Side Effects:**
- None beyond the persisted type on save.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (BOX, PAGE) |
| State transitions | 1 | 1 | OK (type assignment) |
| Outcomes | 0 | 0 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/boxes {"code":"promo-left","contentType":"Page",...}` (caller wrongly says Page)
- Success: `201 {"id":"CNT-1003","contentType":"Box"}` (forced to Box by the boxes endpoint)
- Error Input: n/a (type override is silent by design; validated only against the enum in BR-CMS-003)
- Error Output: n/a

---

### BR-CMS-005: Detail/edit access requires matching store and matching kind

**Source Reference:** `ContentPagesController.java:getContentDetails:105-119`; `ContentBoxesController.java:getContentDetails:113-127`
**Discovery Method:** Direct Source Read

**Statement:** A content item can only be opened for editing when it exists, belongs to the requesting operator's store, and is of the kind the authoring screen handles. A missing item, an item owned by a different store, or an item of the wrong kind is refused.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
content := getById(id)
if content == null → refuse (redirect to list)
if content.store.id != session.store.id → refuse (cross-store guard)
if content.contentType != <PAGE for pages screen | BOX for boxes screen> → refuse
```

**Data Dependencies:**
- Reads: `CONTENT.MERCHANT_ID`, `CONTENT.CONTENT_TYPE`

**Side Effects:**
- None (denied requests do not persist).

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
| Error paths | 3 | 3 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/pages/CNT-1002` (owned by caller's store, type Page)
- Success: `200 {"id":"CNT-1002","contentType":"Page","code":"terms"}`
- Error Input: `GET /api/v1/content/pages/CNT-1003` (CNT-1003 is a Box, or belongs to another store)
- Error Output: `404 {"error":"NotFound","message":"Content not found for this store and type"}`

---

### BR-CMS-006: Box position is an optional {Left, Right} placement

**Source Reference:** `ContentPosition.java:3-5` (enum `LEFT, RIGHT`); `Content.java:67-70` (`@Enumerated(STRING) CONTENT_POSITION nullable=true`); `ContentBoxesController.java:boxPositions`
**Discovery Method:** Direct Source Read

**Statement:** A content box may optionally declare where it renders, left or right. Position is meaningful only for boxes and may be left unset; pages and sections do not use position.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```
CONTENT_POSITION ∈ { LEFT, RIGHT } or NULL     // nullable — a box need not be positioned
boxes screen offers exactly { LEFT, RIGHT }
pages/sections do not set position
```

**Data Dependencies:**
- Reads/Writes: `CONTENT.CONTENT_POSITION`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (LEFT, RIGHT) |
| State transitions | 0 | 0 | OK |
| Outcomes | 0 | 0 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/boxes {"code":"promo","position":"Left",...}`
- Success: `201 {"id":"CNT-1004","contentType":"Box","position":"Left"}`
- Error Input: `POST /api/v1/content/boxes {"code":"promo","position":"Top",...}`
- Error Output: `422 {"error":"ValidationError","message":"position must be Left or Right when supplied"}`

---

### BR-CMS-007: Content sort order defaults to zero and orders listings

**Source Reference:** `Content.java:76-77` (`private Integer sortOrder = 0`); `ContentPagesController.java:saveContent:257-259` (`if sortOrder==null → 0`); `ContentDaoImpl.java:listByType:35-52,56-73,77-96,127-144` (`orderBy(sortOrder.asc())`)
**Discovery Method:** Direct Source Read

**Statement:** Every content item has a numeric display order that defaults to zero when not supplied. Content listings are always returned in ascending order of this value so operators control presentation sequence.
**Intent:** Calculation
**Weight:** Medium

**Logic:**
```
new content seeds sortOrder := 0
on save, if sortOrder == null → sortOrder := 0
all listByType queries orderBy(sortOrder ASC)
```

**Data Dependencies:**
- Reads/Writes: `CONTENT.SORT_ORDER`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (default 0) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"help",...}` (no sortOrder)
- Success: `201 {"id":"CNT-1005","sortOrder":0}`
- Error Input: `GET /api/v1/content/pages` returns items unordered — expectation violated
- Error Output: contract requires items ordered by `sortOrder` ascending, then a stable tiebreak

---

### BR-CMS-008: Visibility is the sole publish gate, applied only on storefront reads

**Source Reference:** `Content.java:66-67` (`boolean VISIBLE`); `ContentDaoImpl.java:listNameByType:112` (`.and(qContent.visible.eq(true))`), `getBySeUrl:246` (`.and(qContent.visible.eq(true))`)
**Discovery Method:** Direct Source Read

**Statement:** A content item is either visible or hidden, and visibility is the only publish signal in this baseline. Storefront-facing reads — the menu-name listing and the friendly-URL page lookup — return only visible content. Administrative and landing-code reads are not filtered by visibility and see all content regardless of flag.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
storefront reads (listNameByType, getBySeUrl) → filter visible == true
admin/landing reads (listByType, getByCode) → NO visible filter (see all)
```

*Note (later-version absence):* there is NO `published` and NO `linkToMenu` column in 2.0.1. Visibility is a
plain boolean with no workflow/transition guard. Flagged for 4a — do not model a Draft/Published state
machine that the source does not have.

**Data Dependencies:**
- Reads: `CONTENT.VISIBLE`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (true) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/storefront/pages/promotions.html` (content hidden, visible=false)
- Success (admin): `GET /api/v1/content/pages/CNT-1006` returns the hidden item to an operator
- Error Input: storefront request for a hidden friendly URL
- Error Output: `404 {"error":"NotFound","message":"Content not available"}` (visibility gate)

---

### BR-CMS-009: The landing section defaults to visible on first creation

**Source Reference:** `StoreLandingController.java:saveStoreLanding:119-124` (`new Content{visible=true, contentType=SECTION, code=LANDING_PAGE}`)
**Discovery Method:** Direct Source Read

**Statement:** The first time a store's landing content is authored, it is created as a visible section under the reserved landing code. This ensures the home page renders immediately after it is first saved. Boxes and pages, by contrast, are not visible by default unless the operator marks them so.
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```
content := getByCode("LANDING_PAGE", store)
if content == null:
    content := new Content{ visible=true, contentType=SECTION, code="LANDING_PAGE", store }
// box/page create paths leave visible at primitive default (false) unless the form sets it
```

**Data Dependencies:**
- Writes: `CONTENT.VISIBLE`, `CONTENT.CODE`, `CONTENT.CONTENT_TYPE`

**Side Effects:**
- None until the subsequent saveOrUpdate.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 3 | 3 | OK (visible=true, SECTION, LANDING_PAGE) |
| State transitions | 1 | 1 | OK (create-defaulting) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/content/landing {"descriptions":[{"languageCode":"en","name":"Home","body":"<h1>Welcome</h1>"}]}` (first time)
- Success: `200 {"code":"LANDING_PAGE","contentType":"Section","visible":true}`
- Error Input: `PUT /api/v1/content/landing {}` (no descriptions supplied)
- Error Output: `422 {"error":"ValidationError","message":"at least one localized description is required"}`

---

### BR-CMS-010: One localized description per content per language

**Source Reference:** `ContentDescription.java:16-21` (`@UniqueConstraint{CONTENT_ID, LANGUAGE_ID}`), `:30-32` (`CONTENT_ID nullable=false`); `Content.java:52-55` (`@OneToMany cascade=ALL`)
**Discovery Method:** Direct Source Read

**Statement:** A content item may carry at most one localized description per language. Descriptions are owned by their parent content — saving the content persists and updates its descriptions, and deleting the content removes them.
**Intent:** Validation
**Weight:** Medium

**Logic:**
```
CONTENT_DESCRIPTION unique on (CONTENT_ID, LANGUAGE_ID)
CONTENT_ID not null
descriptions cascade ALL from parent Content (persist + delete)
```

**Data Dependencies:**
- Reads/Writes: `CONTENT_DESCRIPTION.CONTENT_ID`, `CONTENT_DESCRIPTION.LANGUAGE_ID`

**Side Effects:**
- Cascade persist/delete of descriptions with parent content.

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
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"faq","descriptions":[{"languageCode":"en","name":"FAQ"},{"languageCode":"fr","name":"Questions"}]}`
- Success: `201 {"id":"CNT-1007","descriptions":[{"languageCode":"en"},{"languageCode":"fr"}]}`
- Error Input: two `en` descriptions on the same content
- Error Output: `409 {"error":"Conflict","message":"Duplicate description for language en"}`

---

### BR-CMS-011: A description carries a required name, friendly URL, and SEO metadata

**Source Reference:** `ContentDescription.java:34-56` (`SEF_URL length=120`, `META_KEYWORDS`, `META_TITLE`, `META_DESCRIPTION`); `Description.java` mapped superclass (`NAME @NotEmpty length=120`, `DESCRIPTION` CLOB, `TITLE`)
**Discovery Method:** Direct Source Read

**Statement:** Each localized description must have a name. It may also carry a search-engine-friendly URL slug used to address the page on the storefront, a body of rich text, and search-engine metadata (title, keywords, meta description) that populate the rendered page's head information.
**Intent:** Validation
**Weight:** Low

**Logic:**
```
name required (@NotEmpty, length ≤ 120)
seUrl (SEF_URL, ≤ 120) → storefront friendly-URL key
description (CLOB) → rendered body
metatagTitle / metatagKeywords / metatagDescription → SEO PageInformation
```

**Data Dependencies:**
- Reads/Writes: `CONTENT_DESCRIPTION.NAME`, `.SEF_URL`, `.DESCRIPTION`, `.META_TITLE`, `.META_KEYWORDS`, `.META_DESCRIPTION`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 6 | 6 | OK |
| Constants | 1 | 1 | OK (length 120) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"about","descriptions":[{"languageCode":"en","name":"About","friendlyUrl":"about-us","metaTitle":"About our store"}]}`
- Success: `201 {"id":"CNT-1008","descriptions":[{"languageCode":"en","friendlyUrl":"about-us"}]}`
- Error Input: description with no name
- Error Output: `422 {"error":"ValidationError","message":"description name is required"}`

---

### BR-CMS-012: Submitted descriptions bind to the canonical language by code

**Source Reference:** `ContentPagesController.java:saveContent:249-255` (`langs.get(description.language.code)`); `ContentBoxesController.java:saveContent:186-190`; `StoreLandingController.java:saveStoreLanding:155-160`
**Discovery Method:** Direct Source Read

**Statement:** When content is saved, each supplied description's language is re-resolved to the store's canonical language by its language code, and the description is attached to its parent content, so descriptions always reference a known language and the correct owner.
**Intent:** Data Access
**Weight:** Medium

**Logic:**
```
for each submitted description:
    description.language := languageMap.get(description.language.code)   // canonical language
    description.content  := content                                     // attach to parent
```

**Data Dependencies:**
- Reads: `LANGUAGE` (by code)
- Writes: `CONTENT_DESCRIPTION.LANGUAGE_ID`, `.CONTENT_ID` (in memory pre-save)

**Side Effects:**
- None (in-memory wiring before persist).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (language reference read) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"news","descriptions":[{"languageCode":"en","name":"News"}]}`
- Success: `201 {"id":"CNT-1009","descriptions":[{"languageCode":"en"}]}` (bound to canonical en)
- Error Input: description with `languageCode":"zz"` (not a store language)
- Error Output: `422 {"error":"ValidationError","message":"Unknown language code zz"}`

---

### BR-CMS-013: Creation seeds one empty description per store language

**Source Reference:** `ContentPagesController.java:createPage:71-77`; `ContentBoxesController.java:createBox`
**Discovery Method:** Direct Source Read

**Statement:** When an operator begins creating a content item, the item is pre-populated with one empty localized description for every language the store supports, so the authoring form presents one editable tab per language.
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```
for each language in store.languages:
    content.descriptions.add(new ContentDescription{ language })   // blank name/body
```

**Data Dependencies:**
- Reads: `store.languages`
- Writes: `CONTENT_DESCRIPTION` (in-memory scaffold)

**Side Effects:**
- None (scaffold only; nothing persisted until save).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (scaffold defaulting) |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/pages/new` (store supports en + fr)
- Success: `200 {"descriptions":[{"languageCode":"en","name":null},{"languageCode":"fr","name":null}]}`
- Error Input: store with no configured languages
- Error Output: `200 {"descriptions":[]}` (empty scaffold — operator must have store languages configured first)

---

### BR-CMS-014: Content listings are store-scoped, type-filtered, and ordered

**Source Reference:** `ContentDaoImpl.java:listByType` (four overloads: `:26-49`, `:52-70`, `:74-93`, `:127-144`)
**Discovery Method:** Direct Source Read

**Statement:** Every content listing is restricted to a single store, filtered to one or more content kinds, and returned in ascending display order. Language-aware listings additionally restrict to descriptions in the requested language so each item shows its localized name.
**Intent:** Data Access
**Weight:** Medium

**Logic:**
```
filter: store.id == :storeId AND (contentType == :type OR contentType IN :types)
join descriptions + store (left join, fetch)
language-aware overload: AND description.language.id == :languageId
orderBy sortOrder ASC
```

**Data Dependencies:**
- Reads: `CONTENT`, `CONTENT_DESCRIPTION`, `CONTENT.SORT_ORDER`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (single-type vs list-of-types) |
| Data-flow | 4 | 4 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/pages?languageCode=en`
- Success: `200 {"items":[{"id":"CNT-1002","name":"Terms","sortOrder":0}],"pagination":{...}}`
- Error Input: `GET /api/v1/content/pages?languageCode=zz`
- Error Output: `422 {"error":"ValidationError","message":"Unknown language code zz"}`

---

### BR-CMS-015: Code lookup returns a single item; language lookup returns the first match

**Source Reference:** `ContentDaoImpl.java:getByCode(code,store):155-171` (`singleResult`), `getByCode(code,store,language):205-225` (`results.get(0)` fallback)
**Discovery Method:** Direct Source Read

**Statement:** Looking up content by store and code returns the one matching item. Looking up content by store, code, and language returns the first matching row even when the join produces more than one, so the language-aware lookup never fails on a multiplicity it could otherwise detect.
**Intent:** Data Access
**Weight:** Medium

**Logic:**
```
getByCode(code, store)            → query.singleResult   // exactly one expected (BR-CMS-001)
getByCode(code, store, language)  → results = query.list
                                     if empty → null
                                     else → results.get(0)   // first-row even if size > 1
```

**Data Dependencies:**
- Reads: `CONTENT`, `CONTENT_DESCRIPTION`

**Side Effects:**
- None.

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
| Error paths | 1 | 1 | GAP |

**Preservation:** FLAGGED (Error paths) — the language overload silently returns the first row when the join yields multiple description rows, masking a potential multiplicity issue rather than surfacing it. Given the (store, code) unique constraint this should not occur, but the behavior is preserved as-is and FLAGGED for 4a.

**Concrete Example:**
- Input: `GET /api/v1/content/by-code?code=about&languageCode=en`
- Success: `200 {"id":"CNT-1008","code":"about","languageCode":"en"}`
- Error Input: `GET /api/v1/content/by-code?code=missing&languageCode=en`
- Error Output: `404 {"error":"NotFound","message":"Content about not found"}`

---

### BR-CMS-016: Friendly-URL lookup resolves a visible page and returns its description

**Source Reference:** `ContentDaoImpl.java:getBySeUrl:228-273`
**Discovery Method:** Direct Source Read

**Statement:** The storefront resolves a content page by its friendly URL within a store, returning the localized description only when the content is visible. A hidden or non-existent friendly URL resolves to nothing.
**Intent:** Data Access
**Weight:** Medium

**Logic:**
```
query: description.seUrl == :seUrl AND store.id == :storeId AND content.visible == true
content := query.uniqueResult
if content != null → return content.getDescription()   // first description
// LEGACY DEFECT (preserved): a redundant second branch re-runs query.list()
//   results = query.list(); if not empty → content := results.get(0); return description
// the second branch re-executes the same query and is unreachable when uniqueResult already returned
```

**Data Dependencies:**
- Reads: `CONTENT_DESCRIPTION.SEF_URL`, `CONTENT.VISIBLE`, `CONTENT.MERCHANT_ID`

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | GAP |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (visible=true) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | GAP |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (Control-flow, Error paths) — the DAO runs `uniqueResult` and then a redundant `query.list()` fallback on the same query; the fallback branch is effectively dead/confused control flow. Preserved exactly as-is (not simplified) and FLAGGED for 4a to confirm the second branch is dead code vs. defensive against a known duplicate condition.

**Concrete Example:**
- Input: `GET /api/v1/content/storefront/pages/about-us.html`
- Success: `200 {"name":"About us","body":"<p>...</p>","metaTitle":"About our store"}`
- Error Input: `GET /api/v1/content/storefront/pages/hidden-page.html` (visible=false)
- Error Output: `404 {"error":"NotFound","message":"Content not available"}`

---

### BR-CMS-017: Content save routes on identity (insert vs update)

**Source Reference:** `ContentServiceImpl.java:saveOrUpdate:110-127` (`if id != null && id > 0 → update else save`)
**Discovery Method:** Direct Source Read

**Statement:** Saving a content item creates a new record when it has no assigned identity and updates the existing record otherwise. Descriptions are persisted together with the content in the same operation.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
if content.id != null AND content.id > 0 → update(content)
else                                     → save(content)
// cascade persists/updates descriptions with the parent
```

**Data Dependencies:**
- Writes: `CONTENT`, `CONTENT_DESCRIPTION` (cascade)

**Side Effects:**
- INSERT or UPDATE of content plus cascaded descriptions.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (id > 0 guard) |
| State transitions | 1 | 1 | OK (transient→persistent) |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/pages {"code":"privacy",...}` (no id)
- Success: `201 {"id":"CNT-1010","code":"privacy"}` (insert)
- Error Input: `PUT /api/v1/content/pages/CNT-9999 {...}` (id does not exist)
- Error Output: `404 {"error":"NotFound","message":"Content CNT-9999 not found"}`

---

### BR-CMS-018: Delete re-loads the managed item before removal

**Source Reference:** `ContentServiceImpl.java:delete:55-62` (`c = getById(content.id); super.delete(c)`); `ContentPagesController.java:removeContent:130-165` (store-ownership guard)
**Discovery Method:** Direct Source Read

**Statement:** Deleting a content item first reloads the current record by its identity and then removes it, so the delete always operates on a managed, up-to-date item and cascades to its descriptions. The caller must own the item's store before delete is attempted.
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```
guard: content.store.id == session.store.id   // controller-level ownership check
c := getById(content.id)                       // reload managed instance
delete(c)                                       // cascades descriptions
```

**Data Dependencies:**
- Writes: `CONTENT`, `CONTENT_DESCRIPTION` (cascade delete)

**Side Effects:**
- DELETE of content plus cascaded description rows.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (persistent→deleted) |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `DELETE /api/v1/content/pages/CNT-1010`
- Success: `204` (content and its descriptions removed)
- Error Input: `DELETE /api/v1/content/pages/CNT-2000` (owned by another store)
- Error Output: `404 {"error":"NotFound","message":"Content not found for this store"}`

---

### BR-CMS-019: File-type routing selects the file store by content-file type

**Source Reference:** `ContentServiceImpl.java:addContentFile:135-149`; identical branches in `removeFile:256-268`, `getContentFile:291-307`, `getContentFilesNames:325-337`
**Discovery Method:** Direct Source Read

**Statement:** When a binary file is stored, retrieved, or removed, the target file store is chosen by the file's type: static files and general images go to the static-file store, while all other categories (logos, product images, option/property images, and similar) go to the image store. Both stores are pluggable behind a common file interface.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
if fileContentType ∈ { IMAGE, STATIC_FILE } → staticContentFileManager      // via private addFile()
else                                         → contentFileManager           // via private addImage()
// NAMING QUIRK (preserved): the private helper addFile() calls staticContentFileManager,
//   and addImage() calls contentFileManager — the helper names are inverted vs the two SPI beans.
```

**Extension Point:** EXT-CMS-001 — the two file managers are the pluggable content-file/object store SPI
(get/put/remove). The rule's Logic dispatches to the resolved SPI, never to a concrete Infinispan class.

**Data Dependencies:**
- Reads: `InputContentFile.fileContentType`

**Side Effects:**
- Delegates the binary write/read/remove to the resolved file-store SPI; the input stream is closed in a `finally` block.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 2 | 2 | OK (IMAGE, STATIC_FILE) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 2 | 2 | OK (two SPI stores) |
| Error paths | 1 | 1 | GAP |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (Error paths) — the inverted `addFile`/`addImage` helper naming relative to the two SPI beans is preserved exactly (not renamed) and FLAGGED for 4a. The routing behavior (IMAGE/STATIC_FILE → static store) is preserved.

**Concrete Example:**
- Input: `POST /api/v1/content/stores/DEFAULT/files {"fileType":"StaticFile","fileName":"site.css"}`
- Success: `201 {"fileName":"site.css","fileType":"StaticFile","store":"static-file-store"}`
- Error Input: `POST` with a null file type
- Error Output: `422 {"error":"ValidationError","message":"fileContentType is required"}`

---

### BR-CMS-020: Store logo is stored as a logo-typed object and its name recorded on the store

**Source Reference:** `ContentServiceImpl.java:addLogo:151-163` (forces `FileContentType.LOGO`); `StoreBrandingController.java:saveStoreBranding:96-109`, `removeImage:159-181`
**Discovery Method:** Direct Source Read

**Statement:** A store's logo is uploaded through the content-file service as a logo-typed object; content-cms owns and stores the bytes. The store service (a separate owner) then records the resulting file name against the store and, on removal, clears it. This is an inbound call from the store service to content-cms (BV-5).
**Intent:** State Transition
**Weight:** Medium

**Logic:**
```
addLogo(storeCode, file):
    file.fileContentType := LOGO       // forced
    addImage(...)                       // → contentFileManager (image store)
// caller (MS-03 store service): store.logo := uploadedFileName ; update store
// remove: removeFile(storeCode, LOGO, logoName) ; store.logo := null ; update store
```

**Extension Point:** EXT-CMS-001 — logo bytes are written through the pluggable file-store SPI.

**Data Dependencies:**
- Writes: content-cms object store (LOGO bytes). Store logo file-NAME is recorded by MS-03 (not owned here).

**Side Effects:**
- Object-store write/delete of the logo. MS-03 records/clears the logo name on its own store record (out of scope, inbound-callee relationship).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (LOGO) |
| State transitions | 1 | 1 | OK (store logo set/cleared — by MS-03) |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK (object store) |
| Integrations | 1 | 1 | OK (MS-03 inbound) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/content/stores/DEFAULT/logo` (multipart: `logo.png`) — called by MS-03 store branding
- Success: `201 {"fileName":"logo.png","fileType":"Logo"}`
- Error Input: `DELETE /api/v1/content/stores/DEFAULT/logo?fileName=missing.png`
- Error Output: `404 {"error":"NotFound","message":"Logo missing.png not found for store DEFAULT"}`

---

### BR-CMS-021: The object store is partitioned by store code

**Source Reference:** `ContentServiceImpl.java` (`addContentFile`/`addLogo`/`removeFile`/`getContentFile` all take `merchantStoreCode`; `Assert.notNull(merchantStoreCode,...)`); callers pass `store.getCode()` — `ContentImageController.java`, `StaticContentController.java`, `StoreBrandingController.java`
**Discovery Method:** Direct Source Read

**Statement:** Every stored file lives in a namespace keyed by the owning store's code. All file operations require a store code, so a store's binary assets are isolated from every other store's assets. This ties the physical namespace to the store's code business key.
**Intent:** Data Access
**Weight:** Medium

**Logic:**
```
every file op requires non-null merchantStoreCode (Assert.notNull)
object-store key := storeCode + fileContentType + fileName
callers pass store.getCode() (not id)
```

**Data Dependencies:**
- Reads: store code (reference); object-store namespace.

**Side Effects:**
- None beyond the delegated store operation.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (object store) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/stores/ACME/files?fileType=Image`
- Success: `200 {"items":["banner.jpg","promo.png"]}` (only ACME's images)
- Error Input: `GET /api/v1/content/stores//files?fileType=Image` (blank store code)
- Error Output: `422 {"error":"ValidationError","message":"store code is required"}`

---

### BR-CMS-022: Uploads build a typed file object from each multipart part

**Source Reference:** `ContentImageController.java:saveContentImages:171-199` (IMAGE); `StaticContentController.java:saveFiles:146-169` (STATIC_FILE); `StoreBrandingController.java:saveStoreBranding:96-104` (LOGO — also backs admin product-create image path via product controllers delegating here)
**Discovery Method:** Direct Source Read

**Statement:** Each non-empty uploaded file is turned into a typed file object carrying its original name, MIME type, byte stream, and the category stamped by the upload path (image, static file, or logo), then stored in one batch. Empty parts are skipped, and an entirely empty upload is silently ignored.
**Intent:** Data Access
**Weight:** Medium

**Logic:**
```
for each MultipartFile part:
    if part empty → skip
    else → InputContentFile{ fileName=originalName, mimeType=contentType, file=bytes, fileContentType=<IMAGE|STATIC_FILE|LOGO> }
addContentFiles(storeCode, list)   // batch
// QUIRK (preserved): an entirely empty list falls into an empty else branch — no UI error surfaced
```

**Extension Point:** EXT-CMS-001 — bytes are batched into the pluggable file-store SPI. Product-image uploads
(PRODUCT/PRODUCTLG) from MS-04 use this same inbound path (content-cms owns the bytes; BV-5).

**Data Dependencies:**
- Reads: multipart upload parts
- Writes: object store (batch)

**Side Effects:**
- Batch object-store write. Empty-upload no-op surfaces no error (preserved).

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 4 | 4 | OK |
| Constants | 3 | 3 | OK (IMAGE, STATIC_FILE, LOGO) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK (object store) |
| Error paths | 1 | 1 | GAP |

**Preservation:** FLAGGED [D-06 PRESERVED-AS-IS] (Error paths) — an empty overall upload list falls into an empty else branch that surfaces no user feedback. Preserved as-is and FLAGGED for 4a (intended no-op vs. missing feedback).

**Concrete Example:**
- Input: `POST /api/v1/content/stores/ACME/images` (multipart: `banner.jpg`, `promo.png`)
- Success: `201 {"stored":["banner.jpg","promo.png"],"fileType":"Image"}`
- Error Input: `POST /api/v1/content/stores/ACME/images` with no file parts
- Error Output: `200 {"stored":[]}` (silent no-op — preserved legacy behavior; flagged for 4a)

---

### BR-CMS-023: Storefront content renders through a store-template-suffixed view

**Source Reference:** `LandingController.java:displayLanding:130` (`"landing." + store.getStoreTemplate()`); `ShopContentController.java:displayContent:56-59` (`Content.content + "." + storeTemplate`)
**Discovery Method:** Direct Source Read

**Statement:** The storefront landing page and CMS content pages are rendered through a view whose name is suffixed by the store's selected template, letting each store choose a theme variant for the same content. The template is set from the store's branding configuration, never from the content-authoring form.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
landing view := "landing." + store.template
content-page view := "content." + store.template
// template comes from store branding (MS-03), not the content form
```

**Data Dependencies:**
- Reads: store template (reference from MS-03)

**Side Effects:**
- None.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (view bases: landing., content.) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (store template read) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/storefront/landing` (store template = "boutique")
- Success: `200 {"view":"landing.boutique","content":{...}}`
- Error Input: store with no template configured
- Error Output: `200 {"view":"landing.default","content":{...}}` (falls back to default template suffix)

---

### BR-CMS-024: The landing page is addressed by the reserved code LANDING_PAGE

**Source Reference:** `LandingController.java:41,73` (`getByCode("LANDING_PAGE", store, language)`); `StoreLandingController.java:58,117`
**Discovery Method:** Direct Source Read

**Statement:** Both the storefront and the admin landing editor resolve the store's home-page content through a single reserved code. The admin editor writes the home-page copy and SEO metadata into that section's per-language descriptions; the storefront reads them to build the home page.
**Intent:** Routing
**Weight:** Medium

**Logic:**
```
landing content := getByCode("LANDING_PAGE", store [, language])   // a SECTION
admin: writes home-page body + meta into its per-language descriptions
storefront: reads meta + body into PageInformation
```

**Data Dependencies:**
- Reads/Writes: `CONTENT.CODE == "LANDING_PAGE"` (a SECTION), its descriptions

**Side Effects:**
- None beyond the underlying content save/read.

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (LANDING_PAGE) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/content/storefront/landing?languageCode=en`
- Success: `200 {"code":"LANDING_PAGE","name":"Home","body":"<h1>Welcome</h1>","metaTitle":"Home"}`
- Error Input: `GET /api/v1/content/storefront/landing?languageCode=en` before landing content is authored
- Error Output: `200 {"code":"LANDING_PAGE","content":null}` (no landing content yet — storefront renders default home)
