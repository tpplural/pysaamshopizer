# MS-07 (tax) — Component Inventory

**Service ID**: MS-07
**Analysis mode**: Direct Source Read (no CAST)
**Legacy stack**: Java / Spring MVC, JPA/Hibernate, QueryDSL (Mysema)

## Legacy Components in Scope

| Component | Type | Path (under `initial-source/shopizer/`) | Rules |
|-----------|------|------------------------------------------|-------|
| `TaxServiceImpl` | Service (calc engine) | `sm-core/.../tax/service/TaxServiceImpl.java` | BR-TAX-001,002,004,005,006,007,008,009,011,012,013,014,015,016,020,021,022,023,024 |
| `TaxService` | Service interface | `sm-core/.../tax/service/TaxService.java` | (contract) |
| `TaxRateServiceImpl` | Service | `sm-core/.../tax/service/TaxRateServiceImpl.java` | BR-TAX-016 (delegation) |
| `TaxClassServiceImpl` | Service | `sm-core/.../tax/service/TaxClassServiceImpl.java` | BR-TAX-012,026 (delegation) |
| `TaxRateDaoImpl` | DAO (QueryDSL) | `sm-core/.../tax/dao/taxrate/TaxRateDaoImpl.java` | BR-TAX-017,018,019 |
| `TaxClassDaoImpl` | DAO (QueryDSL) | `sm-core/.../tax/dao/taxclass/TaxClassDaoImpl.java` | BR-TAX-012 (evidence),025 |
| `TaxRate` | Entity | `sm-core/.../tax/model/taxrate/TaxRate.java` | BR-TAX-027 + INV rows |
| `TaxRateDescription` | Entity | `sm-core/.../tax/model/taxrate/TaxRateDescription.java` | INV rows |
| `TaxClass` | Entity | `sm-core/.../tax/model/taxclass/TaxClass.java` | BR-TAX-025 + INV rows |
| `TaxConfiguration` | POJO (JSON) | `sm-core/.../tax/model/TaxConfiguration.java` | BR-TAX-002,003,010 |
| `TaxItem` | POJO (transient) | `sm-core/.../tax/model/TaxItem.java` | BR-TAX-020,023 (evidence) |
| `TaxBasisCalculation` | Enum | `sm-core/.../tax/model/TaxBasisCalculation.java` | BR-TAX-007 (evidence) |
| `TaxClassController` | Controller (admin) | `sm-shop/.../admin/controller/tax/TaxClassController.java` | BR-TAX-025,026 |
| `TaxRatesController` | Controller (admin) | `sm-shop/.../admin/controller/tax/TaxRatesController.java` | BR-TAX-027,028 |
| `TaxConfigurationController` | Controller (admin) | `sm-shop/.../admin/controller/tax/TaxConfigurationController.java` | BR-TAX-001,003 |

## Owned Data

| Table | Legacy origin |
|-------|---------------|
| `tax_class` | `TAX_CLASS` |
| `tax_rate` | `TAX_RATE` |
| `tax_rate_description` | `TAX_RATE_DESCRIPTION` |
| `tax_configuration` | JSON blob in `MERCHANT_CONFIGURATION` (key `TAX_CONFIG`), one document per store |

## External (not owned)

`country_id`, `zone_id`, `language_id` → MS-01 reference data; `merchant_store_id` → MS-03 store;
product tax-class association → MS-04 catalog. Calculation is invoked by MS-09 (order) at checkout.

## Disposition
- Components EXTRACTED (subject of ≥1 BR-ID): TaxServiceImpl, TaxRateDaoImpl, TaxClassDaoImpl, TaxClass, TaxRate, TaxConfiguration, TaxClassController, TaxRatesController, TaxConfigurationController.
- ACCOUNTED (thin delegation, folded into the rules they delegate to): TaxRateServiceImpl, TaxClassServiceImpl, TaxService (interface).
- Evidence-only (entity/POJO/enum providing constants + mappings, cited as additional source tokens): TaxRateDescription, TaxItem, TaxBasisCalculation.
- No dead code excluded; no black-box sub-calls (all callees are within-service service/DAO methods that are themselves extracted or thin delegators).
