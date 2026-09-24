# Dependencies: tax (MS-07)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-07 is the SOURCE + documented domain events.

## Services Consumed

### reference-data (MS-01) — sync REST  ⚠️ NOT BACKED BY A RULE (see GAPS)

The graph carries a `CALLS` edge MS-07 → MS-01. However, tax is a **stateless calculator invoked BY
the order service (MS-09)**: the jurisdiction country / zone / state that drives rate selection arrive
**in the request payload** (`TaxCalculationRequest.customer.billing` / `.delivery` — `country_id`,
`zone_id`, `state`), not from a reference-data lookup. No tax rule (BR-TAX-*) performs a cross-service
read against reference-data; jurisdiction codes are treated as inputs.

**Therefore tax makes NO synchronous call to reference-data in this design.** The graph edge is
**spurious** for MS-07 and is flagged in GAPS. Should the target choose to *validate* an inbound
`country_id`/`zone_id` against the kernel, it would be:

- **Would-be call:** GET `/api/v1/reference/zones/{code}` (`getZone`) / `/api/v1/reference/countries/{isoCode}` (`getCountry`)
- **Status:** NOT MODELED as an active dependency — no BR-ID backs it (codes are request inputs).

## Events Published

None. tax does not publish domain events. It is a synchronous calculator only.

## Events Consumed

- **`merchant.deleted`** (from MS-03) — tax owns store-scoped tax classes / tax rates / tax
  configuration, so on store decommission it purges that store's tax data (BR-MS-LIFE-002 fan-out
  consumer). Inbound event, not an outgoing call.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync calls): **0**
- Integration count implied by MS-07 rules: **0** (jurisdiction codes are request inputs; no cross-service read)
- **Status: MATCH on the rules (0 = 0), but MISMATCH vs the graph** — the graph shows an MS-07 → MS-01
  edge with no backing rule.

## GAPS

1. **MS-07 → MS-01 (reference-data) edge is spurious.** No tax rule performs a reference-data read;
   jurisdiction (`country_id`, `zone_id`, `state`) arrives in the `POST /calculate` request from MS-09.
   **Action:** human / Phase-2 to remove the edge, OR confirm that inbound-code validation against the
   kernel is desired (then add a validation BR-ID). Do NOT fabricate a call. **Status: GAP.**
