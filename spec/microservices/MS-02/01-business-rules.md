# identity-admin (MS-02) — Business Rules

**Service ID**: MS-02
**Version**: 1.0
**Status**: 🟢 Extraction complete (Phase 4)
**Analysis Mode**: Direct Source Read (no CAST)
**Legacy**: Shopizer 2.0.1 — Java / Spring MVC 3.1 + Spring Security 3.1, schema `SALESMANAGER`
**Domain code**: `SC` (Security / identity). Every rule cross-references its Phase-1 origin id `BR-USER-*`.

> Scope: back-office (admin/staff) identity — users, groups, permissions, admin authentication and
> authorization, per-store admin scoping, admin menu build, password lifecycle. Storefront (customer)
> identity is MS-05. The `Group`/`Permission` two-hop RBAC model is historically shared between admin and
> customer via `GroupType {ADMIN, CUSTOMER}`; MS-02 owns that model and exposes it (ADR-004: authn is
> delegated to OIDC in the target — credentials are no longer stored, `idp_subject` replaces the hash;
> legacy password rules are preserved below for traceability and flagged as fix-on-migration).

## Preserve-vs-Fix register (carried to Phase 4a)

These rules capture **current legacy behavior faithfully** but are known defects / security debt. They are
documented as-is with a `PRESERVE-VS-FIX` note; the human decides disposition at 4a (decision D-06 style).

| Rule | Cross-ref | Issue | Disposition proposal |
|------|-----------|-------|----------------------|
| BR-SC-DELUSR-002 | BR-USER-020 | No target-is-superadmin guard on user delete | FIX (add target guard) |
| BR-SC-LSTUSR-002 | BR-USER-021 | Self-exclusion compares `User` to `String` → always false (self never hidden) | FIX (compare adminName) |
| BR-SC-PERM-005 | BR-USER-002 | `removePermission` mutates collection, never persists | FIX (persist) or remove dead method |
| BR-SC-PWD-001 | BR-USER-023 | Unsalted SHA-1 password hash (deprecated encoder) | FIX (OIDC / bcrypt — ADR-004) |
| BR-SC-CREATE-006 | BR-USER-033 | New-user welcome email carries plaintext password | FIX (no cleartext creds) |
| BR-SC-RESET-003 | BR-USER-015 | Reset emails a plaintext temporary password | FIX (reset link, not password) |
| BR-SC-RESET-001 | BR-USER-014 | Unauthenticated reset endpoint enumerates whether a username exists | FIX (uniform response) |
| BR-SC-RESET-004 | BR-USER-034 | Temp-password generator uses `java.util.Random` + index-range defect | FIX (SecureRandom, correct charset) |

---

## Group: BR-SC-RBAC — RBAC model (User → Group → Permission)

### BR-SC-RBAC-001: A user's authority comes only through group membership (two-hop RBAC)

**Source Reference:** `User.java:60-77` (groups ManyToMany join USER_GROUP); `Permission.java:57-72` (groups ManyToMany join PERMISSION_GROUP, owning side); `Group.java:58-59` (permissions mappedBy groups)
**Cross-Reference:** `UserServicesImpl.java:loadUserByUsername:78-92`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-001

**Statement:** An administrator holds a permission only by being a member of one or more groups that carry that permission. There is no direct user-to-permission grant; a user's effective permission set is the union of the permissions of all groups the user belongs to.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
user --(USER_GROUP)--> group --(PERMISSION_GROUP)--> permission
effective_permissions(user) = UNION over user.groups of group.permissions
// membership rows are insert/delete only (both join FK columns updatable=false); never updated in place
```

**Data Dependencies:**
- Reads: user↔group membership, group↔permission grants
- Writes: none (model invariant)

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 5 | 5 | OK |
| Constants | 1 | 1 | OK (join-table shape) |
| State transitions | 1 | 1 | OK (membership insert/delete only) |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/users/42/effective-permissions` (user 42 is in group "Store Admins" which carries STORE_ADMIN, PRODUCTS)
- Success: `200 {"userId":42,"permissions":["AUTH","STORE_ADMIN","PRODUCTS"]}`
- Error Input: `GET /api/v1/identity/users/9999/effective-permissions` (no such user)
- Error Output: `404 {"error":"NotFound","message":"User 9999 not found"}`

### BR-SC-RBAC-002: A permission name IS the authority string checked by role guards

**Source Reference:** `UserServicesImpl.java:loadUserByUsername:84-88`; `PermissionDaoImpl.java:getPermissionsListByGroups:50-64`
**Cross-Reference:** `shopizer-security.xml:intercept-url` (hasRole('AUTH')); UserController `@PreAuthorize("hasRole('STORE_ADMIN')")`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-026

**Statement:** The name of a permission is the exact role string that authorization guards test. A user passes a role check for a given role name if and only if one of the user's groups carries a permission whose name equals that role name. Role names used in endpoint guards and menu gates are permission names, not group names.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
groupIds = [g.id for g in user.groups]
permissions = select distinct p join p.groups grp where grp.id in (:groupIds)
grantedAuthorities = { p.permissionName for p in permissions } (+ AUTH, see BR-SC-AUTHN-002)
hasRole(R) == R in grantedAuthorities
```

**Data Dependencies:**
- Reads: group→permission grants, permission names
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (loop over permissions) |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (Spring Security authority mapping) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/users/42/authorization?role=STORE_ADMIN`
- Success: `200 {"role":"STORE_ADMIN","granted":true}`
- Error Input: `GET /api/v1/identity/users/42/authorization?role=` (blank role)
- Error Output: `400 {"error":"BadRequest","message":"role query parameter is required"}`

### BR-SC-RBAC-003: New permission and group names are data, not code (data-driven RBAC)

**Source Reference:** `Permission.java:53-55` (PERMISSION_NAME unique); `Group.java:50-52` (GROUP_NAME unique)
**Cross-Reference:** `PermissionServiceImpl.java:listPermission`; `GroupServiceImpl.java:listGroup`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-001 (Extensibility Signal — Layer B)

**Statement:** Roles and permissions are configuration data (rows), not compiled constants. Adding a new permission name creates a new authority that role guards and menu gates can immediately reference, with no code change. Permission names are unique and group names are unique across the system.
**Intent:** Validation
**Weight:** Critical
**Extension Point:** EXT-SC-001 (data-driven RBAC — see spec/shared/extensibility-model.md, compiled Stage 1.8)

**Logic:**
```
PERMISSION.permissionName UNIQUE  // adding a row = adding an authority
SM_GROUP.groupName UNIQUE
// a menu item or endpoint guard references a permission by name; resolution is by data lookup
```

**Data Dependencies:**
- Reads: permission names, group names
- Writes: permission row create, group row create (generic CRUD)

**Side Effects:** none beyond the row write

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK (permission/group create) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (uniqueness conflict) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/permissions {"permissionName":"REPORTS"}`
- Success: `201 {"id":91,"permissionName":"REPORTS"}`
- Error Input: `POST /api/v1/identity/permissions {"permissionName":"AUTH"}` (already exists)
- Error Output: `409 {"error":"Conflict","message":"Permission name AUTH already exists"}`

### BR-SC-RBAC-004: Groups are typed ADMIN or CUSTOMER; admin lists show only ADMIN groups

**Source Reference:** `Group.java:46-48` (GROUP_TYPE enum STRING); `GroupDaoImpl.java:listGroup:70-80`; `GroupType.java:3` (ADMIN, CUSTOMER)
**Cross-Reference:** `GroupsController.java:displayGroups:78-84`; `SecurityController.java:displayGroups:43-49`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-022

**Statement:** Every group is classified as either an administrator group or a customer group. Back-office group listings and the assignable-groups picker present only administrator groups, ordered by creation sequence.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
group.groupType in { ADMIN, CUSTOMER }
listGroup(ADMIN): select g where g.groupType = ADMIN order by g.id asc
// NOTE the paged AJAX table (pageGroups) calls list() with NO type filter → shows CUSTOMER groups too (BR-SC-RBAC-005)
```

**Data Dependencies:**
- Reads: group type, group name
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (type filter) |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (ADMIN, CUSTOMER) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/groups?type=ADMIN`
- Success: `200 {"items":[{"id":1,"groupName":"SUPERADMIN","groupType":"ADMIN"},{"id":2,"groupName":"ADMIN","groupType":"ADMIN"}]}`
- Error Input: `GET /api/v1/identity/groups?type=STAFF` (invalid enum)
- Error Output: `400 {"error":"BadRequest","message":"type must be ADMIN or CUSTOMER"}`

### BR-SC-RBAC-005: The paged group table lists all groups regardless of type

**Source Reference:** `GroupsController.java:pageGroups:90-121` (`groupService.list()` — no type filter)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-022 (note)

**Statement:** The paginated group management table returns every group, including customer groups, in contrast to the type-filtered group picker. Each row is decorated with a localized description looked up by a naming convention keyed on the group name; a missing description label is tolerated and logged, not fatal.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
groups = list()   // ALL groups, no groupType filter (differs from BR-SC-RBAC-004)
for g in groups:
   descriptionKey = "security.group.description." + g.groupName
   try description = messages(descriptionKey) catch → log, omit description
```

**Data Dependencies:**
- Reads: all groups, localized labels
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (loop + label try/catch) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (label-key prefix) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (missing-label tolerated) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/groups?page=1&pageSize=20` (no type filter)
- Success: `200 {"items":[{"id":2,"groupName":"ADMIN","description":"Store administrator"},{"id":5,"groupName":"CUSTOMER","description":null}],"pagination":{"page":1,"pageSize":20,"totalItems":6,"totalPages":1}}`
- Error Input: `GET /api/v1/identity/groups?page=-1`
- Error Output: `400 {"error":"BadRequest","message":"page must be >= 1"}`

### BR-SC-RBAC-006: Groups carrying a set of permissions can be listed by those permission ids

**Source Reference:** `GroupDaoImpl.java:getGroupsListBypermissions:22-40`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-022 (data access)

**Statement:** Given a set of permissions, the system can list the groups that grant any of those permissions. This is the reverse lookup of the two-hop model and supports permission-impact analysis.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
select g from Group g join fetch g.permissions perms where perms.id in (:permissionIds)
```

**Data Dependencies:**
- Reads: group→permission grants
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/groups?grantsPermissionId=7`
- Success: `200 {"items":[{"id":2,"groupName":"ADMIN"}]}`
- Error Input: `GET /api/v1/identity/groups?grantsPermissionId=abc`
- Error Output: `400 {"error":"BadRequest","message":"grantsPermissionId must be an integer"}`

---

## Group: BR-SC-PERM — Permission listing & group-association lifecycle

### BR-SC-PERM-001: Permissions can be filtered and paged by owning group

**Source Reference:** `PermissionDaoImpl.java:listByCriteria:67-140`
**Cross-Reference:** `PermissionServiceImpl.java:listByCriteria:76-80`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-026 (data access), BR-USER-002 note

**Statement:** Permissions can be listed with optional filtering to only those granted to a given set of groups, and the result is paginated. When a group filter is supplied the count and page query both restrict to permissions linked to those groups; the total count is computed first and an empty result short-circuits.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
count = select count(p) [INNER JOIN p.groups grp where grp.id in (:groupIds) if groupIds present]
if count == 0 → return empty list with totalCount 0
page = select p join fetch p.groups grp [where grp.id in (:groupIds)] order by p.id asc
if maxCount > 0: firstResult = startIndex; maxResults = min(maxCount, count)
```

**Data Dependencies:**
- Reads: permissions, group→permission grants
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 7 | 6 | OK (paging/branch guards; 1 duplicate count-guard merged) |
| Data-flow | 4 | 4 | OK |
| Constants | 1 | 1 | OK (order-by id) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (empty vs paged) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/permissions?groupId=2&page=1&pageSize=10`
- Success: `200 {"items":[{"id":3,"permissionName":"STORE_ADMIN"},{"id":7,"permissionName":"PRODUCTS"}],"pagination":{"page":1,"pageSize":10,"totalItems":2,"totalPages":1}}`
- Error Input: `GET /api/v1/identity/permissions?groupId=99999&page=1` (group with no permissions)
- Error Output: `200 {"items":[],"pagination":{"page":1,"pageSize":10,"totalItems":0,"totalPages":0}}`

### BR-SC-PERM-002: All permissions are listed ordered by creation sequence

**Source Reference:** `PermissionDaoImpl.java:listPermission:23-33`; `PermissionController.java:pagePermissions:62-90`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-026 (data access)

**Statement:** The full catalog of permissions is returned ordered by the order in which they were created, each carrying its id and role name.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
select distinct p from Permission p order by p.id asc
```

**Data Dependencies:**
- Reads: permissions
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (result loop) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (order-by id) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (failure → error status) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/permissions`
- Success: `200 {"items":[{"id":1,"permissionName":"AUTH"},{"id":2,"permissionName":"SUPERADMIN"},{"id":3,"permissionName":"STORE_ADMIN"}]}`
- Error Input: `GET /api/v1/identity/permissions` (backing store unavailable)
- Error Output: `500 {"error":"InternalError","message":"Unable to list permissions"}`

### BR-SC-PERM-003: The interactive permissions display screen is intentionally unavailable

**Source Reference:** `PermissionController.java:displayPermissions:51-59` (`throw new Exception("Not implemented")`)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-022 (note — permissions display not implemented)

**Statement:** The standalone permissions display page is not implemented in the legacy system and fails when requested; only the paged permissions data feed is functional. This is preserved as a known non-feature, not carried forward as a target endpoint.
**Intent:** Routing
**Weight:** Critical
**PRESERVE-VS-FIX:** Legacy dead screen. Target: omit the endpoint (data feed via BR-SC-PERM-002 is sufficient). No target contract path.

**Logic:**
```
displayPermissions() → throw Exception("Not implemented")   // never renders
```

**Data Dependencies:**
- Reads: none
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 0 | 0 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (always throws) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: (legacy) `GET /admin/permissions/permissions.html`
- Success: none — endpoint always errors by design
- Error Input: any request
- Error Output: `500 Not implemented` (legacy). Target: endpoint not exposed.

### BR-SC-PERM-004: Deleting a permission first detaches it from all groups, then removes it

**Source Reference:** `PermissionServiceImpl.java:deletePermission:59-65`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-003

**Statement:** When a permission is deleted, its links to every group are removed first, and then the permission itself is removed. Re-loading the permission before deletion is required so the removal operates on a currently managed record.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
permission = getById(permission.id)   // re-attach to avoid detached-entity error
permission.setGroups(null)            // drop all PERMISSION_GROUP links
delete(permission)                    // remove PERMISSION row
```

**Data Dependencies:**
- Reads: permission by id
- Writes: group→permission links removed, permission removed

**Side Effects:** deletes the permission's group associations and the permission record

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 2 | 2 | OK (detach → delete) |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK (links + row) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (not found) |

**Preservation:** OK

**Concrete Example:**
- Input: `DELETE /api/v1/identity/permissions/7`
- Success: `204` (permission 7 and its group links removed)
- Error Input: `DELETE /api/v1/identity/permissions/9999` (not found)
- Error Output: `404 {"error":"NotFound","message":"Permission 9999 not found"}`

### BR-SC-PERM-005: Removing a permission from one group detaches the link only for that group

**Source Reference:** `PermissionServiceImpl.java:removePermission:82-88`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-002

**Statement:** Removing a permission from a specific group breaks only the association between that permission and that group; the permission itself and its links to other groups remain. In the legacy code this operation mutates the in-memory association set but issues no explicit persist, so the change relies on the surrounding transaction to flush — unlike permission deletion, which persists explicitly.
**Intent:** State Transition
**Weight:** Critical
**PRESERVE-VS-FIX:** Legacy defect — the method never explicitly persists (no save/flush), unlike deletePermission. Target: persist the detach explicitly (idempotent), or remove if the method proves unused.

**Logic:**
```
permission = getById(permission.id)          // re-attach
permission.getGroups().remove(group)         // mutate managed collection only
// NOTE: no save/flush in method body → persistence depends on ambient transaction
```

**Data Dependencies:**
- Reads: permission by id
- Writes: intended — remove one group→permission link (not explicitly flushed in legacy)

**Side Effects:** in legacy, none guaranteed persisted; target persists the single detach

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (single link detach) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (intended single link; legacy non-persist noted) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (not found) |

**Preservation:** OK (defect preserved as note)

**Concrete Example:**
- Input: `DELETE /api/v1/identity/groups/2/permissions/7` (unlink permission 7 from group 2)
- Success: `204` (link removed; permission 7 still exists and still linked to other groups)
- Error Input: `DELETE /api/v1/identity/groups/2/permissions/7` when no such link exists
- Error Output: `404 {"error":"NotFound","message":"Permission 7 is not granted to group 2"}`

---

## Group: BR-SC-AUTHN — Admin authentication

### BR-SC-AUTHN-001: Authentication loads the admin by username; unknown username fails login

**Source Reference:** `UserServicesImpl.java:loadUserByUsername:60-105`; `UserDaoImpl.java:getByUserName:20-40`
**Cross-Reference:** `shopizer-security.xml:authentication-manager userAuthenticationManager`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-024

**Statement:** Admin authentication resolves the account by its login name. If no account matches the submitted login name, authentication fails. A resolved account is admitted only if it is active; an inactive account cannot log in.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
user = getByUserName(userName)
if user == null → return null   // Spring treats null principal as authentication failure
principal.enabled = user.isActive()   // inactive admin → login denied
principal.password = user.adminPassword  // (legacy; ADR-004 removes stored credential)
```

**Data Dependencies:**
- Reads: admin account by login name, active flag
- Writes: none

**Side Effects:** none (timestamp stamping is BR-SC-AUTHN-004, on success)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (null-user, active) |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (loaded vs fail) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (Spring Security SPI) |
| Error paths | 2 | 2 | OK (unknown user, inactive) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/auth/login {"username":"admin","password":"password"}`
- Success: `200 {"authenticated":true,"userId":1,"authorities":["AUTH","SUPERADMIN","ADMIN"]}`
- Error Input: `POST /api/v1/identity/auth/login {"username":"ghost","password":"x"}`
- Error Output: `401 {"error":"Unauthorized","message":"Invalid credentials"}`

### BR-SC-AUTHN-002: Every authenticated admin is granted the base AUTH authority

**Source Reference:** `UserServicesImpl.java:loadUserByUsername:74-76` (`GrantedAuthorityImpl(PERMISSION_AUTHENTICATED)`); `Constants.java:44` (AUTH)
**Cross-Reference:** `shopizer-security.xml` (all /admin/** require hasRole('AUTH'))
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-025

**Statement:** Any successfully authenticated administrator automatically receives a baseline "authenticated" authority, independent of group membership. Access to the back-office as a whole is gated on this baseline authority, so no admin can reach any admin page without it.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
authorities = { "AUTH" }              // always granted first
authorities += { p.permissionName for each effective permission }  // BR-SC-RBAC-002
```

**Data Dependencies:**
- Reads: constant AUTH
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (AUTH) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (authority grant) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/users/50/effective-permissions` (user 50 in a group with no permissions)
- Success: `200 {"userId":50,"permissions":["AUTH"]}`
- Error Input: `GET /api/v1/identity/users/50/effective-permissions` when user 50 has zero groups (see BR-SC-AUTHN-003)
- Error Output: `404 {"error":"NotFound","message":"User 50 not found"}`

### BR-SC-AUTHN-003: A user with no group and no store is not loadable (inner-join gate)

**Source Reference:** `UserDaoImpl.java:getByUserName:26-33` and `getById:49-56` (inner join groups + merchantStore, left join language)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-016, BR-USER-027

**Statement:** An administrator record is only retrievable when it has at least one group and an assigned store; a user missing either is silently invisible to the system, including at login. The preferred language is optional and its absence does not hide the user. A user may, however, be loadable with groups that carry no permissions — in that case the user authenticates but holds only the baseline authority.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
from User u
  inner join fetch u.groups        // zero groups → row not returned
  inner join fetch u.merchantStore // no store  → row not returned
  left  join fetch u.defaultLanguage  // optional
where u.adminName = :userName  (or u.id = :id)
```

**Data Dependencies:**
- Reads: user, group membership, store, language
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK (join semantics, not branches) |
| Data-flow | 5 | 5 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (returned vs null) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (silent-null when no group/store) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/users/by-username/newadmin` (newadmin has a group and a store)
- Success: `200 {"id":60,"userName":"newadmin","active":true,"groups":[{"id":2,"groupName":"ADMIN"}]}`
- Error Input: `GET /api/v1/identity/users/by-username/orphan` (orphan has no group assigned)
- Error Output: `404 {"error":"NotFound","message":"User orphan not found or not fully provisioned"}`

### BR-SC-AUTHN-004: Successful login records the previous and current login timestamps

**Source Reference:** `UserAuthenticationSuccessHandler.java:onAuthenticationSuccess:29-48`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-028

**Statement:** On each successful login, the account's "last access" is set to the timestamp of the account's previous login (or to now if the account has never logged in before), and the "current login" timestamp is set to now. This preserves a one-login-behind view of prior access for the administrator.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
user = getByUserName(name)
lastAccess = user.loginTime          // the PRIOR login time
if lastAccess == null: lastAccess = now   // first-ever login
user.lastAccess = lastAccess
user.loginTime  = now
saveOrUpdate(user)
→ redirect /admin/home.html   (legacy web redirect; target returns tokens)
```

**Data Dependencies:**
- Reads: prior login timestamp
- Writes: last-access timestamp, current-login timestamp

**Side Effects:** updates the two login timestamps on every successful login

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (null-guard, try/catch) |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 2 | 2 | OK (lastAccess←prior, loginTime←now) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (timestamp update) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (failure logged, non-fatal) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/auth/login {"username":"admin","password":"password"}` (prior login 2024-05-01T09:00Z)
- Success: `200 {"authenticated":true,"lastAccess":"2024-05-01T09:00:00Z","loginTime":"2024-05-02T14:22:00Z"}`
- Error Input: `POST /api/v1/identity/auth/login {"username":"admin","password":"wrong"}`
- Error Output: `401 {"error":"Unauthorized","message":"Invalid credentials"}` (no timestamps changed)

### BR-SC-AUTHN-005: Access-denied logs the administrator out

**Source Reference:** `LoginController.java:displayDenied:28-40`
**Cross-Reference:** `shopizer-security.xml:access-denied-handler ref="adminAccessDenied"` (/admin/denied.html)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER (login/denied views — Screen Inventory)

**Statement:** When an authenticated administrator is denied access to a resource they lack authority for, the system terminates their session rather than merely showing an error, forcing re-authentication.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
on access-denied → route to denied handler
auth = currentAuthentication()
if auth != null: logout(session)   // invalidate session / clear security context
→ show logon
```

**Data Dependencies:**
- Reads: current authentication
- Writes: none (session invalidation)

**Side Effects:** session terminated

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (auth-null guard) |
| Data-flow | 0 | 0 | OK |
| Constants | 1 | 1 | OK (denied route) |
| State transitions | 1 | 1 | OK (authenticated → logged out) |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (security context logout) |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/auth/logout` (Authorization: Bearer <token>)
- Success: `204` (session/token invalidated)
- Error Input: `POST /api/v1/identity/auth/logout` with no token
- Error Output: `401 {"error":"Unauthorized","message":"No active session"}`

### BR-SC-AUTHN-006: A default super-administrator is provisioned at bootstrap

**Source Reference:** `UserServicesImpl.java:createDefaultAdmin:108-133`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-024 (bootstrap)

**Statement:** On system bootstrap a default administrator account is created against the default store, named "admin", assigned to both the super-administrator and administrator groups, so the back-office is reachable on a fresh install. In the legacy system this account ships with a well-known password.
**Intent:** State Transition
**Weight:** Critical
**PRESERVE-VS-FIX:** Legacy ships a known default password. Target: provision via OIDC, force first-login rotation, no shipped credential.

**Logic:**
```
store = getMerchantStore(DEFAULT_STORE)
user = new User("admin", encode("password"), "admin@shopizer.com")
for g in listGroup(ADMIN):
   if g.groupName in { SUPERADMIN, ADMIN }: user.groups += g
user.merchantStore = store
create(user)
```

**Data Dependencies:**
- Reads: default store, admin groups
- Writes: creates the default admin user + group membership

**Side Effects:** default admin account created

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (loop + membership guard) |
| Data-flow | 3 | 3 | OK |
| Constants | 3 | 3 | OK (admin name/email, default password, group names) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (user create) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/bootstrap/default-admin` (fresh install, no admin exists)
- Success: `201 {"id":1,"userName":"admin","groups":["SUPERADMIN","ADMIN"],"storeCode":"DEFAULT"}`
- Error Input: `POST /api/v1/identity/bootstrap/default-admin` when an admin already exists
- Error Output: `409 {"error":"Conflict","message":"Default administrator already provisioned"}`

---

## Group: BR-SC-AUTHZ — Per-request scoping, menu, and pluggable identity source

### BR-SC-AUTHZ-001: An admin request is scoped to the logged-in user's own store

**Source Reference:** `AdminFilter.java:preHandle:72-116` (`storeCode = user.getMerchantStore().getCode()`; else DEFAULT_STORE)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-030

**Statement:** Every back-office request operates within the store owned by the requesting administrator. The active store for the request is derived from the administrator's assigned store; when no administrator is resolved the request falls back to the default store. This store scope is the backbone of multi-tenant isolation for non-super-administrators.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
storeCode = DEFAULT_STORE
if authenticated user resolved:
   storeCode = user.merchantStore.code
activeStore = getStoreByCode(storeCode)
attach activeStore to the request context   // downstream reads scope by it
```

**Data Dependencies:**
- Reads: user's store reference, store by code
- Writes: none (request/session scope only)

**Side Effects:** sets the active-store request attribute

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (user-null, store-null, name-mismatch) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (DEFAULT_STORE) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (unresolved user → default store) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/context` (Authorization: Bearer <token for user whose store is STORE_A>)
- Success: `200 {"userName":"storeadmin","activeStore":"STORE_A"}`
- Error Input: `GET /api/v1/identity/context` with no token
- Error Output: `200 {"userName":null,"activeStore":"DEFAULT"}` (anonymous falls back to default store)

### BR-SC-AUTHZ-002: The logged-in administrator is cached per session and refreshed on user switch

**Source Reference:** `AdminFilter.java:preHandle:66-100`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-029

**Statement:** The resolved administrator is cached for the duration of the session to avoid reloading on every request; the cache is refreshed whenever the session's cached administrator no longer matches the authenticated principal (guarding against a stale session after a user switch). If the principal cannot be resolved to an account, the request is redirected to the unauthorized page.
**Intent:** Routing
**Weight:** Critical

**Logic:**
```
user = session[ADMIN_USER]
if principal present and user == null:
    user = getByUserName(principal); session[ADMIN_USER] = user
    if user == null → redirect /unauthorized
if user.adminName != principal:      // stale session on switch
    user = getByUserName(principal)  // reload
```

**Data Dependencies:**
- Reads: session-cached user, user by login name
- Writes: none (session cache only)

**Side Effects:** session cache write; possible redirect to unauthorized

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK (present, cache-miss, null, mismatch) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (ADMIN_USER key) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (cached vs reload/redirect) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (unresolved → redirect) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/context` (authenticated principal "admin" resolvable)
- Success: `200 {"userName":"admin","cached":true}`
- Error Input: `GET /api/v1/identity/context` (principal token references a user removed from the DB)
- Error Output: `401 {"error":"Unauthorized","message":"Authenticated principal no longer exists"}`

### BR-SC-AUTHZ-003: The admin menu is built from configurable data and cached globally

**Source Reference:** `AdminFilter.java:preHandle:120-165` + `getMenu:170-200`; `admin/menu.json`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-031

**Statement:** The back-office navigation menu is defined in an editable configuration resource rather than in code, parsed once into a tree and cached globally, and exposed to every request. Changing the menu structure requires no code change.
**Intent:** Routing
**Weight:** Critical
**Extension Point:** EXT-SC-002 (config-file-driven menu — see spec/shared/extensibility-model.md, compiled Stage 1.8)

**Logic:**
```
menus = cache["MENUMAP"]
if menus == null:
    data = parse config resource (menu definition, nested)
    for each top node: menus[node.code] = buildMenu(node)   // recursive, carries role per node
    cache["MENUMAP"] = menus
expose menu tree + flat list to request
```

**Data Dependencies:**
- Reads: menu configuration resource
- Writes: none (cache populate)

**Side Effects:** global menu cache populated on first request

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (cache-miss + recursive build + IO guards) |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK (menu resource path, cache key) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (cache/parse) |
| Error paths | 2 | 2 | OK (parse/IO errors logged) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/menu` (Authorization: Bearer <token>)
- Success: `200 {"items":[{"code":"home","role":"AUTH","url":"/admin/home.html"},{"code":"store","role":"STORE"}]}`
- Error Input: `GET /api/v1/identity/menu` with no token
- Error Output: `401 {"error":"Unauthorized","message":"Authentication required"}`

### BR-SC-AUTHZ-004: Each menu item is gated by a role equal to a permission name

**Source Reference:** `AdminFilter.java:getMenu:184` (`m.setRole((String)menu.get("role"))`); `admin/menu.json` (role: AUTH|STORE|SUPERADMIN|PRODUCTS|...)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-032

**Statement:** Every menu item declares a required role, and the item is presented to an administrator only if that administrator holds the authority of the same name. Because role names are permission names (BR-SC-RBAC-002), menu visibility is governed by the same data-driven RBAC as endpoint authorization. For example, store creation and the store list require the super-administrator role, while the home and profile items require only the baseline authenticated authority.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
menuItem.role = <permission name from config>
visible(item, user) == menuItem.role in effectiveAuthorities(user)   // BR-SC-RBAC-002
```

**Data Dependencies:**
- Reads: menu item role, user effective authorities
- Writes: none

**Side Effects:** none (visibility decision)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (role match) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (role names from config) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (visible/hidden) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (authority check) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/menu?filterByAuthority=true` (user holds AUTH, PRODUCTS but not SUPERADMIN)
- Success: `200 {"items":[{"code":"home","role":"AUTH"},{"code":"catalogue","role":"PRODUCTS"}]}` (store-create item omitted)
- Error Input: `GET /api/v1/identity/menu?filterByAuthority=maybe`
- Error Output: `400 {"error":"BadRequest","message":"filterByAuthority must be true or false"}`

### BR-SC-AUTHZ-005: The identity source is pluggable; the LDAP implementation is an inert stub

**Source Reference:** `UserServiceLDAPImpl.java` (entire file — every method throws "Not implemented" or returns null); `shopizer-security.xml` wires the DB-backed `userDetailsService`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER (UserServiceLDAPImpl negative result), Extensibility Signal

**Statement:** The administrator identity source is an extension point with more than one possible implementation. In the legacy system an LDAP-backed alternative exists as a placeholder but is entirely non-functional — every operation is unimplemented — and it is not wired into the running configuration, which uses the database-backed source. This is preserved as an extensibility signal, not as live behavior.
**Intent:** Routing
**Weight:** Critical
**Extension Point:** EXT-SC-003 (pluggable identity provider — target realizes this as OIDC federation per ADR-004)
**PRESERVE-VS-FIX:** Inert stub. Target: the pluggable-provider seam is realized by OIDC delegation, not an LDAP class.

**Logic:**
```
interface UserService { getByUserName, listUser, saveOrUpdate, ... }
DB impl (wired)   → real queries
LDAP impl (unwired) → every method: throw "Not implemented" / return null
```

**Data Dependencies:**
- Reads: none (stub)
- Writes: none (stub)

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 0 | 0 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK (uniformly not-implemented) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (identity-provider seam) |
| Error paths | 1 | 1 | OK (all throw) |

**Preservation:** OK

**Concrete Example:**
- Input: (design-time) configure `identity.provider = LDAP`
- Success: N/A in legacy — the seam exists; target uses OIDC federation
- Error Input: invoking the legacy LDAP source
- Error Output: `501 {"error":"NotImplemented","message":"LDAP identity source is not implemented"}`

---

## Group: BR-SC-USR — Admin user management (list, create, edit, delete)

### BR-SC-LSTUSR-001: User listing scope depends on whether the actor is a super-administrator

**Source Reference:** `UserController.java:pageUsers:118-128`; `UserDaoImpl.java:listUserByStore:78-90`, `listUser:66-76`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-017

**Statement:** A super-administrator sees the administrators of every store; any other administrator sees only the administrators of their own store. The scope of a user-management listing is therefore determined by the requesting administrator's super-administrator membership.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
currentUser = getByUserName(actor)
if userInGroup(currentUser, "SUPERADMIN") → listUser()          // all stores
else                                      → listByStore(activeStore)  // own store only
```

**Data Dependencies:**
- Reads: actor's group membership, users (all or by store)
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (superadmin branch) |
| Data-flow | 3 | 3 | OK |
| Constants | 1 | 1 | OK (SUPERADMIN) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (all vs own-store) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (failure status) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/users` (actor is SUPERADMIN)
- Success: `200 {"items":[{"userId":10,"name":"A B","storeCode":"STORE_A"},{"userId":20,"name":"C D","storeCode":"STORE_B"}]}`
- Error Input: `GET /api/v1/identity/users` (actor lacks STORE_ADMIN authority)
- Error Output: `403 {"error":"Forbidden","message":"STORE_ADMIN role required"}`

### BR-SC-LSTUSR-002: Super-administrators are hidden from the managed-user list

**Source Reference:** `UserController.java:pageUsers:130-150` (`if(!userInGroup(user,"SUPERADMIN")) { if(!currentUser.equals(user.getAdminName())) ... }`)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-021

**Statement:** The managed-user list never shows super-administrator accounts, so they cannot be managed from the ordinary user list. The list is also intended to exclude the requesting administrator's own account, but in the legacy code the self-exclusion test compares the whole account object to a plain login-name string and is therefore always false — so an administrator does in fact see their own row.
**Intent:** Routing / Filtering
**Weight:** Critical
**PRESERVE-VS-FIX:** Self-exclusion is a defect (object-vs-string comparison always false → self not hidden). Target: compare login names so self is correctly excluded.

**Logic:**
```
for user in users:
   if not userInGroup(user, "SUPERADMIN"):        // superadmins always excluded (effective)
      if not currentUser.equals(user.adminName):  // DEFECT: User.equals(String) → always false
         include user
```

**Data Dependencies:**
- Reads: user group membership, actor identity
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (superadmin filter + self filter) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (SUPERADMIN) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (included/excluded) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (self-exclusion ineffective — defect preserved) |

**Preservation:** FLAGGED (self-exclusion defect — behavior preserved, flagged for 4a)

**Concrete Example:**
- Input: `GET /api/v1/identity/users` (actor "storeadmin", store has storeadmin + a superadmin + peer "bob")
- Success: `200 {"items":[{"userId":30,"name":"Store Admin"},{"userId":31,"name":"Bob"}]}` (superadmin absent; legacy also includes actor's own row)
- Error Input: `GET /api/v1/identity/users` (actor not authenticated)
- Error Output: `401 {"error":"Unauthorized","message":"Authentication required"}`

### BR-SC-CREATE-001: Submitted group selections are group ids conveyed in the group-name field

**Source Reference:** `UserController.java:saveUser:470-476` (`ids.add(Integer.parseInt(group.getGroupName()))`); `GroupDaoImpl.java:listGroupByIds:46-66`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-004, BR-USER-018

**Statement:** When an administrator's group assignments are submitted, each selection carries a group identifier (not a name). The system parses those identifiers, re-loads the corresponding real groups (with their permissions), and assigns exactly that set as the user's authoritative group membership, replacing any prior membership.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
ids = { parseInt(selection.groupNameField) for selection in submittedGroups }
(+ forced SUPERADMIN id if applicable — BR-SC-EDIT-001)
newGroups = listGroupByIds(ids)      // select distinct g join fetch g.permissions where g.id in (:ids)
user.groups = newGroups              // replaces membership
```

**Data Dependencies:**
- Reads: submitted group ids, groups by id
- Writes: user's group membership (on persist)

**Side Effects:** user's group membership replaced to match resolved set

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (id-parse loop) |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (membership replace) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (USER_GROUP replace) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (non-numeric id) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users {"userName":"clerk","groupIds":[2,3], ...}`
- Success: `201 {"id":70,"userName":"clerk","groups":[{"id":2,"groupName":"ADMIN"},{"id":3,"groupName":"STORE_ADMIN"}]}`
- Error Input: `POST /api/v1/identity/users {"userName":"clerk","groupIds":["notanumber"], ...}`
- Error Output: `400 {"error":"BadRequest","message":"groupIds must be integers"}`

### BR-SC-CREATE-002: All three security answers are required

**Source Reference:** `UserController.java:saveUser:478-488`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-006

**Statement:** An administrator account must supply an answer to each of its three security questions; any blank answer rejects the save.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
if isBlank(answer1) → error(answer1)
if isBlank(answer2) → error(answer2)
if isBlank(answer3) → error(answer3)
```

**Data Dependencies:**
- Reads: submitted security answers
- Writes: none (validation)

**Side Effects:** binding errors → reject save

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (three blank checks) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 3 | 3 | OK (one per answer) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users {"userName":"clerk","securityAnswers":["blue","paris","rex"], ...}`
- Success: `201 {"id":71,"userName":"clerk"}`
- Error Input: `POST /api/v1/identity/users {"userName":"clerk","securityAnswers":["blue","","rex"], ...}`
- Error Output: `422 {"error":"ValidationError","message":"Security answer 2 is required"}`

### BR-SC-CREATE-003: The three security questions must be distinct

**Source Reference:** `UserController.java:saveUser:490-498`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-005

**Statement:** An administrator's three security questions must all be different from one another; choosing the same question twice rejects the save.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
if q1==q2 or q1==q3 or q2==q3 → error("questions must differ")
// (legacy boolean has redundant duplicated terms but reduces to these three inequalities)
```

**Data Dependencies:**
- Reads: submitted question selections
- Writes: none (validation)

**Side Effects:** binding error → reject save

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (compound distinctness; 6 duplicate terms merged to 3) |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users {"securityQuestions":[1,2,3], ...}`
- Success: `201 {"id":72}`
- Error Input: `POST /api/v1/identity/users {"securityQuestions":[1,1,3], ...}`
- Error Output: `422 {"error":"ValidationError","message":"Security questions must be distinct"}`

### BR-SC-CREATE-004: A new administrator's password must be at least 6 characters

**Source Reference:** `UserController.java:saveUser:515-520` (else-branch when id is null)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-007

**Statement:** When creating a new administrator, the initial password must be at least six characters long. This length check applies only to creation; on edit the password field is not re-validated because the stored password is retained (see BR-SC-EDIT-002).
**Intent:** Validation
**Weight:** Critical
**PRESERVE-VS-FIX:** Weak minimum (6 chars) with unsalted SHA-1. Target: OIDC-managed credentials or strong policy (ADR-004).

**Logic:**
```
if creating (no existing id):
   if password.length < 6 → error("password.length")
```

**Data Dependencies:**
- Reads: submitted password
- Writes: none (validation)

**Side Effects:** binding error → reject create

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (create-branch + length) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (min length 6) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users {"userName":"clerk","password":"s3cret9", ...}`
- Success: `201 {"id":73,"userName":"clerk"}`
- Error Input: `POST /api/v1/identity/users {"userName":"clerk","password":"abc", ...}`
- Error Output: `422 {"error":"ValidationError","message":"Password must be at least 6 characters"}`

### BR-SC-CREATE-005: On creation the password is hashed before storage

**Source Reference:** `UserController.java:saveUser:527-533` (create branch: `encode(password, null)`)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-009, BR-USER-023

**Statement:** A new administrator's password is stored only as a one-way hash, never in clear text. The plaintext is captured transiently only to include in the welcome email (see BR-SC-CREATE-006).
**Intent:** Calculation
**Weight:** Critical
**PRESERVE-VS-FIX:** Legacy hash is unsalted SHA-1 (deprecated encoder). Target: no stored credential — OIDC (ADR-004); if stored, use a salted adaptive hash.

**Logic:**
```
decodedPassword = password        // captured for the email
on create: user.adminPassword = hash(password)   // SHA-1, null salt (legacy)
```

**Data Dependencies:**
- Reads: submitted password
- Writes: stored password hash

**Side Effects:** password hash persisted (legacy)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (create branch) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (null salt) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (hash stored) |
| Integrations | 1 | 1 | OK (password encoder) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users {"userName":"clerk","password":"s3cret9", ...}`
- Success: `201 {"id":74,"userName":"clerk"}` (stored credential is a hash, never returned)
- Error Input: `POST /api/v1/identity/users {"userName":"clerk","password":null, ...}`
- Error Output: `422 {"error":"ValidationError","message":"Password is required"}`

### BR-SC-CREATE-006: Creating an administrator sends a welcome email containing the password

**Source Reference:** `UserController.java:saveUser:537-582`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-033

**Statement:** Only when a new administrator is created (not on edit), after the account is saved, a welcome email is sent to the administrator's address that includes their login name and — in the legacy system — their password in clear text. A failure to send the email is logged and swallowed, so account creation still succeeds.
**Intent:** Integration
**Weight:** Critical
**PRESERVE-VS-FIX:** Cleartext password in email. Target: send an activation/reset link, never the password.

**Logic:**
```
if just created:
   save(user)
   try:
      tokens = { firstName, adminName, password: decodedPassword, adminUrl, ... }
      email(to = adminEmail, template = NEW_USER_TMPL, tokens)   // cleartext password (legacy)
   catch → log, do not rethrow
```

**Data Dependencies:**
- Reads: created user, store email config
- Writes: none (side-effect email)

**Side Effects:** outbound welcome email (SMTP)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (create-only + try/catch) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (template name) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (sent / send-failed-non-fatal) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (email service) |
| Error paths | 1 | 1 | OK (email failure swallowed) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users {"userName":"clerk","email":"clerk@store.com","password":"s3cret9", ...}`
- Success: `201 {"id":75,"userName":"clerk","welcomeEmailSent":true}`
- Error Input: `POST /api/v1/identity/users {...}` with SMTP down
- Error Output: `201 {"id":75,"userName":"clerk","welcomeEmailSent":false}` (creation still succeeds)

### BR-SC-EDIT-001: A super-administrator's SUPERADMIN membership cannot be revoked on edit

**Source Reference:** `UserController.java:saveUser:500-513` (reload dbUser groups; if any "SUPERADMIN", force-add its id back)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-008

**Statement:** When editing an existing administrator who is a super-administrator, the super-administrator group is always retained even if the submitted form omitted it. The system re-adds the super-administrator group id to the resolved membership set before persisting, so a super-administrator cannot be demoted through the edit form.
**Intent:** Authorization / Invariant
**Weight:** Critical

**Logic:**
```
on edit:
   reload dbUser.groups
   superAdmin = the group named "SUPERADMIN" among dbUser.groups (if any)
   if superAdmin != null: ids.add(superAdmin.id)   // force-retain
```

**Data Dependencies:**
- Reads: existing user's groups
- Writes: user membership (superadmin retained) on persist

**Side Effects:** SUPERADMIN membership preserved across edit

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (edit branch + membership loop) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (SUPERADMIN literal — note: literal vs constant inconsistency) |
| State transitions | 1 | 1 | OK (retain membership) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (membership) |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/identity/users/1 {"groupIds":[2]}` (user 1 is a superadmin; form omits SUPERADMIN group id 1)
- Success: `200 {"id":1,"groups":[{"id":1,"groupName":"SUPERADMIN"},{"id":2,"groupName":"ADMIN"}]}` (SUPERADMIN retained)
- Error Input: `PUT /api/v1/identity/users/1 {"groupIds":[]}` for a superadmin
- Error Output: `200 {"id":1,"groups":[{"id":1,"groupName":"SUPERADMIN"}]}` (still retained — cannot be emptied of superadmin)

### BR-SC-EDIT-002: On edit the stored password is preserved and the account identity is confirmed

**Source Reference:** `UserController.java:saveUser:503-505` (id mismatch → redirect), `527-529` (edit branch keeps dbUser password); `displayUser:` sets adminPassword TRANSIENT on load
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-009

**Statement:** When editing an existing administrator, the previously stored password is retained unchanged — the edit form never round-trips the real password (it is loaded as a placeholder). The edit also confirms the record being saved is the same account that was loaded; a mismatch between the submitted account and the loaded account aborts the operation.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
on edit:
   dbUser = getByUserName(user.adminName)
   if dbUser == null → abort (redirect)
   if user.id != dbUser.id → abort (redirect)   // identity confirmation
   user.adminPassword = dbUser.adminPassword     // retain existing hash (form value was TRANSIENT)
```

**Data Dependencies:**
- Reads: existing user and stored password
- Writes: password retained (unchanged) on persist

**Side Effects:** none to the password value

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (null-guard + id match) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (TRANSIENT placeholder) |
| State transitions | 1 | 1 | OK (password unchanged) |
| Outcomes | 2 | 2 | OK (saved vs aborted) |
| Data writes | 1 | 1 | OK (retain) |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK (null user, id mismatch) |

**Preservation:** OK

**Concrete Example:**
- Input: `PUT /api/v1/identity/users/40 {"userName":"clerk","firstName":"Clara"}` (no password field)
- Success: `200 {"id":40,"userName":"clerk","firstName":"Clara"}` (stored credential unchanged)
- Error Input: `PUT /api/v1/identity/users/40 {"userName":"someoneelse"}` (username resolves to a different id)
- Error Output: `409 {"error":"Conflict","message":"Submitted account does not match the target user"}`

### BR-SC-DELUSR-001: Deleting a user requires the actor to hold the ADMIN authority

**Source Reference:** `UserController.java:removeUser:600-618` (target-null guard; `request.isUserInRole(GROUP_ADMIN)`; actor group ADMIN/SUPERADMIN)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-019

**Statement:** An administrator may delete a user only when the target user exists and the acting administrator holds the ADMIN authority and belongs to the administrator or super-administrator group. A missing target, or an actor lacking the ADMIN authority, or an actor who is neither an administrator nor a super-administrator, is rejected as unauthorized.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
target = getById(userId)
if target == null → unauthorized failure
if not actorHasAuthority("ADMIN") → unauthorized failure    // authority named "ADMIN" (a permission)
isAdmin = userInGroup(actor,"ADMIN") or userInGroup(actor,"SUPERADMIN")   // group names
if not isAdmin → failure
```
> NOTE: mixes an authority check ("ADMIN" as a permission name) with a group-membership check ("ADMIN" as a group name) — the same token used two ways (flagged for 4a clarification).

**Data Dependencies:**
- Reads: target user, actor authorities and group membership
- Writes: none (until BR-SC-DELUSR-002)

**Side Effects:** none (guard only)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (target-null, authority, group) |
| Data-flow | 3 | 3 | OK |
| Constants | 2 | 2 | OK (ADMIN, SUPERADMIN) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (allowed vs unauthorized) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 3 | 3 | OK (three rejection paths) |

**Preservation:** OK

**Concrete Example:**
- Input: `DELETE /api/v1/identity/users/40` (actor holds ADMIN authority and is in group ADMIN)
- Success: `204`
- Error Input: `DELETE /api/v1/identity/users/40` (actor authenticated but lacks ADMIN authority)
- Error Output: `403 {"error":"Forbidden","message":"ADMIN role required to remove a user"}`

### BR-SC-DELUSR-002: Deletion removes the user and its group memberships (no target-superadmin guard)

**Source Reference:** `UserController.java:removeUser:620-624` (`userService.delete(user)`); `UserServiceImpl.java:delete:37-43` (reload by id then delete)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-020

**Statement:** Once the actor authorization passes, the target user is removed along with its group membership links. Although the operation's intent (per its comments and error label) is to protect super-administrators, no check prevents deleting a super-administrator target — any qualifying administrator can delete any user, including a super-administrator.
**Intent:** State Transition
**Weight:** Critical
**PRESERVE-VS-FIX:** Missing target-is-superadmin guard (defect). Target: reject deletion of a super-administrator target.

**Logic:**
```
u = getById(target.id)   // re-load managed entity
delete(u)                // DELETE USER + USER_GROUP links
// NOTE: no check that target is NOT a superadmin, despite the "cannot remove superadmin" label
```

**Data Dependencies:**
- Reads: target user by id
- Writes: user removed, user group memberships removed

**Side Effects:** deletes the user and its membership rows

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (user removed) |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK (user + memberships) |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (missing target-guard preserved as defect) |

**Preservation:** FLAGGED (missing superadmin-delete guard — behavior preserved, flagged for 4a)

**Concrete Example:**
- Input: `DELETE /api/v1/identity/users/41` (target 41 is an ordinary admin; actor qualifies)
- Success: `204` (user 41 and its memberships removed)
- Error Input: `DELETE /api/v1/identity/users/1` (target 1 is a superadmin) — legacy permits this
- Error Output: legacy `204` (superadmin deleted — the flagged gap). Target: `403 {"error":"Forbidden","message":"Cannot delete a super-administrator"}`

### BR-SC-UNIQ-001: An administrator login name is unique and checkable before save

**Source Reference:** `UserController.java:checkUserCode:290-340`; `User.java:57-59` (ADMIN_NAME unique)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-018

**Statement:** An administrator login name must be unique across the system. The system can check a proposed login name before submission: a name is acceptable if it is non-blank and either unused, or already belongs to the same account being edited. In the legacy model uniqueness is enforced globally on the login name, not per store.
**Intent:** Validation
**Weight:** Critical
**PRESERVE-VS-FIX:** Uniqueness is global, not per-tenant, while users are store-scoped (open question flagged for 4a). Target ERD keeps `user_name` "unique per tenant".

**Logic:**
```
if isBlank(code) → CODE_ALREADY_EXIST (treated as not acceptable)
existing = getByUserName(code)
if editing (id present) and existing != null and existing.id == id and existing.adminName == code → OK
if existing != null → CODE_ALREADY_EXIST
else → OPERATION_COMPLETED (available)
```

**Data Dependencies:**
- Reads: user by login name
- Writes: none

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK (blank, edit-same, exists, else) |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 3 | 3 | OK (blank, exists, available) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK (blank, taken) |

**Preservation:** OK

**Concrete Example:**
- Input: `GET /api/v1/identity/users/check-username?userName=clerk`
- Success: `200 {"available":true}`
- Error Input: `GET /api/v1/identity/users/check-username?userName=admin` (already taken)
- Error Output: `200 {"available":false,"reason":"USERNAME_TAKEN"}`

---

## Group: BR-SC-PWD — Self password change & reset

### BR-SC-PWD-001: Passwords are stored as an unsalted one-way hash

**Source Reference:** `shopizer-security.xml:passwordEncoder (ShaPasswordEncoder)` + `<password-encoder hash="sha"/>`; `UserController`/`UserServicesImpl` `encodePassword(x, null)`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-023

**Statement:** Administrator passwords are never stored in clear text; they are stored as a one-way hash computed with no per-account salt using a now-deprecated hashing scheme. This is a security-debt behavior preserved for traceability.
**Intent:** Calculation
**Weight:** Critical
**PRESERVE-VS-FIX:** Unsalted SHA-1, deprecated encoder. Target: no stored credential (OIDC, ADR-004); if stored, salted adaptive hash (bcrypt/argon2).

**Logic:**
```
storedHash = SHA1(plaintext)   // salt = null, deprecated ShaPasswordEncoder
compare: SHA1(submitted) == storedHash
```

**Data Dependencies:**
- Reads: submitted plaintext
- Writes: stored hash (on create/change/reset)

**Side Effects:** none directly (used by create/change/reset)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (null salt) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (encoder SPI) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: (internal) hash of "s3cret9"
- Success: a stable hash string persisted as the credential (never returned by any endpoint)
- Error Input: comparing a wrong plaintext
- Error Output: hashes differ → credential rejected (see BR-SC-PWD-002)

### BR-SC-PWD-002: Changing your own password requires the correct current password

**Source Reference:** `UserController.java:changePassword:196-208`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-010

**Statement:** An administrator can change only their own password, and only by proving knowledge of the current one. The change is refused if the request targets a different account than the authenticated one, if the current password is blank, or if the supplied current password does not match what is stored.
**Intent:** Authorization
**Weight:** Critical

**Logic:**
```
dbUser = getByUserName(actor)
if request.user.id != dbUser.id → reject (can only change own password)
if isBlank(currentPassword) → error
if hash(currentPassword) != dbUser.storedHash → error "password.invalid"
```

**Data Dependencies:**
- Reads: actor account, stored hash
- Writes: none (validation stage)

**Side Effects:** binding errors → reject

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK (identity, blank, match) |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (proceed vs reject) |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK (encoder) |
| Error paths | 3 | 3 | OK (wrong account, blank, mismatch) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users/me/password {"currentPassword":"s3cret9","newPassword":"n3wpass1","repeatPassword":"n3wpass1"}`
- Success: `200 {"changed":true}`
- Error Input: `POST /api/v1/identity/users/me/password {"currentPassword":"wrong", ...}`
- Error Output: `422 {"error":"ValidationError","message":"Current password is invalid"}`

### BR-SC-PWD-003: The new password must be confirmed and at least 6 characters

**Source Reference:** `UserController.java:changePassword:210-229`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-011, BR-USER-012

**Statement:** When changing a password, both the new password and its confirmation are required, they must match each other, and the new password must be at least six characters long. Any of these failing rejects the change.
**Intent:** Validation
**Weight:** Critical

**Logic:**
```
if isBlank(newPassword) → error
if isBlank(repeatPassword) → error
if repeatPassword != newPassword → error "password.different"
if newPassword.length < 6 → error "password.length"
```

**Data Dependencies:**
- Reads: submitted new/confirm passwords
- Writes: none (validation)

**Side Effects:** binding errors → reject

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK (blank, blank, match, length) |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK (min length 6) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 4 | 4 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users/me/password {"currentPassword":"s3cret9","newPassword":"n3wpass1","repeatPassword":"n3wpass1"}`
- Success: `200 {"changed":true}`
- Error Input: `POST /api/v1/identity/users/me/password {"currentPassword":"s3cret9","newPassword":"n3wpass1","repeatPassword":"n3wpass2"}`
- Error Output: `422 {"error":"ValidationError","message":"New password and confirmation do not match"}`

### BR-SC-PWD-004: A validated password change persists the new hash

**Source Reference:** `UserController.java:changePassword:235-239`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-013

**Statement:** Once all password-change validations pass, the account's stored credential is replaced with the hash of the new password.
**Intent:** State Transition
**Weight:** Critical

**Logic:**
```
dbUser.storedHash = hash(newPassword)
update(dbUser)
```

**Data Dependencies:**
- Reads: validated new password
- Writes: stored credential hash

**Side Effects:** credential updated

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 0 | 0 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK (credential replaced) |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK (credential) |
| Integrations | 1 | 1 | OK (encoder) |
| Error paths | 0 | 0 | OK |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/users/me/password {"currentPassword":"s3cret9","newPassword":"n3wpass1","repeatPassword":"n3wpass1"}`
- Success: `200 {"changed":true}` (subsequent login requires n3wpass1)
- Error Input: same call when backing store rejects the update
- Error Output: `500 {"error":"InternalError","message":"Password could not be updated"}`

### BR-SC-RESET-001: Password-reset step one returns the account's security questions by username

**Source Reference:** `UserController.java:resetPassword:640-690`
**Cross-Reference:** `shopizer-security.xml` (`/admin/users/resetPassword.html*` permitAll)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-014

**Statement:** The first step of a forgotten-password flow accepts a login name (without authentication) and returns that account's three security questions. The submitted name is retained for the second step. A blank name, or a name that matches no account, returns a failure — and because the failure message differs from success, the response reveals whether a given administrator login name exists.
**Intent:** Routing
**Weight:** Critical
**PRESERVE-VS-FIX:** Unauthenticated + username enumeration (distinct not-found response). Target: uniform response regardless of existence.

**Logic:**
```
session["username_reset"] = username     // stored before existence check
if isBlank(username) → failure
dbUser = getByUserName(username)
if dbUser == null → failure "username.notfound"   // enumeration signal
else → { question1, question2, question3 }
```

**Data Dependencies:**
- Reads: account by login name, its security questions
- Writes: none (session marker)

**Side Effects:** stores the reset username in session

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (blank, not-found) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (session key) |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (questions vs failure) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK (blank, not-found — enumeration preserved) |

**Preservation:** FLAGGED (username enumeration — behavior preserved, flagged for 4a)

**Concrete Example:**
- Input: `POST /api/v1/identity/password-reset/questions {"userName":"admin"}`
- Success: `200 {"question1":"First pet?","question2":"Birth city?","question3":"Mother's maiden name?"}`
- Error Input: `POST /api/v1/identity/password-reset/questions {"userName":"ghost"}`
- Error Output: legacy `404 {"error":"NotFound","message":"Username not found"}` (enumeration). Target: uniform `202 Accepted` regardless.

### BR-SC-RESET-002: Reset step two grants a new password only on exact security-answer match

**Source Reference:** `UserController.java:resetPasswordSecurityQtn:710-760` (answer match, trimmed, case-sensitive)
**Cross-Reference:** `shopizer-security.xml` (`/admin/users/resetPasswordSecurityQtn.html*` permitAll)
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-015

**Statement:** The second reset step retrieves the account named in the first step and grants a password reset only if all three submitted security answers exactly match the stored answers (compared after trimming surrounding whitespace, case-sensitively). Wrong answers, or an unresolved account, reject the reset.
**Intent:** Authorization
**Weight:** Critical
**PRESERVE-VS-FIX:** Unauthenticated; answer-based reset is weak. Target: OIDC-managed reset (ADR-004).

**Logic:**
```
dbUser = getByUserName(session["username_reset"])
if dbUser == null → failure "userNotFound"
if a1 == answer1.trim() and a2 == answer2.trim() and a3 == answer3.trim():
    → proceed to reset (BR-SC-RESET-003)
else → failure "wrongSecurityQtn"
```

**Data Dependencies:**
- Reads: account, stored security answers
- Writes: none (this rule — the write is BR-SC-RESET-003)

**Side Effects:** none directly

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (user-null, answers-match) |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK (match vs wrong) |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK (no user, wrong answers) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/password-reset/verify {"answers":["rex","paris","smith"]}`
- Success: `200 {"verified":true}` (proceeds to reset)
- Error Input: `POST /api/v1/identity/password-reset/verify {"answers":["rex","london","smith"]}`
- Error Output: `422 {"error":"ValidationError","message":"Security answers are incorrect"}`

### BR-SC-RESET-003: A verified reset stores a new random password and emails it in clear text

**Source Reference:** `UserController.java:resetPasswordSecurityQtn:725-745`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-015

**Statement:** On a successful security-answer verification, the system generates a random temporary password, stores its hash as the account's new credential, and emails the temporary password to the account's address in clear text. An email failure is logged and does not undo the credential change.
**Intent:** State Transition
**Weight:** Critical
**PRESERVE-VS-FIX:** Cleartext temporary password in email. Target: send a one-time reset link, not the password.

**Logic:**
```
tempPass = generateRandomTemporaryPassword()   // see BR-SC-RESET-004
dbUser.storedHash = hash(tempPass)
update(dbUser)
try: email(to = adminEmail, template = RESET_PASSWORD_TPL, tokens={ password: tempPass })  // cleartext
catch → log, non-fatal
```

**Data Dependencies:**
- Reads: verified account, store email config
- Writes: stored credential hash

**Side Effects:** credential replaced; outbound reset email (cleartext temp password)

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK (email try/catch) |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK (template name) |
| State transitions | 1 | 1 | OK (credential replaced) |
| Outcomes | 2 | 2 | OK (reset+sent / reset+send-failed) |
| Data writes | 1 | 1 | OK (credential) |
| Integrations | 1 | 1 | OK (email) |
| Error paths | 1 | 1 | OK (email failure non-fatal) |

**Preservation:** OK

**Concrete Example:**
- Input: `POST /api/v1/identity/password-reset/complete` (following a verified BR-SC-RESET-002)
- Success: `200 {"reset":true,"temporaryPasswordEmailed":true}`
- Error Input: `POST /api/v1/identity/password-reset/complete` without a prior verified step
- Error Output: `409 {"error":"Conflict","message":"No verified reset in progress"}`

### BR-SC-RESET-004: The temporary password is a fixed-length random alphanumeric string

**Source Reference:** `UserReset.java:generateRandomString:14-24` and `getRandomNumber:37-46`
**Discovery Method:** Direct Source Read
**Cross-ref P1:** BR-USER-034 (P1 marked charset/length UNKNOWN — resolved here as a net-new finding)

**Statement:** The temporary password produced during reset is a random string of ten characters drawn from an alphanumeric alphabet. In the legacy generator the randomness source is a general-purpose (non-cryptographic) generator, and an off-by-range defect means the last portion of the intended alphabet is never selected and the first character is over-represented — so the effective alphabet and distribution are narrower than intended.
**Intent:** Calculation
**Weight:** Critical
**PRESERVE-VS-FIX:** Non-cryptographic RNG + index-range defect narrows entropy. Target: cryptographically secure generator over the full intended alphabet.

**Logic:**
```
length = 10
alphabet_used = [a-zA-Z0-9]        // 62 chars intended
for i in 0..9:
   n = randomIndex()               // bug: bound = len(CHAR_LIST)=54, not 62; returns n-1 (index 0 over-represented, indices 54..61 never chosen)
   char = alphabet_used[n]
result = concat(chars)             // 10 chars
```

**Data Dependencies:**
- Reads: none
- Writes: none (produces a value consumed by BR-SC-RESET-003)

**Side Effects:** none

**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK (generation loop + range guard) |
| Data-flow | 0 | 0 | OK |
| Constants | 3 | 3 | OK (length 10, two alphabets, bounds) |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK (range defect preserved) |

**Preservation:** OK (defect documented — net-new finding vs P1)

**Concrete Example:**
- Input: (internal) generate a temporary password
- Success: a 10-character alphanumeric string, e.g. `k9Fh2mQ0aB` (legacy: last 8 alphabet slots unreachable)
- Error Input: N/A (no inputs)
- Error Output: N/A
