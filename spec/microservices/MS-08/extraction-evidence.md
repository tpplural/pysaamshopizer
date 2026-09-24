# MS-08 Shipping Service — Extraction Evidence

**Analysis mode**: Direct Source Read (no CAST). All rules extracted by reading actual source in this session.

## Source Files Processed

| # | File | Lines read | Sections read | Rules Extracted | Vectors Counted |
|---|------|-----------|---------------|-----------------|-----------------|
| 1 | `sm-core/.../shipping/service/ShippingServiceImpl.java` | full (~690) | config load; save config; getShippingQuote pipeline (country gates, module selection, order total, free shipping, options price selection); getShippingSummary; supported countries; calculateOrderTotal; getPackagesDetails; requiresShipping | BR-SHIP-001..019, 031 | ✅ |
| 2 | `sm-core/.../integration/shipping/impl/DefaultPackagingImpl.java` | full (~360) | box packing (config load, fit validation, bin-packing, output); per-item packing; PackingBox helper | BR-SHIP-020..025 | ✅ |
| 3 | `sm-core/.../integration/shipping/impl/CustomWeightBasedShippingQuote.java` | full (~135) | custom module config load; getShippingQuotes (region match, weight sum, bracket lookup) | BR-SHIP-026..029 | ✅ |
| 4 | `sm-shop/.../shipping/CustomShippingMethodsController.java` | full (~560) | addCustomRegion, addCountryToRegion, addPrice (parse+validate+sort), delete flows, paging | BR-SHIP-030, 032 | ✅ |
| 5 | `sm-shop/.../shipping/ShippingOptionsController.java` | full (~175) | display/save options (money parse, flags) | BR-SHIP-030, 033 | ✅ |
| 6 | `sm-shop/.../shipping/ShippingPackagingController.java` | full (~150) | display/save packaging (2dp weight rounding, box dims, package type) | BR-SHIP-030, 034 | ✅ |
| 7 | `sm-shop/.../shipping/ShippingConfigsController.java` | full (~230) | mode save; supported-countries paging/update | BR-SHIP-030 | ✅ |
| 8 | `sm-shop/.../shipping/ShippingMethodsController.java` | full (~200) | list/save/delete methods (delete lacks role guard) | BR-SHIP-030 | ✅ |
| 9 | `sm-core-modules/.../integration/shipping/model/ShippingQuoteModule.java` | full | quote provider SPI (extension point) | supports BR-SHIP-006/012/031 |  n/a (interface) |
| 10 | `sm-core-modules/.../integration/shipping/model/Packaging.java` | full | packaging SPI (extension point) | supports BR-SHIP-009/020..025 | n/a (interface) |
| 11 | `sm-core-model/.../shipping/model/ShippingConfiguration.java` | full (~330) | config fields, JSON binding, enum defaults | supports BR-SHIP-001,009,010,011,033,034 | ✅ |
| 12 | `sm-core-modules/.../model/CustomShippingQuotesConfiguration.java` | full | regions holder + JSON | supports BR-SHIP-026,032 | ✅ |
| 13 | `sm-core-modules/.../model/CustomShippingQuotesRegion.java` | full | region (name, countries, brackets) | supports BR-SHIP-027,029,032 | ✅ |
| 14 | `sm-core-modules/.../model/CustomShippingQuoteWeightItem.java` | full | weight→price bracket | supports BR-SHIP-029,032 | ✅ |
| 15 | `sm-core-model/.../shipping/model/ShippingQuote.java` | full | quote result + return-code constants | supports BR-SHIP-003..013 | ✅ |
| 16 | `sm-core/.../constants/ShippingConstants.java` | full | SHIPPING_CONFIG key constant | supports BR-SHIP-001 | ✅ |
| 17 | Enums: `ShippingType`, `ShippingBasisType`, `ShippingOptionPriceType`, `ShippingPackageType`, `ShippingDescription` | full | enum value sets | supports BR-SHIP-003,009,016,017 | ✅ |
| 18 | Models: `ShippingOption`, `ShippingSummary`, `ShippingProduct`, `PackageDetails` | full | transient data holders | supports BR-SHIP-014..019,028 | ✅ |

## Source File Resolution (escalation)

- The stated in-scope SPI files `ShippingQuoteModule.java` and `Packaging.java` are interfaces; the
  concrete engines were located via directory scan under `sm-core/.../integration/shipping/impl/`:
  `DefaultPackagingImpl.java` and `CustomWeightBasedShippingQuote.java`. Both read in full.
- Model sources confirmed under `sm-core-model/.../business/shipping/model/` (not sm-core), consistent
  with the note in the segment brief.

## Not Found

None. Every referenced component was located and read.

## Extraction Status
- Files total (in scope): 18 groups
- Files processed: 18/18
- Rules extracted: 34 (BR-SHIP-001..034)
- Source vectors complete: yes (8-dimension per rule; source counts from this-session reads,
  reconciled with the Phase-1 per-component vector table)

## Session Log
| Session | Files Processed | Rules Added | Notes |
|---------|-----------------|-------------|-------|
| 1 | 1-18 (all) | 34 | Single pass; orchestrator + 2 engines + 5 controllers + SPI + models/enums |
