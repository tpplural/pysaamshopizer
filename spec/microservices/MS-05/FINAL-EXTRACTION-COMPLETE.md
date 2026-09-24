# MS-05 Customer Service — FINAL EXTRACTION COMPLETE

**Service ID**: MS-05 · **Mode**: Direct Source · **Status**: 🟢 Extraction complete (Phase 4)

## Final Counts (authoritative — match file content)

| Artifact | Count |
|----------|-------|
| Business rules | 43 |
| — BR-CUST-001..028 | 28 |
| — BR-CUSTOPT-001..015 | 15 |
| Owned tables | 8 |
| API endpoints (operations) | 30 |
| Data invariants | 13 |
| Source files read | 24 |

## Deliverables (all present in spec/microservices/MS-05/)
- [x] INDEX.md
- [x] 00-component-inventory.md
- [x] 01-business-rules.md (43 rules, each with 8-dimension preservation table + concrete success/error example)
- [x] 02-domain-model.md (8 tables, customer state model, 13 invariants)
- [x] 03-api-design.md (30 endpoints)
- [x] 04-api-contract.yaml (OpenAPI 3.1, 30 operations, unique operationIds, all $refs resolve)
- [x] 06-completion-summary.md
- [x] extraction-evidence.md
- [x] FINAL-EXTRACTION-COMPLETE.md

*(05-dependencies.md intentionally NOT created — Stage 1.5 cross-service compilation.)*

## Net-new findings (deep read beyond Phase 1)
- BR-CUST-027 — gender silently defaults to Male when unset. **Modernization requirement recorded: default gender MUST be configurable, not hard-coded.**
- BR-CUST-028 — shopper hard-delete cascades to attributes in application code.
- BR-CUST-026 — REST create assigns ADMIN group (suspected defect, flagged for clarification).

## Greenfield rules
None — every rule traces to a read legacy source file.

## Not done here (by delegation)
- Graph import (Tracker step).
- Git commit (Tracker step).
