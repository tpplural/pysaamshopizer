# identity-admin (MS-02) — Spec Package Index

**Service ID**: MS-02 · **Name**: identity-admin · **Port**: 8002 · **Schema**: `identity_admin`
**Priority**: 1 (Core) · **Wave**: 0 · **Segment**: 12 (User/Admin & Security)
**Cross-ref**: BR-USER-001..034 → BR-SC-* · **Analysis mode**: Direct Source Read

## Purpose

Back-office (admin/staff) identity: users, groups, permissions, admin authentication and authorization,
per-store admin scoping, admin menu build, and password lifecycle. Owns the two-hop RBAC model
(User → Group → Permission) historically shared with the storefront. Per ADR-004 the target delegates
authentication to an OIDC provider (`idp_subject`, no stored credentials); legacy password rules are kept
documented for traceability.

## Files

| File | Contents |
|------|----------|
| `00-component-inventory.md` | Legacy components → target disposition; extensibility signals; Layer C (none) |
| `01-business-rules.md` | 43 rules (BR-SC-*) in 6 groups, each with 8-dim preservation table + concrete example |
| `02-domain-model.md` | Executable PostgreSQL DDL (5 tables), entity state model, 7 data invariants |
| `03-api-design.md` | 25 endpoints + endpoint-to-rule coverage |
| `04-api-contract.yaml` | OpenAPI 3.1 — 20 paths, 29 schemas (naming authority) |
| `06-completion-summary.md` | Counts, decomposition rationale, net-new findings, preserve-vs-fix register |
| `extraction-evidence.md` | Every source file read (26) with sections + rules |
| `FINAL-EXTRACTION-COMPLETE.md` | Completion marker |

> `05-dependencies.md` is produced in Stage 1.5 (cross-service compilation), not here.

## Rule groups

| Group | Rules | Theme |
|-------|-------|-------|
| BR-SC-RBAC | 6 | User→Group→Permission two-hop model; role=permission-name; data-driven roles; group typing |
| BR-SC-PERM | 5 | Permission listing/paging; permission-group association lifecycle |
| BR-SC-AUTHN | 6 | Admin authentication, AUTH grant, inner-join load gate, login timestamps, bootstrap |
| BR-SC-AUTHZ | 5 | Per-store scoping, session cache, config-driven menu + per-item role gate, pluggable provider |
| BR-SC-USR | 15 | User list/create/edit/delete; sticky SUPERADMIN; uniqueness |
| BR-SC-PWD | 6 | Self password change; 3-step security-question reset; temp-password generator |

## Key preserved behaviors

Two-hop RBAC (authorities = ⋃ group permissions + forced AUTH) · permission name IS the Spring role in
guards and menu gates · per-store admin scoping via the user's store · SUPERADMIN sticky on self-edit but
deletable (flagged) · login-timestamp stamping · answer-based reset · config-driven menu.
