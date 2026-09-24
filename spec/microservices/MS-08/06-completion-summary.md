# MS-08 Shipping Service — Completion Summary

**Service ID**: MS-08
**Port**: 8008
**Schema**: `shipping_schema`
**Target stack**: Python / FastAPI + PostgreSQL 15+
**Analysis mode**: Direct Source Read (no CAST)
**Status**: 🟢 Extraction complete · 🔵 Phase 4a reconciled (2026-09-20)

> **Phase 4a BA review (Mode A, human-approved 2026-09-20):** the 11 D-06 preserve-and-flag shipping
> quirks were NOT preserved. Human decision: drop the quirks. Reconciled as:
> - **Obsolete (dropped to `07-obsolete-rules-appendix.md`):** BR-SHIP-005 (dead null-branch),
>   BR-SHIP-027 (dead basis-type read). Active rule count **34 → 32**.
> - **Simplify / fix-on-migration (capability kept, defect removed):** BR-SHIP-006 (deterministic
>   ordering), BR-SHIP-010 (`>=` + exact decimals), BR-SHIP-016/017 (exact-decimal option selection),
>   BR-SHIP-019 (taxOnShipping propagation), BR-SHIP-021 (correct getter), BR-SHIP-022 (per-package qty=1),
>   BR-SHIP-025 (per-box weight/dims), BR-SHIP-030 (gate delete endpoint). These carry a `**4a Decision:**`
>   note in `01-business-rules.md` — the modernized service implements the CORRECT behavior, not the quirk.
>
> Counts below reflect the ORIGINAL extraction (34). Post-4a active scope is **32 rules** (2 obsolete).

## Counts (verified against file content)

| Artifact | Count |
|----------|-------|
| Business rules — original extraction (`### BR-` headers) | 34 |
| Business rules — post-4a active scope | 32 (2 dropped: BR-SHIP-005, BR-SHIP-027) |
| Rule group | 1 (BR-SHIP, contiguous 001..034) |
| Owned relational tables (CREATE TABLE in 02-domain-model.md) | 4 |
| Data invariants (INV- rows in 02-domain-model.md) | 9 |
| API endpoints (rows in 03-api-design.md = operations in 04-api-contract.yaml) | 20 |
| Extension points | 2 (EXT-SHIP-001 quote provider SPI, EXT-SHIP-002 packaging SPI) |

## Rule count as a decomposition outcome (NOT a target)

34 rules = 8 rule-bearing source components decomposed along behavioral seams:
- `ShippingServiceImpl` (quote orchestrator) → 20 rules (BR-SHIP-001..019, 031) split along the pipeline's
  distinct behavioral seams: config load, country-eligibility gates (national vs international), module
  selection (active + region-eligible), order-total calculation, package-strategy routing, free-shipping
  gate, handling/tax propagation, provider-invocation error path, null-result handling, price-text
  formatting, option-name defaulting, HIGHEST vs LEAST/ALL selection, list-collapse, summary assembly,
  and provider-save validation.
- `DefaultPackagingImpl` → 6 rules (BR-SHIP-020..025): virtual exclusion, dimension/weight defaulting +
  attribute accumulation, per-item explosion, box-config validation, per-product fit validation, bin-packing.
- `CustomWeightBasedShippingQuote` → 4 rules (BR-SHIP-026..029): config load, region eligibility, weight
  sum, bracket lookup.
- 5 controllers → 4 authoring/authorization rules (BR-SHIP-030, 032, 033, 034), merging sibling
  validation checks into per-purpose rules rather than one-rule-per-check.

This is a 1:1 alignment with the Phase-1 catalog (P1 also produced 34 BR-SHIP rules); the Phase-4 deep read
CONFIRMED the P1 grouping was already faithful and did not fragment or inflate it.

### Net-new findings from the deep read (beyond P1 restatement)

The deep read confirmed and sharpened several defects/quirks that P1 flagged only as clarification items;
these are now embedded as preserved-and-flagged behavior in the rules (not just questions):

1. **BR-SHIP-025** — box-packing output loop uses the stale last-`box` weight for EVERY emitted package
   AND the configured box height/length/width for every package (confirmed by reading the output loop:
   `details.setShippingWeight(weight + box.getWeight())` with `box` being the last-created reference, and
   `setShippingHeight(height)` using config dims). Genuine defect, preserved.
2. **BR-SHIP-021** — per-item path guards on `getAttributeAdditionalWeight()` but adds
   `getProductAttributeWeight()` (mismatched getter). Confirmed copy-paste defect, preserved.
3. **BR-SHIP-027** — `CustomWeightBasedShippingQuote` reads `shippingConfiguration.getShippingBasisType()`
   into a local and never uses it (dead read). Confirmed, preserved.
4. **BR-SHIP-030** — `ShippingMethodsController.deleteShippingMethod` has NO `@PreAuthorize` while every
   sibling endpoint does (authorization gap). Confirmed by reading the annotation set.
5. **BR-SHIP-016/017** — option price comparison uses `.longValue()` (whole-unit truncation, cents ignored)
   and LEAST/ALL selection bodies are byte-identical. Confirmed, preserved.

## Endpoint Coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /quotes | POST | COVERED | BR-SHIP-002..018, 026..029 |
| /summary | POST | COVERED | BR-SHIP-019 |
| /packages | POST | COVERED | BR-SHIP-009, 020..025 |
| /requires-shipping | POST | COVERED | BR-SHIP-020 |
| /configuration | GET | COVERED | BR-SHIP-001 |
| /configuration | PUT | COVERED | BR-SHIP-001, 030 |
| /options | PUT | COVERED | BR-SHIP-033, 030 |
| /packaging | PUT | COVERED | BR-SHIP-034, 030 |
| /supported-countries | GET | COVERED | BR-SHIP-004 |
| /supported-countries | PUT | COVERED | BR-SHIP-004, 030 |
| /methods | GET | COVERED | BR-SHIP-007 |
| /providers | PUT | COVERED | BR-SHIP-031, 030 |
| /providers/{moduleCode} | DELETE | COVERED | BR-SHIP-030 (flagged), 031 |
| /providers/weight-based/configuration | GET | COVERED | BR-SHIP-026 |
| /providers/weight-based/regions | POST | COVERED | BR-SHIP-032, 030 |
| /providers/weight-based/regions/{regionName} | DELETE | COVERED | BR-SHIP-032, 030 |
| /providers/weight-based/regions/{regionName}/countries | POST | COVERED | BR-SHIP-032, 030 |
| /providers/weight-based/regions/{regionName}/countries/{countryCode} | DELETE | COVERED | BR-SHIP-032, 030 |
| /providers/weight-based/regions/{regionName}/prices | POST | COVERED | BR-SHIP-032, 030 |
| /providers/weight-based/regions/{regionName}/prices/{maximumWeight} | DELETE | COVERED | BR-SHIP-032, 030 |

## Semantic Preservation

| Source Component | Flagged Dimensions | Status | Notes |
|-----------------|-------------------|--------|-------|
| ShippingServiceImpl | none (business dims OK) | OK | free-shipping strict-`>`/double, longValue truncation, LEAST=ALL preserved as flagged behavior in rules |
| DefaultPackagingImpl | none | OK (with preserved defects) | stale-box output weight + ITEM getter mismatch preserved & flagged |
| CustomWeightBasedShippingQuote | none | OK | dead shippingBasisType read preserved & flagged |
| Controllers | none | OK | authoring validators merged per purpose |

All 34 rules carry a full 8-dimension Semantic Preservation table. No CRITICAL (source>0, spec==0)
dimension. Flagged rules are quirk/defect preservations (D-06), not condensation.

## Extension Points (Layer B)

| EXT-ID | Mechanism | What varies |
|--------|-----------|-------------|
| EXT-SHIP-001 | plug-in provider (quote SPI) | Which quote engine runs (weightBased / external carriers / future); resolved by first active configured provider (BR-SHIP-006) |
| EXT-SHIP-002 | plug-in packaging strategy | Box vs per-item packaging engine (BR-SHIP-009) |

External carrier gateways (UPS/USPS/CanadaPost) plug into EXT-SHIP-001 and are OUT OF SCOPE (documented in
00-component-inventory.md).

## Preserved-and-flagged quirks (D-06 register)

| Rule | Quirk |
|------|-------|
| BR-SHIP-005 | Dead null-branch (module map never null) |
| BR-SHIP-006 | Non-deterministic first-active-module selection (unordered map) |
| BR-SHIP-010 | Free shipping strict-`>` threshold + floating-point comparison |
| BR-SHIP-016/017 | Whole-unit price truncation; LEAST and ALL selection identical |
| BR-SHIP-019 | Summary taxOnShipping never populated |
| BR-SHIP-021 | ITEM-path attribute-weight getter mismatch |
| BR-SHIP-022 | Per-package quantity set to full line quantity |
| BR-SHIP-025 | Stale last-box weight + config dims used for every emitted package |
| BR-SHIP-027 | Unused shippingBasisType read |
| BR-SHIP-030 | deleteShippingMethod lacks role guard |

## Greenfield rules

None. All 34 rules trace to legacy source.

## Dependencies (informational — 05-dependencies.md generated in Stage 1.5)

- Callers: order (MS-09) at checkout, cart (MS-06) for shipping eligibility.
- Reads (caller-supplied / other services): catalog/pricing (MS-04) for product weight/dimensions/virtual
  flags and final price; reference data (MS-01) for country names; store (MS-03) for store country.
- Side-effect: merchant operational log (system/logging).
