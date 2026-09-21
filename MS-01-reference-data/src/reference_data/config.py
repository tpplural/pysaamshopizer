"""Runtime configuration for reference-data (MS-01).

Config keys per spec/shared/env-schema.md. reference-data reads:
  - DATABASE_URL (required)
  - REDIS_URL    (required — cache-using service, BR-REF-CAC-001/002)
  - SERVICE_PORT (default 8001)
Reference data is GLOBAL/tenant-neutral: NO OIDC audience scoping is enforced here beyond
optional auth, and there is NO messaging (no MESSAGE_BROKER_URL).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # SQLAlchemy DSN. PRIMARY runtime persistence (env-schema.md: required, all services).
    database_url: str = "postgresql+psycopg://saam:saam_local@localhost:5432/shopizer_dev"

    # Redis DSN — backs the reference-list memoization cache (BR-REF-CAC-001) and the
    # credit-card year/month lists (BR-REF-API-003). Fail-soft on cache errors (BR-REF-CAC-002).
    redis_url: str = "redis://localhost:6379/0"

    # HTTP port (env-schema.md: 8001 for MS-01).
    service_port: int = 8001

    log_level: str = "INFO"

    # Owned PostgreSQL schema (db-per-service in prod; per-schema in shared dev DB).
    db_schema: str = "reference_data"

    # Redis cache TTL (seconds) for the read-through reference lists. Legacy had NO eviction;
    # the target keeps the lists cached but adds an explicit TTL + invalidation hook (BR-REF-CAC-001).
    cache_ttl_seconds: int = 3600

    # Test mode degrades a missing/unavailable cache to a no-op instead of failing
    # (infrastructure-patterns.md Test-mode isolation; BR-REF-CAC-002 fail-soft).
    test_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
