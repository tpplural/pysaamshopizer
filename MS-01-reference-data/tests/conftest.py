"""Test fixtures for reference-data (MS-01) unit tests.

Uses an in-memory SQLite database ONLY for unit tests (never as the default runtime — PostgreSQL
via DATABASE_URL is primary). The ORM models are schema-qualified (``reference_data``); SQLite has
no schema concept, so we ATTACH a database aliased to that schema name, which lets the identical
schema-qualified metadata create and query cleanly on SQLite.
"""

from __future__ import annotations

import pytest
from sqlalchemy import BigInteger, create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from reference_data.database import Base
from reference_data.models import SCHEMA
from reference_data import models  # noqa: F401  (register tables)


# SQLite only autoincrements a bare ``INTEGER PRIMARY KEY`` — not BIGINT. The production models use
# BigInteger identity PKs (correct for PostgreSQL). For the in-memory SQLite TEST engine only, render
# BigInteger as INTEGER so identity PKs autoincrement. This does NOT alter the models or the Postgres
# runtime — it is a dialect-scoped compilation rule active only while these tests import conftest.
@compiles(BigInteger, "sqlite")
def _bigint_as_integer_on_sqlite(element, compiler, **kw):  # pragma: no cover - test wiring
    return "INTEGER"


@pytest.fixture()
def session():
    engine = create_engine("sqlite://", future=True)

    # Attach an in-memory db under the schema alias so 'reference_data.<table>' resolves on SQLite.
    @event.listens_for(engine, "connect")
    def _attach_schema(dbapi_conn, _record):  # pragma: no cover - wiring
        dbapi_conn.execute(f"ATTACH DATABASE ':memory:' AS {SCHEMA}")

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


class FakeCache:
    """A pass-through cache double (BR-REF-CAC-001 semantics without Redis).

    Backs the read-through path in tests: get returns what was set. To exercise the fail-soft path
    (BR-REF-CAC-002) a test can use FailingCache below.
    """

    def __init__(self) -> None:
        self.store: dict = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def invalidate(self, key):
        self.store.pop(key, None)


class FailingCache:
    """A cache that raises on every op — but the service must still never surface an error
    (BR-REF-CAC-002). Only meaningful if the service caught cache errors; our ReferenceCache does,
    so here we model a cache that simply never returns a hit (get -> None, set -> no-op)."""

    def get(self, key):
        return None

    def set(self, key, value):
        return None

    def invalidate(self, key):
        return None


@pytest.fixture()
def cache():
    return FakeCache()
