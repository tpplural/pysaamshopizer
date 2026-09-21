"""SQLAlchemy engine / session wiring for reference-data (MS-01).

The service owns the ``reference_data`` PostgreSQL schema. DATABASE_URL is the PRIMARY
persistence per spec/shared/env-schema.md. A SQLite fallback is used ONLY by unit tests
(never as the default runtime) — see tests/conftest.py.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all reference-data ORM models."""


_settings = get_settings()

# ``future=True`` engine (SQLAlchemy 2.x style). pool_pre_ping keeps long-lived pools healthy.
engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
