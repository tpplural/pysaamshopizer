# Dependencies: content-cms (MS-11)

> **Generated in Phase 4 Stage 1.5** (Cross-Service Dependency Compilation).
> Source: the graph's `CALLS` edges where MS-11 is the SOURCE + documented domain events.

## Services Consumed

### catalog (MS-04) — ⚠️ EDGE PRESENT IN GRAPH BUT NOT BACKED BY A RULE (see GAPS)

The graph carries a `CALLS` edge MS-11 → MS-04. No content-cms rule makes such a call. content-cms is a
**pure inbound byte provider** (BV-5): MS-03 and MS-04 call INTO it to store logo / product-image /
digital-file bytes; content-cms owns the object store and the CMS content rows and does not call out.

The likely origin of the edge is the legacy `LandingController` featured-items path (fetching featured
product items from catalog for the storefront landing page). That composition concern was **scoped OUT**
of MS-11 — BR-CMS-023 / BR-CMS-024 only render the landing SECTION content (`code = LANDING_PAGE`) that
content-cms itself owns; there is no featured-product fetch. **No synchronous call to catalog is
modeled.** See GAPS.

**content-cms has no active outgoing dependencies.** All operations (content pages/boxes, landing,
files/images/logos) complete within its own database and object store.

## Events Published

None. content-cms does not publish domain events.

## Events Consumed

- **`merchant.deleted`** (from MS-03) — content-cms owns store-scoped content rows and the store's blob
  namespace; on store decommission it purges that store's content and objects (BR-MS-LIFE-002 fan-out
  consumer). Inbound event, not an outgoing call.

## Reconciliation (integration dimension)

- specIntegrations written into this file (active outbound sync calls): **0**
- Integration count implied by MS-11 rules: **0** (inbound-only byte provider; BR-CMS-020 etc. describe MS-03/MS-04 as inbound callers)
- **Status: MATCH on the rules (0 = 0); MISMATCH vs the graph** — the MS-11 → MS-04 edge has no backing rule.

## GAPS

1. **MS-11 → MS-04 (catalog) edge is spurious / scoped-out.** The legacy `LandingController`
   featured-items composition was excluded from MS-11's scope; content-cms owns only content bytes/rows
   and landing SECTION content, and calls nothing. **Action:** human / Phase-2 to remove the edge (or,
   if storefront featured-items composition is later re-scoped in, add the backing rule + endpoint
   FIRST). Do NOT fabricate a call. **Status: GAP.**
