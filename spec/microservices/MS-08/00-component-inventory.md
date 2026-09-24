# MS-08 Shipping Service — Component Inventory

**Service ID**: MS-08
**Analysis mode**: Direct Source Read (no CAST)

Legacy components mapped to this service. Roots under `initial-source/shopizer/` (excluding `/target/`).

## Rule-bearing components (business logic — read in full)

| Component | Module | Role | Rules |
|-----------|--------|------|-------|
| `ShippingServiceImpl.java` | sm-core | Quote orchestrator (getShippingQuote pipeline, config load, order total, package strategy, summary, supported countries) | BR-SHIP-001..019, 031 |
| `DefaultPackagingImpl.java` | sm-core (integration/shipping/impl) | Packaging engine — box bin-packing + per-item | BR-SHIP-020..025 |
| `CustomWeightBasedShippingQuote.java` | sm-core (integration/shipping/impl) | Custom weight-based quote engine (region → weight-range → price) | BR-SHIP-026..029 |
| `CustomShippingMethodsController.java` | sm-shop | Weight-based region/country/price authoring | BR-SHIP-030, 032 |
| `ShippingOptionsController.java` | sm-shop | Free-shipping / handling / tax / price-type authoring | BR-SHIP-030, 033 |
| `ShippingPackagingController.java` | sm-shop | Box dimensions + package type authoring | BR-SHIP-030, 034 |
| `ShippingConfigsController.java` | sm-shop | Shipping mode + supported-countries authoring | BR-SHIP-030 |
| `ShippingMethodsController.java` | sm-shop | Provider list / save / delete (delete lacks role guard) | BR-SHIP-030 |

## SPI / extension-point contracts (interfaces — no formulas)

| Component | Module | Role |
|-----------|--------|------|
| `ShippingQuoteModule.java` | sm-core-modules | Quote provider SPI (extension point EXT-SHIP-001) |
| `Packaging.java` | sm-core-modules | Packaging SPI (extension point EXT-SHIP-002) |

## Configuration / model components (data holders)

| Component | Module | Role |
|-----------|--------|------|
| `ShippingConfiguration.java` | sm-core-model | Per-store shipping config document (→ shipping_configuration) |
| `CustomShippingQuotesConfiguration.java` | sm-core-modules | Weight-based config document (→ custom_weight_quote_configuration) |
| `CustomShippingQuotesRegion.java` | sm-core-modules | Region within weight-based config |
| `CustomShippingQuoteWeightItem.java` | sm-core-modules | Weight→price bracket |
| `CustomShippingQuoteItem.java` | sm-core-modules | Abstract price holder |
| `ShippingQuote.java` | sm-core-model | Transient quote result + return-code constants |
| `ShippingOption.java` | sm-core-model | Transient option |
| `ShippingSummary.java` | sm-core-model | Transient summary |
| `ShippingProduct.java` | sm-core-model | Item + quantity wrapper |
| `PackageDetails.java` | sm-core-model | Computed package |
| `ShippingConstants.java` | sm-core | Config key constants |
| Enums: `ShippingType`, `ShippingBasisType`, `ShippingOptionPriceType`, `ShippingPackageType`, `ShippingDescription` | sm-core-model | Enumerations |

## Out of scope (external carrier gateways — documented, not extracted)

| Component | Reason |
|-----------|--------|
| `UPSShippingQuote.java` | External carrier gateway plug-in (UPS) — separate carrier-integration concern |
| `USPSShippingQuote.java` | External carrier gateway plug-in (USPS) |
| `CanadaPostShippingQuote.java` | External carrier gateway plug-in (Canada Post) |

These are additional `ShippingQuoteModule` implementations reached through the same provider extension
point; their carrier-specific internals are not modelled here.
