# identity-admin (MS-02) — Completion Summary

**Service ID**: MS-02 · **Priority**: 1 (Core) · **Analysis Mode**: Direct Source Read
**Status**: 🟢 Phase 4 extraction complete

## Counts (verified against file content)

| Artifact | Count |
|----------|-------|
| Business rules (BR-SC-*) | 43 |
| Semantic-preservation tables | 43 (1 per rule) |
| Concrete examples | 43 (≥1 success + ≥1 error each) |
| Tables (DDL) | 5 (`admin_user`, `sm_group`, `permission`, `user_group`, `permission_group`) |
| Data invariants (INV-SC-*) | 7 |
| Entity state machines | 1 (`admin_user`: Active↔Inactive) |
| API endpoints (03-api-design) | 25 (23 COVERED + 2 CRUD-only) |
| OpenAPI paths | 20 |
| OpenAPI schemas | 29 |
| Extension points (Layer B) | 3 |
| DB logic objects (Layer C) | 0 (app-tier only) |

## Rule count as a decomposition outcome (NOT a target)

43 rules = the 34 Phase-1 findings (BR-USER-001..034) **decomposed along behavioral seams**, not a
per-proc slice and not fitted to the "60-100 core" guide. Where P1 grouped several distinct behaviors under
one id, the deep read split them; where P1 over-split, the read merged. Concretely:

- **Split by behavioral seam:** P1 BR-USER-009 (single "password on save") → BR-SC-CREATE-005 (create:
  hash+store) + BR-SC-EDIT-002 (edit: retain+identity-confirm) — two genuinely different code paths and
  outcomes. P1 BR-USER-010..013 (change-password) → BR-SC-PWD-002 (authorize/current-match),
  BR-SC-PWD-003 (confirm+length), BR-SC-PWD-004 (persist) — validation vs authorization vs state-change are
  distinct seams. P1 BR-USER-015 → BR-SC-RESET-002 (answer verify) + BR-SC-RESET-003 (random-pw+email).
  P1 BR-USER-019/020 → BR-SC-DELUSR-001 (authorization guard) + BR-SC-DELUSR-002 (state change + missing
  target-guard defect). P1 BR-USER-031/032 → BR-SC-AUTHZ-003 (menu build/cache) + BR-SC-AUTHZ-004 (per-item
  role gate).
- **Merged where P1 over-counted:** the redundant six-term question-distinctness boolean is ONE rule
  (BR-SC-CREATE-003), not six; the sequential answer-blank checks are ONE rule (BR-SC-CREATE-002).
- **Model consolidation:** the two-hop RBAC (BR-USER-001) is stated once as BR-SC-RBAC-001 and referenced,
  not re-asserted per consumer.

### Net-new findings (produced by the deep read, absent from P1)

1. **BR-SC-RESET-004 (resolved from P1's "unknown"):** P1 flagged `UserReset.generateRandomString()` charset
   and length as out of scope. The deep read of `UserReset.java` establishes it: **10-char alphanumeric via
   `java.util.Random` (non-cryptographic)**, and an **off-by-range defect** — `getRandomNumber()` bounds on
   `CHAR_LIST.length()` (54) while indexing `CHAR_LIST_WITHNUM` (62), and returns `n-1`, so the last 8
   alphabet slots are never selected and index 0 is over-represented. This narrows reset-password entropy —
   a concrete security finding, not in P1.
2. **BR-SC-RBAC-005 (behavioral divergence made explicit):** the paged group table calls the untyped
   `list()` (ALL groups incl. CUSTOMER), diverging from the type-filtered picker (BR-SC-RBAC-004) — surfaced
   as its own rule with the missing-label tolerance path.
3. **BR-SC-AUTHN-006 (bootstrap made first-class):** `createDefaultAdmin` provisions the default super-admin
   with a shipped known password — captured as a rule with a fix-on-migration note (was only implicit in P1).

## Preserve-vs-Fix register (flagged for Phase 4a — decision D-06 style)

| Rule | Cross-ref | Issue | Preservation |
|------|-----------|-------|--------------|
| BR-SC-DELUSR-002 | BR-USER-020 | No target-is-superadmin guard on delete | FLAGGED |
| BR-SC-LSTUSR-002 | BR-USER-021 | Self-exclusion object-vs-string → always false | FLAGGED |
| BR-SC-PERM-005 | BR-USER-002 | removePermission never persists | OK (noted) |
| BR-SC-PWD-001 | BR-USER-023 | Unsalted SHA-1 (deprecated encoder) | OK (noted) |
| BR-SC-CREATE-006 | BR-USER-033 | Cleartext password in welcome email | OK (noted) |
| BR-SC-RESET-001 | BR-USER-014 | Unauthenticated + username enumeration | FLAGGED |
| BR-SC-RESET-003 | BR-USER-015 | Cleartext temp password in email | OK (noted) |
| BR-SC-RESET-004 | BR-USER-034 | Non-crypto RNG + index-range entropy defect | OK (noted) |

## Endpoint Coverage

See `03-api-design.md` — 23 of 25 endpoints are BR-driven; 2 (`GET /users/{id}`, `GET /groups/{id}`) are
CRUD-only read-by-id and marked as such. No UNCOVERED endpoints. The legacy "Not implemented" permissions
display screen (BR-SC-PERM-003) is intentionally not exposed as a target endpoint.

## Semantic Preservation

| Component | Flagged Dimensions | Status | Notes |
|-----------|--------------------|--------|-------|
| UserController | error-paths (self-exclusion, delete guard) | FLAGGED (preserved) | defects captured faithfully with PRESERVE-VS-FIX notes, not condensed away |
| PermissionServiceImpl | data-writes (removePermission non-persist) | OK (noted) | legacy non-persist documented |
| UserReset | constants (charset/bounds) | OK | net-new: full charset+defect captured |
| All other components | none | OK | source vs spec vectors balanced |

Two rules carry `Preservation: FLAGGED` because the legacy behavior is a **defect preserved as current
behavior** (self-exclusion ineffective; no superadmin-delete guard) — the flags mark them for 4a
disposition, they are not extraction gaps. All other 41 rules are `Preservation: OK`.

## Notes on target shape (ADR-004)

Credentials are not stored in the target (`idp_subject` replaces `ADMIN_PASSWORD`); the password and
security-question columns and their rules (BR-SC-PWD-*, BR-SC-RESET-*, BR-SC-CREATE-005/006) are documented
for traceability but realized by the OIDC provider. The two-hop RBAC model, per-store scoping, sticky
SUPERADMIN, login-timestamp stamping, and the data-driven menu are all carried into the target.
