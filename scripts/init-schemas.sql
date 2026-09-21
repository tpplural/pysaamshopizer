-- Per-service schemas in the shared dev database (db-per-service in production).
-- Schema names match modernization/services-composition.md.
CREATE SCHEMA IF NOT EXISTS reference_data;   -- MS-01
CREATE SCHEMA IF NOT EXISTS identity_admin;   -- MS-02
CREATE SCHEMA IF NOT EXISTS merchant_store;   -- MS-03
CREATE SCHEMA IF NOT EXISTS catalog;          -- MS-04
CREATE SCHEMA IF NOT EXISTS customer;         -- MS-05
CREATE SCHEMA IF NOT EXISTS cart;             -- MS-06
CREATE SCHEMA IF NOT EXISTS tax;              -- MS-07
CREATE SCHEMA IF NOT EXISTS shipping;         -- MS-08
CREATE SCHEMA IF NOT EXISTS "order";          -- MS-09 (quoted — reserved word)
CREATE SCHEMA IF NOT EXISTS payment;          -- MS-10
CREATE SCHEMA IF NOT EXISTS content_cms;      -- MS-11
