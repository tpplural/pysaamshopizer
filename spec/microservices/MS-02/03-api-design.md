# identity-admin (MS-02) — API Design

**Service ID**: MS-02 · **Port**: 8002 · **Base path**: `/api/v1/identity`
**Auth model (target)**: OIDC bearer tokens (ADR-004). Cross-cutting headers: `x-tenant-id` (store scope,
BR-SC-AUTHZ-001), `x-correlation-id`. Endpoint guards map to permission names (BR-SC-RBAC-002).

> Naming conventions (locked): JSON fields snake_case; URL paths kebab-case; enum values PascalCase.
> Every business endpoint below traces to at least one BR-ID (see Endpoint Coverage). CRUD-only endpoints
> are marked. The legacy `resetPassword`/`resetPasswordSecurityQtn` flow is modeled here for traceability;
> in the OIDC target it is realized by the provider (endpoints kept so the contract is complete and gaps
> are visible to Phase 4a).

## Endpoints

### Authentication & context

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | `/api/v1/identity/auth/login` | Authenticate an admin; returns authorities + login timestamps | BR-SC-AUTHN-001, -002, -004 |
| POST | `/api/v1/identity/auth/logout` | Terminate the session (access-denied also logs out) | BR-SC-AUTHN-005 |
| GET | `/api/v1/identity/context` | Resolve the active admin + active store for the request | BR-SC-AUTHZ-001, -002 |
| POST | `/api/v1/identity/bootstrap/default-admin` | Provision the default super-admin on a fresh install | BR-SC-AUTHN-006 |

### Menu

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| GET | `/api/v1/identity/menu` | Return the admin menu tree; optional authority filtering | BR-SC-AUTHZ-003, -004 |

### Admin users

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| GET | `/api/v1/identity/users` | List managed admins (scoped by super-admin; hides super-admins) | BR-SC-LSTUSR-001, -002 |
| GET | `/api/v1/identity/users/{id}` | Get one admin by id | CRUD — no BR-ID (read by id) |
| GET | `/api/v1/identity/users/by-username/{userName}` | Get one admin by login name (only if fully provisioned) | BR-SC-AUTHN-003 |
| GET | `/api/v1/identity/users/check-username` | Pre-check whether a login name is available | BR-SC-UNIQ-001 |
| POST | `/api/v1/identity/users` | Create an admin (groups, security answers, password rules, welcome email) | BR-SC-CREATE-001..006 |
| PUT | `/api/v1/identity/users/{id}` | Edit an admin (retain password, sticky SUPERADMIN, identity confirm) | BR-SC-EDIT-001, -002 |
| DELETE | `/api/v1/identity/users/{id}` | Delete an admin (authorization guard) | BR-SC-DELUSR-001, -002 |
| GET | `/api/v1/identity/users/{id}/effective-permissions` | Resolve a user's union of group permissions (+AUTH) | BR-SC-RBAC-001, BR-SC-AUTHN-002 |
| GET | `/api/v1/identity/users/{id}/authorization` | Test whether a user holds a given role | BR-SC-RBAC-002 |

### Self password change & reset

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| POST | `/api/v1/identity/users/me/password` | Change own password (current match, confirm, length, persist) | BR-SC-PWD-002, -003, -004 |
| POST | `/api/v1/identity/password-reset/questions` | Reset step 1: return security questions by username | BR-SC-RESET-001 |
| POST | `/api/v1/identity/password-reset/verify` | Reset step 2: verify security answers | BR-SC-RESET-002 |
| POST | `/api/v1/identity/password-reset/complete` | Reset step 3: set random temp password + email | BR-SC-RESET-003, -004 |

### Groups

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| GET | `/api/v1/identity/groups` | List groups (type filter; or all; or by granted permission) | BR-SC-RBAC-004, -005, -006 |
| GET | `/api/v1/identity/groups/{id}` | Get one group | CRUD — no BR-ID (read by id) |
| POST | `/api/v1/identity/groups` | Create a group | BR-SC-RBAC-003 (uniqueness) |
| DELETE | `/api/v1/identity/groups/{groupId}/permissions/{permissionId}` | Unlink one permission from a group | BR-SC-PERM-005 |

### Permissions

| Method | Endpoint | Description | Driven by |
|--------|----------|-------------|-----------|
| GET | `/api/v1/identity/permissions` | List/page permissions (optional group filter) | BR-SC-PERM-001, -002 |
| POST | `/api/v1/identity/permissions` | Create a permission | BR-SC-RBAC-003 (uniqueness) |
| DELETE | `/api/v1/identity/permissions/{id}` | Delete a permission (detach group links first) | BR-SC-PERM-004 |

## Endpoint Coverage

| Endpoint | Method | Status | Driving BR-IDs |
|----------|--------|--------|----------------|
| /auth/login | POST | COVERED | BR-SC-AUTHN-001/002/004 |
| /auth/logout | POST | COVERED | BR-SC-AUTHN-005 |
| /context | GET | COVERED | BR-SC-AUTHZ-001/002 |
| /bootstrap/default-admin | POST | COVERED | BR-SC-AUTHN-006 |
| /menu | GET | COVERED | BR-SC-AUTHZ-003/004 |
| /users | GET | COVERED | BR-SC-LSTUSR-001/002 |
| /users/{id} | GET | CRUD-ONLY | — |
| /users/by-username/{userName} | GET | COVERED | BR-SC-AUTHN-003 |
| /users/check-username | GET | COVERED | BR-SC-UNIQ-001 |
| /users | POST | COVERED | BR-SC-CREATE-001..006 |
| /users/{id} | PUT | COVERED | BR-SC-EDIT-001/002 |
| /users/{id} | DELETE | COVERED | BR-SC-DELUSR-001/002 |
| /users/{id}/effective-permissions | GET | COVERED | BR-SC-RBAC-001, BR-SC-AUTHN-002 |
| /users/{id}/authorization | GET | COVERED | BR-SC-RBAC-002 |
| /users/me/password | POST | COVERED | BR-SC-PWD-002/003/004 |
| /password-reset/questions | POST | COVERED | BR-SC-RESET-001 |
| /password-reset/verify | POST | COVERED | BR-SC-RESET-002 |
| /password-reset/complete | POST | COVERED | BR-SC-RESET-003/004 |
| /groups | GET | COVERED | BR-SC-RBAC-004/005/006 |
| /groups/{id} | GET | CRUD-ONLY | — |
| /groups | POST | COVERED | BR-SC-RBAC-003 |
| /groups/{groupId}/permissions/{permissionId} | DELETE | COVERED | BR-SC-PERM-005 |
| /permissions | GET | COVERED | BR-SC-PERM-001/002 |
| /permissions | POST | COVERED | BR-SC-RBAC-003 |
| /permissions/{id} | DELETE | COVERED | BR-SC-PERM-004 |

**Not carried forward:** legacy `GET /admin/permissions/permissions.html` (BR-SC-PERM-003 — "Not implemented"
dead screen) is intentionally omitted from the target contract.
