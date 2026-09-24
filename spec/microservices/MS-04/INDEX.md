# MS-04 Catalog Service — Specification Index

**Service ID:** MS-04
**Service name:** catalog
**Port:** 8004
**Database schema:** `catalog_schema`
**Priority:** 1 (Core — the product aggregate anchor)
**Source stack:** Java / Spring MVC / JPA-Hibernate + QueryDSL (Shopizer 2.0.1)
**Extraction mode:** Direct Source Read (Phase 4 deep pass)

## Purpose
The catalog service owns the product aggregate and its satellite concerns: products and their lifecycle,
the category taxonomy, manufacturers/brands, the option/value/attribute configuration engine, the pricing
engine, product media, and customer reviews. It is the largest service in the engagement, spanning four
Phase-1 assessment segments and seven business-rule groups.

## Metadata
| Metric | Value |
|--------|-------|
| Business rules | 104 |
| Owned tables | 22 |
| Endpoints (operations) | 59 |
| Data invariants | 10 |
| Rule groups | 7 (CATPROD, CATCAT, CATMAN, CATOPT, CATPRICE, CATIMG, CATREV) |

## Rule group breakdown
| Group | Domain | Rules |
|-------|--------|-------|
| BR-CATPROD | Product aggregate & lifecycle | 26 |
| BR-CATCAT | Category taxonomy | 14 |
| BR-CATMAN | Manufacturer / brand | 7 |
| BR-CATOPT | Options, values & attributes | 27 |
| BR-CATPRICE | Pricing engine | 15 |
| BR-CATIMG | Images & media | 7 |
| BR-CATREV | Reviews | 8 |
| **Total** | | **104** |

## Files
| File | Content |
|------|---------|
| `00-component-inventory.md` | Legacy source components mapped to this service |
| `01-business-rules.md` | 104 business rules with semantic statements, source references, 8-dimension preservation, concrete examples |
| `02-domain-model.md` | Executable PostgreSQL DDL, entity state models, data invariants |
| `03-api-design.md` | Endpoint catalog with driving BR-IDs |
| `04-api-contract.yaml` | OpenAPI 3.1 contract (naming authority) |
| `06-completion-summary.md` | Accurate counts, net-new findings, greenfield rules |
| `extraction-evidence.md` | Source files read + coverage |
| `FINAL-EXTRACTION-COMPLETE.md` | Completion marker |

> `05-dependencies.md` is intentionally NOT produced here — it is generated in Stage 1.5 after all provider
> service contracts exist.
