# identity-admin (MS-02) — Extraction Evidence

**Analysis Mode:** Direct Source Read (no CAST). **Session:** Phase 4 deep extraction.

## Source Files Processed

| # | File | LOC (approx) | Sections Read | Rules Extracted | Vectors |
|---|------|--------------|---------------|-----------------|---------|
| 1 | sm-core-model/.../user/model/User.java | 250 | full — entity, 15 columns, groups M:N, store, language, timestamps | BR-SC-RBAC-001, BR-SC-AUTHN-003 (model basis) | ✅ |
| 2 | sm-core-model/.../user/model/Group.java | 110 | full — GROUP_NAME unique, GROUP_TYPE enum, permissions mappedBy | BR-SC-RBAC-003/004 | ✅ |
| 3 | sm-core-model/.../user/model/Permission.java | 120 | full — PERMISSION_NAME unique, groups M:N owning side (PERMISSION_GROUP) | BR-SC-RBAC-001/003 | ✅ |
| 4 | sm-core-model/.../user/model/GroupType.java | 6 | full — ADMIN, CUSTOMER | BR-SC-RBAC-004 | ✅ |
| 5 | sm-core-model/.../user/model/PermissionCriteria.java | 55 | full — paging/filter DTO (permissionName, available, groupIds) | BR-SC-PERM-001 | ✅ |
| 6 | sm-core-model/.../user/model/PermissionList.java | 27 | full — totalCount + permissions list DTO | BR-SC-PERM-001 | ✅ |
| 7 | sm-core/.../user/service/UserServiceImpl.java | 90 | full — getByUserName, delete (reload+delete), saveOrUpdate (create vs update) | BR-SC-DELUSR-002, BR-SC-CREATE-001 | ✅ |
| 8 | sm-core/.../user/service/UserServiceLDAPImpl.java | 110 | full — every method throws "Not implemented"/returns null (inert stub) | BR-SC-AUTHZ-005 | ✅ |
| 9 | sm-core/.../user/service/GroupServiceImpl.java | 55 | full — listGroup(type), listGroupByIds | BR-SC-RBAC-004, BR-SC-CREATE-001 | ✅ |
| 10 | sm-core/.../user/service/PermissionServiceImpl.java | 100 | full — deletePermission (null groups→delete), removePermission (no persist), getPermissions, listByCriteria | BR-SC-PERM-004/005/001 | ✅ |
| 11 | sm-core/.../user/dao/UserDaoImpl.java | 95 | full — getByUserName/getById (inner join groups+store, left join lang), listUser, listUserByStore | BR-SC-AUTHN-003, BR-SC-LSTUSR-001 | ✅ |
| 12 | sm-core/.../user/dao/GroupDaoImpl.java | 85 | full — getGroupsListBypermissions, listGroupByIds (join fetch permissions), listGroup(type) | BR-SC-RBAC-004/006, BR-SC-CREATE-001 | ✅ |
| 13 | sm-core/.../user/dao/PermissionDaoImpl.java | 140 | full — listPermission, getById, getPermissionsListByGroups, listByCriteria (count+page) | BR-SC-PERM-001/002, BR-SC-RBAC-002 | ✅ |
| 14 | sm-shop/.../admin/controller/user/UserController.java | 640 | multi-pass (list/paging, change-password, save create+edit, remove, reset step1+step2, checkUserCode) | BR-SC-LSTUSR-*, BR-SC-CREATE-*, BR-SC-EDIT-*, BR-SC-DELUSR-*, BR-SC-PWD-*, BR-SC-RESET-*, BR-SC-UNIQ-001 | ✅ |
| 15 | sm-shop/.../admin/controller/user/GroupsController.java | 155 | full — displayGroups (ADMIN filter), pageGroups (list() ALL), editGroup | BR-SC-RBAC-004/005 | ✅ |
| 16 | sm-shop/.../admin/controller/user/PermissionController.java | 115 | full — displayPermissions (throws Not implemented), pagePermissions | BR-SC-PERM-002/003 | ✅ |
| 17 | sm-shop/.../admin/controller/user/LoginController.java | 50 | full — logon, denied (logout), unauthorized views | BR-SC-AUTHN-005 | ✅ |
| 18 | sm-shop/.../admin/controller/user/SecurityController.java | 65 | full — displayGroups (ADMIN), displayPermissions view | BR-SC-RBAC-004 | ✅ |
| 19 | sm-shop/.../admin/security/UserServicesImpl.java | 135 | full — loadUserByUsername (AUTH grant + permission authorities), createDefaultAdmin | BR-SC-AUTHN-001/002/006, BR-SC-RBAC-002 | ✅ |
| 20 | sm-shop/.../admin/security/UserAuthenticationSuccessHandler.java | 50 | full — onAuthenticationSuccess (lastAccess/loginTime stamping) | BR-SC-AUTHN-004 | ✅ |
| 21 | sm-shop/.../filter/AdminFilter.java | 210 | full — preHandle (user cache, store scope, language, menu build) + getMenu (recursive, role) | BR-SC-AUTHZ-001/002/003/004 | ✅ |
| 22 | sm-shop/.../utils/UserUtils.java | 25 | full — userInGroup(user, groupName) | BR-SC-LSTUSR-001/002, BR-SC-DELUSR-001 | ✅ |
| 23 | sm-shop/.../webapp/WEB-INF/spring/appServlet/shopizer-security.xml | 130 | full — /admin/** filter chain, ShaPasswordEncoder, permitAll reset endpoints, form-login + success handler | BR-SC-PWD-001, BR-SC-AUTHN-001/005, BR-SC-RESET-001/002 | ✅ |
| 24 | sm-shop/.../resources/admin/menu.json | 300 | full — menu tree, per-node role (AUTH/STORE/SUPERADMIN/PRODUCTS/...) | BR-SC-AUTHZ-003/004 | ✅ |
| 25 | sm-shop/.../admin/entity/userpassword/UserReset.java | 50 | full — generateRandomString (len 10), getRandomNumber (range defect) | BR-SC-RESET-004 | ✅ |
| 26 | sm-shop/.../web/constants/Constants.java | (grep) | GROUP_ADMIN="ADMIN", GROUP_SUPERADMIN="SUPERADMIN", PERMISSION_AUTHENTICATED="AUTH", ADMIN_STORE, ADMIN_USER, DEFAULT_STORE | supports BR-SC-AUTHN-002, BR-SC-DELUSR-001, BR-SC-EDIT-001 | ✅ |

## Extraction Status
- Files total: 26 (24 primary + UserReset + Constants confirmations)
- Files processed: 26
- Rules extracted: 43 (BR-SC-*, cross-referenced to BR-USER-001..034)
- Source vectors complete: yes (from P1 per-component 8-dim vectors + this deep read)
- Files NOT read / NOT FOUND: none. (`SecurityQuestion.java` located but is a trivial label DTO — not a
  rule source; its 9 static questions are surfaced as the securityQuestions option list in the create flow.)

## Session Log
| Session | Files Processed | Rules Added | Notes |
|---------|-----------------|-------------|-------|
| 1 | 1-26 (all) | 43 | Single deep pass. UserController read multi-pass (640 LOC). BR-USER-034 charset/length resolved from UserReset.java (net-new). |
