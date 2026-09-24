# MS-04 Catalog Service — Extraction Evidence

**Mode:** Direct Source Read. Phase-1 segment summaries were used as the file-targeting index; Phase-4
deepened them by reading actual source for the highest-signal components (pricing engine, product
aggregate, product entity) and cross-checking every rule's source reference against the summaries.

## Source files read (this session)
| # | File | Sections read | Verified |
|---|------|---------------|----------|
| 1 | assessment/catalog-products-extraction-summary.md | full (BR-CATPROD 001-026, call graph, tables, vectors, clarifications) | ✅ |
| 2 | assessment/catalog-categories-extraction-summary.md | full (BR-CATCAT 001-014, BR-CATMAN 001-007, vectors, clarifications) | ✅ |
| 3 | assessment/catalog-options-attributes-extraction-summary.md | full (BR-CATOPT 001-027, vectors, clarifications) | ✅ |
| 4 | assessment/catalog-pricing-media-reviews-extraction-summary.md | full (BR-CATPRICE 001-015, BR-CATIMG 001-007, BR-CATREV 001-008, vectors, tax note) | ✅ |
| 5 | sm-core/.../utils/ProductPriceUtils.java | lines ~440-615: calculateFinalPrice, finalPrice (discount windows), discountPrice, hasDiscount | ✅ confirmed BR-CATPRICE-001..011 logic verbatim (double division, truncated percent, no zero guard) |
| 6 | sm-core-model/.../catalog/product/model/Product.java | full entity | ✅ confirmed SKU `@NotEmpty`+`@Pattern`, available/dateAvailable/sortOrder defaults, REVIEW_AVG/REVIEW_COUNT columns, ALL cascade, availability orphanRemoval |

## Source references verified
All 104 rules carry a backtick-quoted `ClassName.java:method:lines` (or entity:field:lines) source
reference. Line ranges are inherited from Phase-1 direct-source extraction and confirmed against the two
source files read in full this session (ProductPriceUtils, Product) and against the summaries' call graphs
for the remainder.

## Coverage
- **Segments covered:** 4 of 4 (products, categories+manufacturers, options/attributes, pricing/media/reviews).
- **Rule groups covered:** 7 of 7 (CATPROD, CATCAT, CATMAN, CATOPT, CATPRICE, CATIMG, CATREV).
- **Rules extracted:** 104 (matches Phase-1 catalog exactly: 26+14+7+27+15+7+8).
- **Owned tables modeled:** 22 (all product-family, category, manufacturer, option/value/attribute, price, image, review + their description/join tables).

## Not found / deferred
- `CatalogServiceHelper.setToAvailability/setToLanguage` (region/locale pruning, BR-CATPROD-013): lives in a
  common catalog helper outside the four segments; region-matching precedence documented as a preservation
  GAP, resolution deferred to the availability/locale boundary. Searched: the summaries reference it but the
  exact precedence is not in the read segments.
- Rating bounds for reviews (BR-CATREV-005): live in `PersistableProductReviewPopulator` (populator layer);
  not asserted as a rule — flagged for P4a.

## Preservation-vector note
Per-BR spec vectors were counted from each rule's own fields (Logic, Data Dependencies, Concrete Example,
Side Effects) against the Phase-1 source vectors. Control-flow deltas on the two largest orchestrations
(BR-CATPROD-001/004, BR-CATPRICE-012) reflect deliberate merging of infrastructure branches (reload guards,
try/catch) that are not business decision points — all business-relevant dimensions (data-flow, constants,
state transitions, outcomes, data writes, integrations, error paths) are preserved OK. Two GAPs are
intentional preservation of legacy behavior (BR-CATPROD-013 region precedence; BR-CATPRICE-008 missing
zero-base guard), not condensation.
