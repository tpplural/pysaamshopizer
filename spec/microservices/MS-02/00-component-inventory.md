# identity-admin (MS-02) — Component Inventory

**Segment:** 12 (User/Admin & Security). **Legacy stack:** Java / Spring MVC 3.1 + Spring Security 3.1.
**Legacy schema:** `SALESMANAGER`. **Target schema:** `identity_admin`.

## Legacy components mapped

| Component | Type | Complexity | Target disposition | Rules |
|-----------|------|------------|--------------------|-------|
| User / Group / Permission (model) | Entity | Simple | `admin_user` / `sm_group` / `permission` + join tables | BR-SC-RBAC-001/003/004 |
| GroupType (enum) | Utility | Simple | `group_type` CHECK (ADMIN/CUSTOMER) | BR-SC-RBAC-004 |
| PermissionCriteria / PermissionList | Utility (DTO) | Simple | pagination request/response shapes | BR-SC-PERM-001 |
| UserServiceImpl / UserDaoImpl | Service/DAO | Medium | user CRUD + fetch-join loads | BR-SC-AUTHN-003, BR-SC-DELUSR-002, BR-SC-LSTUSR-001 |
| UserServiceLDAPImpl | Service | Simple | **inert stub** → pluggable-provider seam (OIDC in target) | BR-SC-AUTHZ-005 |
| GroupServiceImpl / GroupDaoImpl | Service/DAO | Simple | group listing (type/ids/permission) | BR-SC-RBAC-004/006, BR-SC-CREATE-001 |
| PermissionServiceImpl / PermissionDaoImpl | Service/DAO | Medium | permission listing, criteria paging, group-assoc lifecycle | BR-SC-PERM-001/002/004/005 |
| UserController | MVC controller | Complex (~640 LOC) | admin user CRUD, password change, reset, uniqueness AJAX | BR-SC-LSTUSR/CREATE/EDIT/DELUSR/PWD/RESET/UNIQ |
| GroupsController | MVC controller | Simple | group list/edit/paging | BR-SC-RBAC-004/005 |
| PermissionController | MVC controller | Simple | permission paging (display = not implemented) | BR-SC-PERM-002/003 |
| LoginController | MVC controller | Simple | logon/denied(logout)/unauthorized | BR-SC-AUTHN-005 |
| SecurityController | MVC controller | Simple | groups/permissions menu views | BR-SC-RBAC-004 |
| UserServicesImpl (admin SPI) | Security SPI | Medium | UserDetailsService load + default-admin bootstrap | BR-SC-AUTHN-001/002/006, BR-SC-RBAC-002 |
| UserAuthenticationSuccessHandler | Security SPI | Simple | login timestamp stamping | BR-SC-AUTHN-004 |
| AdminFilter | Interceptor | Medium | user session cache, store scope, language, menu build | BR-SC-AUTHZ-001/002/003/004 |
| UserUtils | Utility | Simple | userInGroup helper | (supports authorization rules) |
| UserReset | Utility | Simple | random temp-password generator (defect) | BR-SC-RESET-004 |
| shopizer-security.xml | Config | Medium | filter chain, encoder, permitAll reset endpoints | BR-SC-PWD-001, BR-SC-AUTHN-001/005 |
| admin/menu.json | Config resource | Medium | menu tree with per-item role | BR-SC-AUTHZ-003/004 |

## Owned tables (target)

`admin_user`, `sm_group`, `permission`, `user_group`, `permission_group`.
Legacy `SM_SEQUENCER` (id allocation) is replaced by DB identity columns. `MERCHANT_STORE` and `LANGUAGE`
are cross-service reads (xref), not owned.

## Extensibility signals (Layer B — compiled Stage 1.8)

| ID | Mechanism | What varies |
|----|-----------|-------------|
| EXT-SC-001 | data-driven RBAC | new permission/group names are data rows → new authorities with no code change (BR-SC-RBAC-003) |
| EXT-SC-002 | config-file-driven menu | menu structure + per-item required role are editable config (BR-SC-AUTHZ-003/004) |
| EXT-SC-003 | pluggable identity provider | DB vs LDAP (legacy stub) → OIDC federation in target (BR-SC-AUTHZ-005, ADR-004) |

## Placement candidates (Layer C)

None. No batch sweeps, no set-based bulk updates, no DB stored procedures/triggers. All logic is app-tier.
