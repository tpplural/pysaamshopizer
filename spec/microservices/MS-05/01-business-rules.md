# Customer Service (MS-05) — Business Rules

**Version**: 1.0
**Service ID**: MS-05
**Status**: 🟢 Extraction complete (Phase 4, Direct Source mode)
**Legacy system**: Shopizer 2.0.1 (Java / Spring MVC / JPA-Hibernate / Spring Security)
**Groups**: `BR-CUST` (customer / registration / auth / embedded billing+delivery address / gender) — 28 rules · `BR-CUSTOPT` (customer options / values / option-sets / per-customer attributes) — 15 rules
**Total**: 43 rules

> Statements are architecture-agnostic (domain terms only). Legacy class/table/column names appear ONLY in Logic and Source Reference. All source paths are under `initial-source/shopizer/`.

---

### BR-CUST-001: Shopper username is unique within a store

**Source Reference:** `CustomerFacadeImpl.java:getCustomerByUserName:~228-232`; `CustomerServiceImpl.java:getByNick:58-61`; `CustomerDAOImpl.java:getByNick:216-247`
**Discovery Method:** Direct Source Read
**Statement:** A shopper is identified by a username that is unique only within a single store; the same username may be reused by a different shopper in a different store. Authentication and lookups always resolve a shopper by the pair (username, store).
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
customer = getByNick(nick, storeId)   // filters nick == nick AND merchantStore.id == storeId
RETURN customer OR null   // null on no result
```
**Data Dependencies:**
- Reads: customer.customer_nick, customer.merchant_id
**Side Effects:** None (read).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/customers/lookup?userName=jsmith` (header `x-store-id: 1`)
- Success: `200 {"id":"...","userName":"jsmith","storeId":1}`
- Error Input: `GET /api/v1/customers/lookup?userName=nobody` (header `x-store-id: 1`)
- Error Output: `404 {"error":"NotFound","message":"No customer for username in this store"}`

---

### BR-CUST-002: Registration rejects a username already taken in the same store

**Source Reference:** `CustomerFacadeImpl.java:checkIfUserExists:~245-267`; `CustomerRegistrationController.java:registerCustomer:~175-183`
**Discovery Method:** Direct Source Read
**Statement:** Registration is rejected when the requested username is already in use by another shopper in the same store. Uniqueness is scoped per store, not globally.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
IF notBlank(userName) AND store != null:
    existing = getByNick(userName, store.id)
    IF existing != null: reject with "registration.username.already.exists"
```
**Data Dependencies:**
- Reads: customer.customer_nick, customer.merchant_id
**Side Effects:** None (adds validation error, returns registration form). No DB unique constraint exists on (merchant_id, nick) in the legacy — enforced in code only.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Note (modernization):** the legacy relies on an application-level check only. The target service SHOULD add a database unique constraint on (store, username) to close the race window (see INV-CUST-002).

**Concrete Example:**
- Input: `POST /api/v1/customers/registration {"userName":"jsmith","emailAddress":"j@x.com","password":"p","checkPassword":"p"}` (`x-store-id: 1`, existing jsmith)
- Success: `201` when username is free
- Error Input: same body when jsmith already exists in store 1
- Error Output: `409 {"error":"Conflict","message":"Username already exists for this store"}`

---

### BR-CUST-003: Registration requires the password and its confirmation to match

**Source Reference:** `CustomerRegistrationController.java:registerCustomer:~186-197`
**Discovery Method:** Direct Source Read
**Statement:** During self-service registration, when both a password and a confirmation value are supplied, they must be identical; a mismatch rejects the registration.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
IF notBlank(password) AND notBlank(checkPassword):
    IF password != checkPassword: reject with "message.password.checkpassword.identical"
```
**Data Dependencies:**
- Reads: (request fields password, checkPassword)
**Side Effects:** None (validation). Match is only enforced when both fields present.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/registration {"userName":"a","password":"secret1","checkPassword":"secret1", ...}`
- Success: `201 {"id":"..."}`
- Error Input: `{"password":"secret1","checkPassword":"secret2", ...}`
- Error Output: `422 {"error":"Unprocessable","message":"Password and confirmation do not match"}`

---

### BR-CUST-004: Shopper passwords are stored only in one-way encoded form

**Source Reference:** `CustomerFacadeImpl.java:getCustomerModel:~330-333`; `CustomerFacadeImpl.java:setCustomerModelDefaultProperties:~370-377`; `CustomerAccountController.java:changePassword:~230-235`
**Discovery Method:** Direct Source Read
**Statement:** A shopper's password is never persisted in clear text; it is always stored as a one-way encoded value produced by the identity mechanism before persistence.
**Intent:** Compliance
**Weight:** High
**Logic:**
```pseudocode
encoded = passwordEncoder.encodePassword(clearPassword, null)  // Spring Security PasswordEncoder, null salt (deprecated API)
customer.password = encoded  // persisted to customer.customer_password (length 50 in legacy)
```
**Data Dependencies:**
- Reads: (transient clear password)
- Writes: customer.customer_password
**Side Effects:** Persists encoded password. Delegates encoding to identity mechanism (MS-02 / Spring Security).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

> **Note (modernization):** legacy uses a deprecated encoder with a null salt and a 50-char column. Target SHOULD use a salted adaptive hash (e.g. bcrypt/argon2) and widen the credential field.

**Concrete Example:**
- Input: `POST /api/v1/customers/registration {"password":"secret1", ...}`
- Success: `201` — stored credential is an opaque hash, never `secret1`
- Error Input: attempt to read back the stored password via any API
- Error Output: response never contains the clear or encoded password field

---

### BR-CUST-005: A new shopper with a blank username is assigned a generated username

**Source Reference:** `CustomerFacadeImpl.java:setCustomerModelDefaultProperties:~360-366`; constant `USERNAME_LENGTH=6`
**Discovery Method:** Direct Source Read
**Statement:** When a new shopper is created without a username, the system assigns a randomly generated six-character username. This applies only to new shoppers.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
IF (customer.id == null OR id == 0) AND isBlank(nick):
    nick = generateRandomString(6)   // USERNAME_LENGTH = 6
```
**Data Dependencies:**
- Writes: customer.customer_nick
**Side Effects:** Sets username before persistence.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com"}` (no userName; `x-store-id: 1`)
- Success: `201 {"userName":"a7Kd2P"}` (generated 6-char)
- Error Input: `POST /api/v1/customers {"emailAddress":""}` (no username, invalid email)
- Error Output: `422 {"error":"Unprocessable","message":"Email is required"}`

---

### BR-CUST-006: A new or blank-password shopper is assigned a generated encoded password

**Source Reference:** `CustomerFacadeImpl.java:setCustomerModelDefaultProperties:~367-372`; `CustomerRESTController.java:createCustomer:~430-436`
**Discovery Method:** Direct Source Read
**Statement:** When a new shopper is created without a password (typically admin- or system-created accounts), the system generates a random password and stores it encoded.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
IF isBlank(password):
    password = encode(generateRandomString())
```
**Data Dependencies:**
- Writes: customer.customer_password
**Side Effects:** Persists a generated encoded password.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com","userName":"a"}` (no password)
- Success: `201` — account is created with a generated encoded password
- Error Input: `POST /api/v1/customers {}` (no email)
- Error Output: `422 {"error":"Unprocessable","message":"Email is required"}`

---

### BR-CUST-007: A shopper with no group defaults to the standard shopper group

**Source Reference:** `CustomerFacadeImpl.java:setCustomerModelDefaultProperties:~379-388`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper is created without any group membership, they are placed into the standard shopper group by default.
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
IF customer.groups isEmpty:
    groups = groupService.listGroup(CUSTOMER)
    add the group whose name == GROUP_CUSTOMER
```
**Data Dependencies:**
- Reads: group (external MS-02)
- Writes: customer_group (join)
**Side Effects:** Adds group membership. Group catalog is owned by MS-02 (identity); this service references group ids only.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/registration {"userName":"a","password":"p","checkPassword":"p","emailAddress":"a@x.com"}`
- Success: `201 {"groups":["CUSTOMER"]}`
- Error Input: registration with a non-existent group id supplied
- Error Output: `422 {"error":"Unprocessable","message":"Unknown group"}`

---

### BR-CUST-008: An authenticated shopper's authorities combine a base role with group permissions

**Source Reference:** `CustomerFacadeImpl.java:authenticate:~394-420`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper authenticates, their effective authorities are the base "authenticated shopper" role plus one authority per permission granted through their groups. Authentication itself is delegated to the identity mechanism.
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
authorities = [PERMISSION_CUSTOMER_AUTHENTICATED]
FOR each permission in permissionService.getPermissions(customer.groupIds):
    authorities.add(GrantedAuthority(permission.name))
token = UsernamePasswordAuthenticationToken(userName, password, authorities)
customerAuthenticationManager.authenticate(token)   // delegated
SecurityContextHolder.setAuthentication(...)
```
**Data Dependencies:**
- Reads: group, permission (external MS-02)
**Side Effects:** Mutates security context. Delegates to identity/Spring-Security AuthenticationManager (MS-02).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 2 | 2 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/login {"userName":"jsmith","password":"secret1"}` (`x-store-id: 1`)
- Success: `200 {"authenticated":true,"authorities":["AUTH_CUSTOMER","..."]}`
- Error Input: `POST /api/v1/customers/login {"userName":"jsmith","password":"wrong"}`
- Error Output: `401 {"error":"Unauthorized","message":"Authentication failed"}`

---

### BR-CUST-009: Login fails uniformly when the shopper does not exist for (username, store)

**Source Reference:** `CustomerLoginController.java:logon:~66-73`
**Discovery Method:** Direct Source Read
**Statement:** A login attempt returns a single generic failure when no shopper exists for the supplied username in the current store, and likewise for a bad password — the two cases are indistinguishable to the caller.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
customer = getCustomerByUserName(userName, store)
IF customer == null: RETURN FAILURE
TRY authenticate(...) CATCH AuthenticationException|Exception: RETURN FAILURE
```
**Data Dependencies:**
- Reads: customer.customer_nick, customer.merchant_id
**Side Effects:** On success sets session/customer context.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/login {"userName":"jsmith","password":"secret1"}`
- Success: `200 {"status":"success"}`
- Error Input: `POST /api/v1/customers/login {"userName":"ghost","password":"x"}`
- Error Output: `401 {"status":"failure"}` (same status for unknown user and bad password)

---

### BR-CUST-010: Setting a real password marks a shopper as non-anonymous

**Source Reference:** `CustomerPopulator.java:populate:~64-67`; `Customer.java:setPassword`; `Customer.java:setAnonymous`
**Discovery Method:** Direct Source Read
**Statement:** When a real (encoded) password is assigned to a shopper, that shopper is flagged as a registered (non-anonymous) account.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
IF notBlank(source.encodedPassword):
    target.password = encoded
    target.anonymous = false
```
**Data Dependencies:**
- Writes: customer.customer_password, customer.customer_anonymous
**Side Effects:** Mutates account state.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/registration {"userName":"a","password":"p","checkPassword":"p","emailAddress":"a@x.com"}`
- Success: `201 {"anonymous":false}`
- Error Input: register with blank password when a password is required by the flow
- Error Output: `422 {"error":"Unprocessable","message":"Password required"}`

---

### BR-CUST-011: A billing address requires name, street, city and postal code

**Source Reference:** `Billing.java:20-30`; `CustomerController.java:saveCustomer:~250-300`; `Customer.java:66-70`
**Discovery Method:** Direct Source Read
**Statement:** A shopper's billing address must include first name, last name, street address, city, postal code and a country; the shopper email must also be present and well-formed. These are mandatory before a customer record can be persisted with billing.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
// Billing firstName, lastName are @NotEmpty; billing country nullable=false
// admin controller also rejects blank: firstName, lastName, address, city, postalCode
// email is @Email @NotEmpty on the customer entity
IF blank(any of firstName,lastName,address,city,postalCode) OR country==null: reject
```
**Data Dependencies:**
- Reads/Writes: customer.billing_first_name, billing_last_name, billing_street_address, billing_city, billing_postcode, billing_country_id, customer.customer_email_address
**Side Effects:** None (validation).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 7 | 7 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `PUT /api/v1/customers/{id}/addresses/billing {"firstName":"J","lastName":"S","address":"1 St","city":"NY","postalCode":"10001","country":"US"}`
- Success: `200 {"billing":{"city":"NY"}}`
- Error Input: `{"firstName":"J","lastName":"S","city":"NY","country":"US"}` (missing address, postalCode)
- Error Output: `422 {"error":"Unprocessable","message":"Billing address and postal code are required"}`

---

### BR-CUST-012: The delivery (shipping) address is optional

**Source Reference:** `Delivery.java:16-50`; `CustomerPopulator.java:populate:~121-160`
**Discovery Method:** Direct Source Read
**Statement:** A shopper's delivery address is entirely optional; all its fields, including its country, may be absent, in contrast to the billing address.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
// Delivery has no @NotEmpty; delivery country nullable=true
IF source.delivery present: build Delivery else leave null
```
**Data Dependencies:**
- Writes: customer.delivery_* columns (all nullable)
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com","userName":"a","billing":{...}}` (no delivery)
- Success: `201 {"delivery":null}`
- Error Input: `PUT /api/v1/customers/{id}/addresses/delivery {"country":"ZZ"}` (unknown country code)
- Error Output: `422 {"error":"Unprocessable","message":"Unsupported country code ZZ"}`

---

### BR-CUST-013: Country and zone on an address must resolve to known reference data

**Source Reference:** `CustomerPopulator.java:populate:~88-118`; `CustomerFacadeImpl.java:updateAddress:~470-520`
**Discovery Method:** Direct Source Read
**Statement:** Whenever an address supplies a country or a state/zone code, that code must correspond to an existing reference-data entry; an unknown code causes the operation to be rejected.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
country = countriesMap.get(code); IF country == null: throw "Unsuported country code"
IF country present AND notBlank(zoneCode):
    zone = zoneService.getByCode(zoneCode); IF zone == null: throw "Unsuported zone code"
```
**Data Dependencies:**
- Reads: country, zone (external MS-01 reference data)
**Side Effects:** Aborts persistence on unknown code.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 2 | 2 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `PUT /api/v1/customers/{id}/addresses/billing {"country":"US","zone":"NY", ...}`
- Success: `200 {"billing":{"country":"US","zone":"NY"}}`
- Error Input: `{"country":"US","zone":"ZZZ", ...}`
- Error Output: `422 {"error":"Unprocessable","message":"Unsupported zone code ZZZ"}`

---

### BR-CUST-014: A shopper's language defaults to the store default when unresolved

**Source Reference:** `CustomerPopulator.java:populate:~186-196`
**Discovery Method:** Direct Source Read
**Statement:** Every shopper has a language. If the requested language code cannot be resolved, the shopper is assigned the store's default language so that the language is never left unset.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
IF target.defaultLanguage == null:
    lang = languageService.getByCode(source.language)
    IF lang == null: lang = store.getDefaultLanguage()
    target.defaultLanguage = lang
```
**Data Dependencies:**
- Reads: language, merchant_store default language (external MS-01)
- Writes: customer.language_id
**Side Effects:** Sets language before persistence (language_id is not-null).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com","language":"zz"}` (store default en)
- Success: `201 {"language":"en"}`
- Error Input: `POST /api/v1/customers {"emailAddress":"a@x.com"}` when the store has no default language configured
- Error Output: `422 {"error":"Unprocessable","message":"No language could be resolved"}`

---

### BR-CUST-015: Persisting a shopper creates when new and updates when existing

**Source Reference:** `CustomerServiceImpl.java:saveOrUpdate:~84-96`
**Discovery Method:** Direct Source Read
**Statement:** Saving a shopper creates a new record when the shopper has no identity yet and updates the existing record otherwise (upsert by identity presence).
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
IF customer.id != null AND id > 0: update(customer)
ELSE: create(customer)
```
**Data Dependencies:**
- Writes: customer (INSERT or UPDATE)
**Side Effects:** INSERT or UPDATE of the customer record.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com","userName":"a"}`
- Success: `201 {"id":"c-1"}` (create); `PUT /api/v1/customers/c-1 {...}` → `200` (update)
- Error Input: `PUT /api/v1/customers/does-not-exist {...}`
- Error Output: `404 {"error":"NotFound","message":"Customer not found"}`

---

### BR-CUST-016: Changing a password requires the current password to match

**Source Reference:** `CustomerAccountController.java:changePassword:~205-218`
**Discovery Method:** Direct Source Read
**Statement:** A shopper may change their own password only after proving knowledge of the current password; a mismatch rejects the change.
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
encodedCurrent = encode(currentPassword)
IF encodedCurrent != customer.password: reject with "message.invalidpassword"
ELSE: customer.password = encode(newPassword); saveOrUpdate; send change-password email
```
**Data Dependencies:**
- Reads/Writes: customer.customer_password
**Side Effects:** On success: UPDATE customer; send change-password email (external).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/{id}/password {"currentPassword":"old","password":"new"}`
- Success: `200 {"status":"changed"}`
- Error Input: `{"currentPassword":"wrong","password":"new"}`
- Error Output: `422 {"error":"Unprocessable","message":"Current password is invalid"}`

---

### BR-CUST-017: Administrative email validation applies a stricter pattern

**Source Reference:** `CustomerController.java:saveCustomer:~230-247`
**Discovery Method:** Direct Source Read
**Statement:** On the administrative save path, the shopper email must be non-empty and match an explicit email pattern, in addition to the standard email validation.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
IF blank(email): reject "NotEmpty"
ELSE IF !pattern.matches(email): reject "Email.customer.EmailAddress"
// pattern = \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}\b
```
**Data Dependencies:**
- Reads: customer.customer_email_address
**Side Effects:** None (validation).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK

> **Note (modernization):** the legacy TLD bound `{2,4}` rejects valid modern TLDs; target SHOULD use a standards-based email validator.

**Concrete Example:**
- Input: `POST /api/v1/admin/customers {"emailAddress":"j@x.com", ...}`
- Success: `201 {"emailAddress":"j@x.com"}`
- Error Input: `{"emailAddress":"not-an-email", ...}`
- Error Output: `422 {"error":"Unprocessable","message":"Invalid email address"}`

---

### BR-CUST-018: A shopper or option resource may be operated on only within its owning store

**Source Reference:** `CustomerController.java:saveCustomer:~305-316`; `CustomerAccountController.java:saveCustomerAttributes:~236-241`; `CustomerRESTController.java:deleteCustomer:~360-372`
**Discovery Method:** Direct Source Read
**Statement:** Every operation on a shopper (or a store-scoped customer option/value/set) is permitted only when the target resource belongs to the store in the request context; a cross-store operation is refused.
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
IF resource.merchantStore.id != contextStore.id: abort (redirect / 404 / failure)
```
**Data Dependencies:**
- Reads: customer.merchant_id (and option/value merchant_id)
**Side Effects:** Aborts the operation.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/customers/{id}` where id belongs to store 1 (`x-store-id: 1`)
- Success: `200 {"id":"...","storeId":1}`
- Error Input: same id with `x-store-id: 2`
- Error Output: `404 {"error":"NotFound","message":"Customer is not part of this store"}`

---

### BR-CUST-019: Address state and zone are mutually exclusive, driven by a country flag

**Source Reference:** `CustomerController.java:saveCustomer:~275-360`; `CustomerFacadeImpl.java:updateAddress:~485-520`
**Discovery Method:** Direct Source Read
**Statement:** For a given country, an address supplies either a selectable zone or a free-text state, never both. When the country uses a zone list, the zone is required and any free-text state is cleared; otherwise the zone is cleared and the free-text state is kept.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
IF showStateList == "yes":   // country uses zone dropdown
    require zone; setZone(zone); setState(null)
ELSE:
    setZone(null); keep free-text state
```
**Data Dependencies:**
- Writes: customer.billing_zone_id / billing_state (and delivery_*)
**Side Effects:** Normalizes zone/state before save.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 2 | 2 | OK |
| State transitions | 2 | 2 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `PUT /api/v1/customers/{id}/addresses/billing {"country":"US","zone":"NY"}` (US uses zones)
- Success: `200 {"billing":{"zone":"NY","state":null}}`
- Error Input: `{"country":"US","state":"Freetext"}` (zone required but omitted)
- Error Output: `422 {"error":"Unprocessable","message":"Billing state/zone is required"}`

---

### BR-CUST-020: Registration validates a human-verification challenge when supplied

**Source Reference:** `CustomerRegistrationController.java:registerCustomer:~150-170`
**Discovery Method:** Direct Source Read
**Statement:** When a human-verification challenge and response are present on a registration request, they must validate against the verification provider; an invalid response rejects the registration. When absent, the check is skipped.
**Intent:** Validation
**Weight:** High
**Logic:**
```pseudocode
IF notBlank(challenge) AND notBlank(response):
    resp = reCaptcha.checkAnswer(remoteAddr, challenge, response)
    IF !resp.isValid(): reject "validaion.recaptcha.not.matched"
```
**Data Dependencies:**
- Reads: verification provider keys (config)
**Side Effects:** Network call to the verification provider (external integration).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Note (modernization):** the challenge is skipped entirely when the fields are absent, so a client omitting them bypasses it. Target SHOULD enforce verification server-side rather than trust presence of the fields.

**Concrete Example:**
- Input: `POST /api/v1/customers/registration {"userName":"a","password":"p","checkPassword":"p","emailAddress":"a@x.com","captchaChallenge":"c","captchaResponse":"r"}`
- Success: `201` when the challenge validates
- Error Input: same with an invalid captchaResponse
- Error Output: `422 {"error":"Unprocessable","message":"Human verification failed"}`

---

### BR-CUST-021: Lifecycle emails are sent on registration, password reset and password change

**Source Reference:** `CustomerRegistrationController.java:registerCustomer:~226-228`; `CustomerAccountController.java:changePassword:~240-242`; `CustomerRESTController.java:createCustomer:~443`
**Discovery Method:** Direct Source Read
**Statement:** After a successful registration, password change, or administrative password reset, a corresponding notification email is dispatched to the shopper.
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
AFTER successful register/change/reset:
    build templated email; send via EmailService/EmailTemplatesUtils
```
**Data Dependencies:**
- Reads: store email config, customer email/name
**Side Effects:** Outbound SMTP email (external integration).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Note (modernization):** legacy does not wrap registration email send in a try/catch, so an SMTP failure surfaces after the account is already persisted. Target SHOULD make notifications fire-and-forget (queued) so they do not fail the transaction.

**Concrete Example:**
- Input: `POST /api/v1/customers/registration {...valid...}`
- Success: `201` and a registration email is queued to the shopper
- Error Input: registration completes but the mail provider is down
- Error Output: account remains created; email delivery is retried asynchronously (target behavior)

---

### BR-CUST-022: On login, an anonymous session cart is merged into the shopper's cart

**Source Reference:** `CustomerFacadeImpl.java:mergeCart:~145-230`; `CustomerLoginController.java:logon:~85-99`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper logs in, an unowned cart from the anonymous session is assigned or merged into the shopper's cart; a cart already owned by a different shopper is never taken. The cart operation itself is owned by the cart service.
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
IF customer has no cart AND session cart unowned: assign session cart to customer
ELSE IF both exist AND session cart unowned: mergeShoppingCarts
ELSE IF session cart owned by same customer but different code: merge
ELSE IF session cart owned by another user: return null (do not steal)
```
**Data Dependencies:**
- Reads/Writes: shopping_cart (owned by MS-06)
**Side Effects:** Delegates cart save/merge to the cart service (MS-06). This service is only the login-side trigger.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 6 | 6 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 3 | 3 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/login {"userName":"a","password":"p","sessionCartCode":"CART-XYZ"}`
- Success: `200 {"status":"success","cartCode":"CART-XYZ"}`
- Error Input: login with a sessionCartCode already owned by another shopper
- Error Output: `200 {"status":"success","cartCode":null}` (foreign cart not merged)

---

### BR-CUST-023: Group membership is associated but group records are never created or deleted through a shopper

**Source Reference:** `Customer.java:100-118`; `CustomerFacadeImpl.java:setCustomerModelDefaultProperties:~379-388`
**Discovery Method:** Direct Source Read
**Statement:** Assigning a shopper to a group records the membership only; the group definitions themselves are never created, modified, or removed as a side effect of shopper operations.
**Intent:** Compliance
**Weight:** High
**Logic:**
```pseudocode
// ManyToMany cascade = {REFRESH} only (+ Hibernate DETACH/LOCK/REFRESH/REPLICATE); NO PERSIST/MERGE/REMOVE
add group to customer.groups → only the customer_group join row is written
```
**Data Dependencies:**
- Writes: customer_group (join only)
**Side Effects:** Join-table write on flush; never writes the group catalog (owned by MS-02).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/{id}/groups {"groupId":3}`
- Success: `200 {"groups":[3]}` — only membership is written
- Error Input: `POST /api/v1/customers/{id}/groups {"groupId":9999}` (unknown group)
- Error Output: `422 {"error":"Unprocessable","message":"Unknown group id"}`

---

### BR-CUST-024: Store-scoped operations resolve and validate the store from the request

**Source Reference:** `CustomerRESTController.java:getCustomer:~110-135`; `CustomerRESTController.java:createCustomer:~380-405`
**Discovery Method:** Direct Source Read
**Statement:** For store-scoped operations, the target store is taken from the request context and validated against the requested store identifier; when the store cannot be resolved the request is refused before any data access.
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
store = requestContext.store
IF store.code != requestedStore: store = null
IF store == null: store = merchantStoreService.getByCode(requestedStore)
IF store == null: respond 503 (unresolved store)
```
**Data Dependencies:**
- Reads: merchant_store (external MS-01)
**Side Effects:** Error response when store is unresolved; otherwise scopes all access.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/customers/{id}` (`x-store-id: 1`)
- Success: `200 {...}`
- Error Input: request with an unknown store identifier
- Error Output: `503 {"error":"ServiceUnavailable","message":"Store could not be resolved"}`

---

### BR-CUST-025: An administrative password reset emails the new password in clear text

**Source Reference:** `CustomerController.java:resetPassword:~640-690`; `CustomerRESTController.java:createCustomer:~430-443`
**Discovery Method:** Direct Source Read
**Statement:** When an administrator resets a shopper's password, the newly generated password is placed into the reset email body and sent to the shopper in clear text (the stored copy remains encoded).
**Intent:** Routing
**Weight:** High
**Logic:**
```pseudocode
newPassword = generateRandomString()
customer.password = encode(newPassword); save
email.body[EMAIL_CUSTOMER_PASSWORD] = newPassword (clear); send
```
**Data Dependencies:**
- Reads: customer email
- Writes: customer.customer_password
**Side Effects:** Outbound email containing a clear-text password.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

> **Note (modernization):** emailing a clear-text password is a security exposure. Target SHOULD replace this with a one-time reset link / token flow and never transmit the password.

**Concrete Example:**
- Input: `POST /api/v1/admin/customers/{id}/password-reset`
- Success: `200 {"status":"reset"}` (email dispatched)
- Error Input: reset for an id not in the admin's store
- Error Output: `404 {"error":"NotFound","message":"Customer is not part of this store"}`

---

### BR-CUST-026: Shoppers created via the service API are placed in an administrative group (legacy defect)

**Source Reference:** `CustomerRESTController.java:createCustomer:~408-411`
**Discovery Method:** Direct Source Read
**Statement:** On the service (REST) create path, a newly created shopper is assigned administrative group membership rather than the standard shopper group used by the self-service path. This is inconsistent with the shopper domain and is treated as a suspected defect to be confirmed.
**Intent:** Authorization
**Weight:** Critical
**4a Decision:** Fix-on-migration — assign CUSTOMER group (not ADMIN) for REST-created shoppers
**Logic:**
```pseudocode
groups = groupService.listGroup(GroupType.ADMIN)  // <-- ADMIN, not CUSTOMER
cust.setGroups(groups)
```
**Data Dependencies:**
- Reads: group (external MS-02)
- Writes: customer_group (join)
**Side Effects:** Grants admin-level group membership to API-created shoppers.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 1 | 1 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 1 | 1 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** FLAGGED (outcomes — suspected defect)

> **Note (modernization / 🔴 clarification):** this appears to be a copy/paste defect. Target behavior SHOULD assign the standard shopper group (per BR-CUST-007); confirm with the business before preserving.

**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com","userName":"a"}` (service path)
- Success (legacy, preserved-as-flagged): `201 {"groups":["ADMIN"]}`
- Error Input: same when the ADMIN group is not configured for the store
- Error Output: `422 {"error":"Unprocessable","message":"Group not available"}`

---

### BR-CUST-027: A shopper's gender defaults to a fixed value when unset (net-new)

**Source Reference:** `CustomerPopulator.java:populate:~68-74`; `Customer.java:setGender`; `CustomerGender.java`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper is created without a specified gender, the system assigns a default gender value rather than leaving it unset. Valid gender values are Male and Female.
**Intent:** Calculation
**Weight:** High
**Logic:**
```pseudocode
IF source.gender != null AND target.gender == null:
    target.gender = valueOf(source.gender)
IF target.gender == null:
    target.gender = M   // legacy hard-codes Male as the default
```
**Data Dependencies:**
- Writes: customer.customer_gender
**Side Effects:** Sets gender before persistence.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK

> **Note (modernization):** the legacy silently defaults gender to Male (`M`). Preserved as the current behavior for parity. **Target-state requirement:** the default gender value MUST be configurable (e.g. a per-store / service configuration setting) rather than hard-coded to Male; the service SHOULD read the default from configuration and SHOULD support leaving gender unset where the store allows it. This is a modernization/flag item, not the preserved legacy behavior.

**Concrete Example:**
- Input: `POST /api/v1/customers {"emailAddress":"a@x.com","userName":"a"}` (no gender)
- Success: `201 {"gender":"M"}` (legacy default; configurable default in target)
- Error Input: `POST /api/v1/customers {"emailAddress":"a@x.com","gender":"X"}` (invalid gender)
- Error Output: `422 {"error":"Unprocessable","message":"Gender must be M or F"}`

---

### BR-CUST-028: Hard-deleting a shopper cascades removal of the shopper's attributes (net-new)

**Source Reference:** `CustomerServiceImpl.java:delete:~99-110`; `CustomerAttributeServiceImpl.java:delete:~37-42`; `CustomerRESTController.java:deleteCustomer:~360-375`
**Discovery Method:** Direct Source Read
**Statement:** Deleting a shopper first removes all of that shopper's custom attributes and then removes the shopper record itself, so no orphaned attributes remain.
**Intent:** State Transition
**Weight:** High
**Logic:**
```pseudocode
customer = getById(id)
attributes = customerAttributeService.getByCustomer(store, customer)
FOR each attribute: customerAttributeService.delete(attribute)
customerDAO.delete(customer)
```
**Data Dependencies:**
- Writes: customer_attribute (DELETE), customer (DELETE)
**Side Effects:** Multi-row DELETE. Legacy performs the attribute cascade in application code (in addition to the JPA REMOVE cascade on the attributes association).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Note (modernization):** the target SHOULD enforce this cascade at the database level (ON DELETE CASCADE, INV-CUST-013) so integrity does not depend on the application being the sole writer.

**Concrete Example:**
- Input: `DELETE /api/v1/customers/{id}` (`x-store-id: 1`)
- Success: `204` — shopper and all its attributes removed
- Error Input: `DELETE /api/v1/customers/{id}` where id belongs to another store
- Error Output: `404 {"error":"NotFound","message":"Customer is not part of this store"}`

---

### BR-CUSTOPT-001: A customer option code is unique within a store

**Source Reference:** `CustomerOptionsController.java:saveOption:~190-196`; `CustomerOption.java:33-37`; `CustomerOptionServiceImpl.java:getByCode:~90-93`
**Discovery Method:** Direct Source Read
**Statement:** A merchant-defined custom customer field (option) must have a code that is unique within its store; creating a second option with an existing code in the same store is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
byCode = getByCode(store, code)
IF byCode != null AND option.id == null: reject "message.code.exist"
// backed by DB unique constraint (merchant_id, customer_opt_code)
```
**Data Dependencies:**
- Reads/Writes: customer_option.customer_opt_code, customer_option.merchant_id
**Side Effects:** None (validation).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-options {"code":"NEWSLETTER","type":"Checkbox","descriptions":[{"language":"en","name":"Newsletter"}]}`
- Success: `201 {"id":"...","code":"NEWSLETTER"}`
- Error Input: same code again in the same store
- Error Output: `409 {"error":"Conflict","message":"Option code already exists"}`

---

### BR-CUSTOPT-002: A customer option code is alphanumeric/underscore and non-empty

**Source Reference:** `CustomerOption.java:50-54`; `CustomerOptionsController.java:saveOption:~150-165`
**Discovery Method:** Direct Source Read
**Statement:** A customer option code must be non-empty and contain only letters, digits and underscores.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
// @NotEmpty @Pattern(regexp="^[a-zA-Z0-9_]*$")
IF blank(code) OR !code.matches("^[a-zA-Z0-9_]*$"): reject
```
**Data Dependencies:**
- Reads: customer_option.customer_opt_code
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-options {"code":"PREF_LANG","type":"Select", ...}`
- Success: `201 {"code":"PREF_LANG"}`
- Error Input: `{"code":"pref lang!","type":"Select", ...}`
- Error Output: `422 {"error":"Unprocessable","message":"Code must match ^[a-zA-Z0-9_]*$"}`

---

### BR-CUSTOPT-003: Each customer option requires a name in every store language

**Source Reference:** `CustomerOptionsController.java:saveOption:~198-220`
**Discovery Method:** Direct Source Read
**Statement:** A customer option must carry a non-empty display name for each language configured on the store; a blank name for any language is rejected.
**Intent:** Validation
**Weight:** Low
**Logic:**
```pseudocode
FOR each description in submitted list:
    IF blank(description.name): reject "message.name.required"
    ELSE bind description.language and back-reference the option
```
**Data Dependencies:**
- Reads/Writes: customer_option_description, language (external)
**Side Effects:** Sets descriptions before save.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-options {"code":"NL","type":"Checkbox","descriptions":[{"language":"en","name":"Newsletter"},{"language":"fr","name":"Infolettre"}]}`
- Success: `201`
- Error Input: `{"code":"NL","type":"Checkbox","descriptions":[{"language":"en","name":""}]}`
- Error Output: `422 {"error":"Unprocessable","message":"Name is required"}`

---

### BR-CUSTOPT-004: A customer option value code is unique within a store

**Source Reference:** `CustomerOptionsValueController.java:saveOption:~205-211`; `CustomerOptionValue.java:33-35`; `CustomerOptionValueServiceImpl.java:getByCode:~87-90`
**Discovery Method:** Direct Source Read
**Statement:** A value belonging to a customer option must have a code unique within its store; a duplicate code in the same store is rejected on create.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
byCode = getByCode(store, code)
IF byCode != null AND value.id == null: reject "message.code.exist"
// backed by DB unique constraint (merchant_id, customer_opt_val_code)
```
**Data Dependencies:**
- Reads/Writes: customer_option_value.customer_opt_val_code, merchant_id
**Side Effects:** None (validation).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-option-values {"code":"WEEKLY","descriptions":[{"language":"en","name":"Weekly"}]}`
- Success: `201 {"code":"WEEKLY"}`
- Error Input: same code again in the same store
- Error Output: `409 {"error":"Conflict","message":"Value code already exists"}`

---

### BR-CUSTOPT-005: A customer option value code is alphanumeric/underscore and non-empty

**Source Reference:** `CustomerOptionValue.java:51-55`; `CustomerOptionsValueController.java:saveOption:~205-215`
**Discovery Method:** Direct Source Read
**Statement:** A customer option value code must be non-empty and contain only letters, digits and underscores.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
// @NotEmpty @Pattern(regexp="^[a-zA-Z0-9_]*$")
IF blank(code) OR !code.matches("^[a-zA-Z0-9_]*$"): reject
```
**Data Dependencies:**
- Reads: customer_option_value.customer_opt_val_code
**Side Effects:** None.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-option-values {"code":"WEEKLY", ...}`
- Success: `201`
- Error Input: `{"code":"weekly!", ...}`
- Error Output: `422 {"error":"Unprocessable","message":"Code must match ^[a-zA-Z0-9_]*$"}`

---

### BR-CUSTOPT-006: Each option value requires at least one non-blank description

**Source Reference:** `CustomerOptionsValueController.java:saveOption:~215-245`
**Discovery Method:** Direct Source Read
**Statement:** A customer option value must have at least one description, and every supplied description must have a non-blank name.
**Intent:** Validation
**Weight:** Low
**Logic:**
```pseudocode
IF descriptions empty: reject "message.name.required"
ELSE FOR each description: IF blank(name): reject; ELSE bind language + back-reference value
```
**Data Dependencies:**
- Reads/Writes: customer_option_value_description, language (external)
**Side Effects:** Sets descriptions before save.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-option-values {"code":"W","descriptions":[{"language":"en","name":"Weekly"}]}`
- Success: `201`
- Error Input: `{"code":"W","descriptions":[]}`
- Error Output: `422 {"error":"Unprocessable","message":"At least one description is required"}`

---

### BR-CUSTOPT-007: An option-set binding requires both an option and a value

**Source Reference:** `CustomerOptionsSetController.java:saveOptionSet:~110-130`
**Discovery Method:** Direct Source Read
**Statement:** A binding that associates a customer option with one of its values must reference both an existing option and an existing value; a binding missing either is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
IF optionSet.customerOption == null OR optionSet.customerOptionValue == null:
    reject "message.optionset.noassociation"
option = getById(optionId); IF null: redirect
value = getById(valueId); IF null: redirect
```
**Data Dependencies:**
- Reads: customer_option, customer_option_value
- Writes: customer_option_set
**Side Effects:** None on failure.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 2 | 2 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-option-sets {"optionId":"o-1","optionValueId":"v-1"}`
- Success: `201 {"id":"...","optionId":"o-1","optionValueId":"v-1"}`
- Error Input: `{"optionId":"o-1"}` (no value)
- Error Output: `422 {"error":"Unprocessable","message":"Option and value are both required"}`

---

### BR-CUSTOPT-008: An (option, value) binding is unique within a store

**Source Reference:** `CustomerOptionsSetController.java:saveOptionSet:~130-170`; `CustomerOptionSet.java:17-27`
**Discovery Method:** Direct Source Read
**Statement:** The same (option, value) pairing may be bound only once within a store; attempting to create a duplicate binding is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
FOR each existing set in store:
    IF set.optionId == optionId AND set.optionValueId == valueId:
        reject "message.optionset.optionassociationexists"; break
// backed by DB unique constraint (customer_option_id, customer_option_value_id)
```
**Data Dependencies:**
- Reads/Writes: customer_option_set
**Side Effects:** None on duplicate.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-option-sets {"optionId":"o-1","optionValueId":"v-1"}`
- Success: `201`
- Error Input: same pairing again
- Error Output: `409 {"error":"Conflict","message":"Option/value association already exists"}`

---

### BR-CUSTOPT-009: Option, value, set and attribute persistence create when new and update when existing

**Source Reference:** `CustomerOptionServiceImpl.java:saveOrUpdate:~47-58`; `CustomerOptionValueServiceImpl.java:saveOrUpdate:~50-62`; `CustomerOptionSetServiceImpl.java:saveOrUpdate:~63-73`; `CustomerAttributeServiceImpl.java:saveOrUpdate:~32-40`
**Discovery Method:** Direct Source Read
**Statement:** Saving any customer option, value, option-set, or per-shopper attribute creates a new record when it has no identity and updates the existing record otherwise.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```pseudocode
IF entity.id != null AND id > 0: update(entity)
ELSE: save/create(entity)
// NOTE: option-set uses id > 0 directly and would NPE on a null id (legacy defect, minor)
```
**Data Dependencies:**
- Writes: customer_option, customer_option_value, customer_option_set, customer_attribute
**Side Effects:** INSERT/UPDATE.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 1 | 1 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customer-options {"code":"X", ...}` then `PUT /api/v1/customer-options/{id} {...}`
- Success: `201` (create) then `200` (update)
- Error Input: `PUT /api/v1/customer-options/missing {...}`
- Error Output: `404 {"error":"NotFound","message":"Option not found"}`

---

### BR-CUSTOPT-010: A shopper attribute's option and value must exist and belong to the shopper's store

**Source Reference:** `CustomerPopulator.java:populate:~163-190`
**Discovery Method:** Direct Source Read
**Statement:** When assigning a custom attribute to a shopper, the referenced option and value must both exist and both belong to the same store as the shopper; otherwise the attribute is rejected.
**Intent:** Validation
**Weight:** Medium
**Logic:**
```pseudocode
option = getById(attr.optionId); IF null: throw "does not exist"
value = getById(attr.valueId); IF null: throw "does not exist"
IF option.store.id != store.id: throw "Invalid customer option id"
IF value.store.id != store.id: throw "Invalid customer option value id"
```
**Data Dependencies:**
- Reads: customer_option, customer_option_value, merchant_id
- Writes: customer_attribute
**Side Effects:** Throws (abort) on failure; on success adds attribute to the shopper.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 4 | 4 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 1 | 1 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 4 | 4 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/{id}/attributes {"optionId":"o-1","optionValueId":"v-1"}`
- Success: `200 {"attributes":[{"optionId":"o-1","optionValueId":"v-1"}]}`
- Error Input: `{"optionId":"o-1","optionValueId":"v-from-another-store"}`
- Error Output: `422 {"error":"Unprocessable","message":"Invalid customer option value id"}`

---

### BR-CUSTOPT-011: Text-type attributes store free text; choice-type attributes store a selected value

**Source Reference:** `CustomerAccountController.java:saveCustomerAttributes:~215-232`; `CustomerOptionType.java`
**Discovery Method:** Direct Source Read
**Statement:** For a text-type option, a shopper's attribute stores free text (or is cleared when blank); for a choice-type option (radio, select, checkbox), the attribute stores the selected value.
**Intent:** Routing
**Weight:** Medium
**Logic:**
```pseudocode
IF option.type == Text:
    IF notBlank(paramValue): set value + textValue
    ELSE: textValue = null
ELSE:
    set selected customerOptionValue
```
**Data Dependencies:**
- Writes: customer_attribute.customer_attr_txt_val, customer_attribute.option_value_id
**Side Effects:** Sets attribute fields before persist.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 3 | 3 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 1 | 1 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 2 | 2 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `POST /api/v1/customers/{id}/attributes {"optionId":"o-text","textValue":"blue"}`
- Success: `200 {"attributes":[{"optionId":"o-text","textValue":"blue"}]}`
- Error Input: `{"optionId":"o-choice"}` (choice type with no selected value)
- Error Output: `422 {"error":"Unprocessable","message":"A value must be selected for this option"}`

---

### BR-CUSTOPT-012: Saving attributes reconciles the submitted set (create, update, delete unselected)

**Source Reference:** `CustomerAccountController.java:saveCustomerAttributes:~180-260`
**Discovery Method:** Direct Source Read
**Statement:** When a shopper submits their attribute selections, the service creates newly selected attributes, updates changed ones, and deletes any previously stored attribute that was not resubmitted. A shopper holds at most one attribute per option.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```pseudocode
load existing attributes into map keyed by option id
FOR each submitted param:
    IF no existing attribute for option: create
    ELSE: remove from the "to-delete" working set
    apply text/choice value (BR-CUSTOPT-011)
    IF has id AND value null: delete; ELSE IF has id: update; ELSE: save
after loop: delete every remaining attribute in the working set (not resubmitted)
```
**Data Dependencies:**
- Writes: customer_attribute (INSERT/UPDATE/DELETE)
**Side Effects:** INSERT/UPDATE/DELETE of attributes; refresh of the shopper.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 5 | 5 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 3 | 3 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `PUT /api/v1/customers/{id}/attributes {"attributes":[{"optionId":"o-1","optionValueId":"v-1"}]}` (previously had o-2)
- Success: `200 {"attributes":[{"optionId":"o-1"}]}` (o-2 removed)
- Error Input: submit an attribute whose option does not belong to the store
- Error Output: `422 {"error":"Unprocessable","message":"Invalid customer option id"}`

---

### BR-CUSTOPT-013: Deleting a customer option cascades to its attributes and option-sets

**Source Reference:** `CustomerOptionServiceImpl.java:delete:~61-83`
**Discovery Method:** Direct Source Read
**Statement:** Removing a customer option first removes every shopper attribute that uses it and every option-set binding that references it, then removes the option itself.
**Intent:** State Transition
**Weight:** Medium
**[Placement: db (ON DELETE CASCADE) — PLACE-004]** Do NOT emit the row-by-row app-tier cascade below. The cascade is enforced declaratively by the DB: `customer_attribute.customer_option_id` and `customer_option_set.customer_option_id` already carry `ON DELETE CASCADE` (INV-CUSTOPT-011). The app deletes the option in ONE statement and the DB cascades.
**Logic:**
```pseudocode
attrs = getByOptionId(store, optionId); FOR each: delete
sets = listByOption(option, store); FOR each: delete
delete(option)
```
**Data Dependencies:**
- Writes: customer_attribute, customer_option_set, customer_option (DELETE)
**Side Effects:** Multi-table DELETE (application-managed cascade).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK

> **Note (modernization):** legacy performs a row-by-row app-tier cascade (N round-trips). Target SHOULD use DB ON DELETE CASCADE / set-based deletes (INV-CUST-011).

**Concrete Example:**
- Input: `DELETE /api/v1/customer-options/{id}`
- Success: `204` — option, its attributes, and its bindings removed
- Error Input: `DELETE /api/v1/customer-options/{id}` for an option in another store
- Error Output: `404 {"error":"NotFound","message":"Option is not part of this store"}`

---

### BR-CUSTOPT-014: Deleting a customer option value cascades to its attributes and option-sets

**Source Reference:** `CustomerOptionValueServiceImpl.java:delete:~64-84`
**Discovery Method:** Direct Source Read
**Statement:** Removing a customer option value first removes every shopper attribute that uses it and every option-set binding that references it, then removes the value itself.
**Intent:** State Transition
**Weight:** Medium
**Logic:**
```pseudocode
attrs = getByCustomerOptionValueId(store, valueId); FOR each: delete
sets = listByOptionValue(value, store); FOR each: delete
delete(value)
```
**Data Dependencies:**
- Writes: customer_attribute, customer_option_set, customer_option_value (DELETE)
**Side Effects:** Multi-table DELETE.
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 3 | 3 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 1 | 1 | OK |
| Outcomes | 1 | 1 | OK |
| Data writes | 3 | 3 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 1 | 1 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `DELETE /api/v1/customer-option-values/{id}`
- Success: `204`
- Error Input: `DELETE /api/v1/customer-option-values/{id}` for a value in another store
- Error Output: `404 {"error":"NotFound","message":"Value is not part of this store"}`

---

### BR-CUSTOPT-015: Only active and public options are shown to shoppers; admins see active options

**Source Reference:** `CustomerDashboardController.java:getCustomerOptions:~85-95`; `CustomerController.java:getCustomerOptions:~175`
**Discovery Method:** Direct Source Read
**Statement:** On the shopper-facing dashboard, only options that are both active and public are shown; on the administrative view, all active options are shown regardless of their public flag. The shopper's stored selections are shown against each option (text options display the stored text).
**Intent:** Authorization
**Weight:** Critical
**Logic:**
```pseudocode
// storefront
IF !option.active OR !option.publicOption: skip
// admin
IF !option.active: skip
```
**Data Dependencies:**
- Reads: customer_option.customer_opt_active, customer_option.customer_opt_public
**Side Effects:** None (read/render).
**Semantic Preservation:**
| Dimension | Source | Spec | Status |
|-----------|--------|------|--------|
| Control-flow | 2 | 2 | OK |
| Data-flow | 2 | 2 | OK |
| Constants | 0 | 0 | OK |
| State transitions | 0 | 0 | OK |
| Outcomes | 2 | 2 | OK |
| Data writes | 0 | 0 | OK |
| Integrations | 0 | 0 | OK |
| Error paths | 0 | 0 | OK |
**Preservation:** OK
**Concrete Example:**
- Input: `GET /api/v1/customers/{id}/available-options` (shopper context)
- Success: `200 {"options":[{"code":"NL","active":true,"public":true}]}` (inactive/private omitted)
- Error Input: `GET /api/v1/customers/{id}/available-options` with an id outside the store
- Error Output: `404 {"error":"NotFound","message":"Customer is not part of this store"}`
