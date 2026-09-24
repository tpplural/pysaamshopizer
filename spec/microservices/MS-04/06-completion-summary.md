# MS-04 Catalog Service — Completion Summary

**Service ID:** MS-04 · **Port:** 8004 · **Schema:** `catalog_schema` · **Priority:** 1 (Core)
**Status:** 🟢 Spec package complete (extraction) — pending Validator + Tracker + P4a review.

## Counts (verified against file content)
| Metric | Count |
|--------|-------|
| Business rules (`### BR-` headers in 01-business-rules.md) | **104** |
| Owned tables (CREATE TABLE in 02-domain-model.md) | **22** |
| API operations (OpenAPI paths × methods) | **59** |
| API paths | 36 |
| OpenAPI schemas | 55 |
| Data invariants | 10 |
| Entity state models | 3 (Product, ProductPrice discount, RelationshipGroup) + category tree-position |

## Rule count as a decomposition outcome (NOT a target hit)
104 rules = the seven Phase-1 rule groups carried forward **1:1 with the Phase-1 catalog** (26 CATPROD +
14 CATCAT + 7 CATMAN + 27 CATOPT + 15 CATPRICE + 7 CATIMG + 8 CATREV). Phase-1 for this domain was already
a faithful direct-source extraction (High confidence 80-89% per segment), so Phase-4's deep read
**confirmed** the decomposition rather than splitting or merging it. No rule was split to inflate the count
and none was padded; the count is the sum of the source-driven groups, not a fitted number.

### Per-group breakdown
| Group | Domain | Rules | Owned tables (primary) |
|-------|--------|-------|------------------------|
| BR-CATPROD | Product aggregate & lifecycle | 26 | product, product_description, product_availability, product_digital, product_relationship, product_type, product_category |
| BR-CATCAT | Category taxonomy | 14 | category, category_description, product_category |
| BR-CATMAN | Manufacturer / brand | 7 | manufacturer, manufacturer_description |
| BR-CATOPT | Options, values & attributes | 27 | product_option(_description), product_option_value(_description), product_attribute |
| BR-CATPRICE | Pricing engine | 15 | product_price, product_price_description |
| BR-CATIMG | Images & media | 7 | product_image, product_image_description |
| BR-CATREV | Reviews | 8 | product_review, product_review_description |

## Net-new findings (from the deep read, beyond Phase-1 grouping)
1. **BR-CATOPT-026 — missing role gate on option/option-value delete (security exposure).** The delete
   handlers omit the products-management role annotation that every other admin catalog operation carries;
   only a store-ownership guard remains. Preserved as-is (D-06) but flagged as a net-new security finding —
   the modernized service SHOULD add the role gate. Raised for P4a disposition.
2. **BR-CATPRICE-008 — unguarded floating-point discount ratio (defect).** The discount percentage divides
   the special amount by the base amount as a `double` with no zero-base guard, yielding Infinity/NaN, and
   truncates (not rounds) the percentage. Preserved as-is; flagged.
3. **BR-CATPRICE-009 vs -010 — asymmetric attribute add-on (behavioral subtlety).** Default-attribute
   pricing does NOT adjust the discounted amount while selected-attribute pricing does. Two divergent code
   paths preserved as-is.
4. **BR-CATPRICE-011 vs -004/005/006 — two inconsistent discount predicates.** The admin "has discount"
   indicator recognizes only a both-dates window; the final-price engine also activates start-null/end-present
   and no-window discounts. Preserved as-is.
5. **INV-CAT-009 — review aggregate drift (defect).** `review_avg`/`review_count` are maintained on review
   create (BR-CATREV-001) but NOT on delete (BR-CATREV-006), so the aggregate drifts. Preserved as-is;
   invariant tagged `app` with a note that a hardened target would recompute.
6. **BR-CATCAT-013 — destructive product deletion on category delete.** Deleting a category deletes products
   whose only category was the removed one. Preserved as-is; surfaced as a behavioral risk.
7. **Wire-format detail — BR-CATOPT-018 fifteen-character text-value name truncation** and **BR-CATOPT-019
   ten-character generated code** are exact algorithmic details preserved for faithful reimplementation.

## Preserved quirks (D-06 — behavior preserved, NOT corrected)
- Category lineage trailing-slash inconsistency between create and addChild (BR-CATCAT-001).
- Category code-check false positive in edit mode (BR-CATCAT-003).
- Option/value code-exists false positive in edit mode (BR-CATOPT-021).
- Text-option sentinel case mismatch making the branch potentially dead at runtime (BR-CATOPT-017).
- Boxed-id identity comparisons in recursion and ownership checks (BR-CATCAT-006, BR-CATCAT-009, BR-CATIMG-006, BR-CATREV-006).
- Magic ids: root sentinel -1 (BR-CATCAT-007), global-root id 1 bypassing tenant isolation (BR-CATCAT-011).
- Region-specific pricing not implemented (BR-CATPRICE-002); order-dependent first-non-default price selection (BR-CATPRICE-003).
- Integer-only attribute weight on a decimal column (BR-CATOPT-015).

## Greenfield rules (no legacy source origin)
**None.** Every one of the 104 rules traces to a legacy source reference. No net-new greenfield business
rules were introduced during this extraction. (The security hardening for BR-CATOPT-026 is recorded as a
finding/recommendation, not asserted as a new rule.)

## Tax
No tax logic in this service — prices are stored and computed tax-exclusive; tax is applied downstream by
the tax/order services. `product.tax_class_id` is retained as a reference id only. Recorded as a flag, no BR.

## Endpoint coverage
Every business operation (create/save/delete/move/attach/price/review) maps to an endpoint in
03-api-design.md and 04-api-contract.yaml with its driving BR-IDs listed. Pure list/get-by-id endpoints are
marked CRUD.

## Files delivered
INDEX.md · 00-component-inventory.md · 01-business-rules.md · 02-domain-model.md · 03-api-design.md ·
04-api-contract.yaml · 06-completion-summary.md · extraction-evidence.md · FINAL-EXTRACTION-COMPLETE.md
(05-dependencies.md intentionally deferred to Stage 1.5.)
