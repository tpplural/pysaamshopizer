# Dependencies: reference-data (MS-01)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-01 is the SOURCE + documented domain events.

## Services Consumed

**This service has no external dependencies.** reference-data is a pure read-only leaf provider
(the shared kernel, ADR-006): it serves country / zone / currency / language / calendar lookups to
every other service and calls no other service. All operations complete within its own database and
in-memory caches. It has **no outgoing `CALLS` edges** in the graph.

## Events Published

None. reference-data does not publish domain events.

## Events Consumed

- **`merchant.deleted`** (from MS-03 merchant-store) — reference-data is a global (non-store-scoped)
  kernel and owns no store-scoped aggregates, so it is **not** a functional consumer of the
  store-decommission fan-out. No handler is required here. (Recorded for completeness; see
  `spec/shared/event-schemas/index.md`.)

## Reconciliation (integration dimension)

- specIntegrations written into this file (outbound sync calls): **0**
- Integration count implied by MS-01 rules (Logic / Side Effects "Calls"/"Publishes"): **0**
  (reference-data rules are pure lookups/derivations with no cross-service call)
- **Status: MATCH** — leaf provider, zero outgoing integrations as expected.
