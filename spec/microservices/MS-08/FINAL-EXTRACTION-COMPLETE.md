# MS-08 Shipping Service — FINAL EXTRACTION COMPLETE

**Service ID**: MS-08
**Status**: 🟢 Extraction complete (Direct Source Read, no CAST)

## Verified Counts

| Metric | Value |
|--------|-------|
| Business rules (`### BR-` headers) | 34 (BR-SHIP-001..034) |
| Owned relational tables (CREATE TABLE) | 4 |
| Data invariants (INV-SHIP rows) | 9 |
| API endpoints / OpenAPI operations | 20 |
| Extension points | 2 |
| Greenfield rules | 0 |

All counts are consistent across INDEX.md, 06-completion-summary.md, 02-domain-model.md,
03-api-design.md, 04-api-contract.yaml, and this file.

## Coverage

- **Quote pipeline** (getShippingQuote): fully covered — config load, country-eligibility gates, module
  selection (active + region-eligible), order total, package strategy, free shipping, handling/tax,
  provider invocation + error path, null-result handling, price-text/name, price selection, list collapse
  (BR-SHIP-001..018, plus 026..029 for the weight-based provider).
- **Packaging** (box bin-packing + per-item): fully covered with explicit formulas (BR-SHIP-020..025).
- **Custom weight-based quote** (region → weight-sum → bracket): fully covered with explicit formula
  (BR-SHIP-026..029).
- **SPI / extension point**: quote provider (EXT-SHIP-001) and packaging (EXT-SHIP-002) modelled;
  external carriers documented out of scope.
- **Admin authoring**: config mode, options, packaging, supported countries, providers, weight-based
  regions/countries/prices (BR-SHIP-030..034).

## Preserved-and-flagged quirks (D-06)

BR-SHIP-005 (dead branch), 006 (non-deterministic selection), 010 (strict-`>`/double), 016/017
(whole-unit truncation, LEAST=ALL), 019 (taxOnShipping gap), 021 (getter mismatch), 022 (per-package
quantity), 025 (stale-box weight + config dims), 027 (dead read), 030 (missing role guard).

## Not done here (per instructions)

- Graph import NOT run.
- Git commit NOT performed.
- 05-dependencies.md NOT produced (Stage 1.5 artifact).

Ready for validation (Subagent C).
