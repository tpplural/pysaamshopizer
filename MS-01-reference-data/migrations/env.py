"""Alembic environment for reference-data (MS-01).

Reads DATABASE_URL from the app config (single source of truth) and targets the
``reference_data`` schema. Autogenerate is scoped to that schema.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from reference_data.config import get_settings
from reference_data.database import Base
from reference_data import models  # noqa: F401  (import registers the tables on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.database_url)

target_metadata = Base.metadata
TARGET_SCHEMA = _settings.db_schema


def _include_object(obj, name, type_, reflected, compare_to):
    # Only manage objects in our owned schema.
    if type_ == "table":
        return getattr(obj, "schema", None) in (TARGET_SCHEMA, None)
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=_settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        version_table_schema=TARGET_SCHEMA,
        include_object=_include_object,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=TARGET_SCHEMA,
            include_object=_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
