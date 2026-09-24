# Dependencies: identity-admin (MS-02)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-02 is the SOURCE + documented domain events.

## Services Consumed

**This service has no external dependencies.** identity-admin authenticates administrators and manages
admin users / groups / permissions. Authentication itself is delegated to the external OIDC provider
(ADR-004) — the OIDC provider is infrastructure, not a SAAM microservice, so it is not modeled as a
`CALLS` edge. identity-admin has **no outgoing `CALLS` edges** to any of the other ten services; all
operations complete within its own database.

## Events Published

None. identity-admin does not publish domain events.

## Events Consumed

- **`merchant.deleted`** (from MS-03 merchant-store) — listed by MS-03's decommission rule
  (BR-MS-LIFE-002) among the fan-out consumers. If admin users are store-scoped in the target,
  identity-admin removes the store's admin memberships on this event. This is an inbound event,
  not an outgoing call. (Recorded for completeness; see `spec/shared/event-schemas/index.md`.)

## Reconciliation (integration dimension)

- specIntegrations written into this file (outbound sync calls): **0**
- Integration count implied by MS-02 rules (Logic / Side Effects "Calls"/"Publishes"): **0**
  (auth is delegated to OIDC infrastructure, not a SAAM service call)
- **Status: MATCH** — self-contained service, zero outgoing integrations as expected.
