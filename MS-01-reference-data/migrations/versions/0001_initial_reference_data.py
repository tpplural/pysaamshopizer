"""Initial reference-data schema (MS-01).

Creates the ``reference_data`` schema and all tables / constraints / indexes exactly as the
executable DDL in spec/microservices/MS-01/02-domain-model.md.

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "reference_data"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

    # ── LANGUAGE ────────────────────────────────────────────────
    op.create_table(
        "language",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_language_code"),
        schema=SCHEMA,
    )

    # ── CURRENCY ────────────────────────────────────────────────
    op.create_table(
        "currency",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("iso_code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("supported", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_currency_code"),
        sa.UniqueConstraint("iso_code", name="uq_currency_iso_code"),
        sa.UniqueConstraint("name", name="uq_currency_name"),
        schema=SCHEMA,
    )

    # ── GEOZONE (+ description) — ships EMPTY ────────────────────
    op.create_table(
        "geozone",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=40), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_table(
        "geozone_description",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("geozone_id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["geozone_id"], [f"{SCHEMA}.geozone.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("geozone_id", "language_code", name="uq_geozone_desc"),
        schema=SCHEMA,
    )

    # ── COUNTRY (+ description) ──────────────────────────────────
    op.create_table(
        "country",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("iso_code", sa.String(length=2), nullable=False),
        sa.Column("supported", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("geozone_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["geozone_id"], [f"{SCHEMA}.geozone.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("iso_code", name="uq_country_iso_code"),
        schema=SCHEMA,
    )
    op.create_table(
        "country_description",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("country_id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["country_id"], [f"{SCHEMA}.country.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_id", "language_code", name="uq_country_desc"),
        schema=SCHEMA,
    )

    # ── ZONE (+ description) ─────────────────────────────────────
    op.create_table(
        "zone",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("country_id", sa.BigInteger(), nullable=False),
        sa.Column("geozone_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["country_id"], [f"{SCHEMA}.country.id"]),
        sa.ForeignKeyConstraint(["geozone_id"], [f"{SCHEMA}.geozone.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_zone_code"),
        schema=SCHEMA,
    )
    op.create_table(
        "zone_description",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("zone_id", sa.BigInteger(), nullable=False),
        sa.Column("language_code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["zone_id"], [f"{SCHEMA}.zone.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("zone_id", "language_code", name="uq_zone_desc"),
        schema=SCHEMA,
    )

    # ── Hot-path indexes (BR-REF-LST-001/002) ────────────────────
    op.create_index("ix_country_desc_lang_name", "country_description", ["language_code", "name"], schema=SCHEMA)
    op.create_index("ix_zone_desc_lang_name", "zone_description", ["language_code", "name"], schema=SCHEMA)
    op.create_index("ix_zone_country", "zone", ["country_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_zone_country", table_name="zone", schema=SCHEMA)
    op.drop_index("ix_zone_desc_lang_name", table_name="zone_description", schema=SCHEMA)
    op.drop_index("ix_country_desc_lang_name", table_name="country_description", schema=SCHEMA)
    op.drop_table("zone_description", schema=SCHEMA)
    op.drop_table("zone", schema=SCHEMA)
    op.drop_table("country_description", schema=SCHEMA)
    op.drop_table("country", schema=SCHEMA)
    op.drop_table("geozone_description", schema=SCHEMA)
    op.drop_table("geozone", schema=SCHEMA)
    op.drop_table("currency", schema=SCHEMA)
    op.drop_table("language", schema=SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
