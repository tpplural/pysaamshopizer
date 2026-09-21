"""SQLAlchemy 2.x ORM models for reference-data (MS-01).

One-to-one mapping of the executable DDL in spec/microservices/MS-01/02-domain-model.md.
Schema ``reference_data``; snake_case columns; identity PKs; all UNIQUE / NOT NULL / FK
constraints and the three hot-path indexes are declared here (they also live in the Alembic
migration, which is the authority for a fresh DB).

Descriptions carry ``language_code`` (a language-code string xref), NOT a FK to language —
matching the target ERD's cross-reference-by-code approach within this service (02-domain-model.md).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

SCHEMA = "reference_data"


# ─────────────────────────────────────────────────────────────
# LANGUAGE (maps to legacy LANGUAGE)
# ─────────────────────────────────────────────────────────────
class Language(Base):
    __tablename__ = "language"
    __table_args__ = (
        # INV-REF-002: legacy had NO unique constraint — the target ADDS it.
        UniqueConstraint("code", name="uq_language_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)  # BR-REF-RES-002
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NF-4 / BR-REF-LST-003
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ─────────────────────────────────────────────────────────────
# CURRENCY (maps to legacy CURRENCY)
# ─────────────────────────────────────────────────────────────
class Currency(Base):
    __tablename__ = "currency"
    __table_args__ = (
        UniqueConstraint("code", name="uq_currency_code"),
        UniqueConstraint("iso_code", name="uq_currency_iso_code"),
        UniqueConstraint("name", name="uq_currency_name"),  # INV-REF-003
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(3), nullable=False)  # BR-REF-RES-003, ISO-4217
    iso_code: Mapped[str] = mapped_column(String(3), nullable=False)  # platform-derived
    name: Mapped[str] = mapped_column(String(80), nullable=False)  # NF-2: real display name
    supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ─────────────────────────────────────────────────────────────
# GEOZONE (maps to legacy GEOZONE) — modeled, ships EMPTY (BR-REF-SEED-GEO finding)
# ─────────────────────────────────────────────────────────────
class Geozone(Base):
    __tablename__ = "geozone"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    descriptions: Mapped[list["GeozoneDescription"]] = relationship(
        back_populates="geozone", cascade="all, delete-orphan"
    )


class GeozoneDescription(Base):
    __tablename__ = "geozone_description"
    __table_args__ = (
        UniqueConstraint("geozone_id", "language_code", name="uq_geozone_desc"),  # INV-REF-006
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    geozone_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.geozone.id", ondelete="CASCADE"), nullable=False
    )
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    geozone: Mapped[Geozone] = relationship(back_populates="descriptions")


# ─────────────────────────────────────────────────────────────
# COUNTRY (maps to legacy COUNTRY)
# ─────────────────────────────────────────────────────────────
class Country(Base):
    __tablename__ = "country"
    __table_args__ = (
        UniqueConstraint("iso_code", name="uq_country_iso_code"),  # INV-REF-001
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    iso_code: Mapped[str] = mapped_column(String(2), nullable=False)  # BR-REF-RES-001
    supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    geozone_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.geozone.id"), nullable=True
    )  # always null in legacy (BR-REF-SEED-GEO)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    descriptions: Mapped[list["CountryDescription"]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )
    zones: Mapped[list["Zone"]] = relationship(back_populates="country")


class CountryDescription(Base):
    __tablename__ = "country_description"
    __table_args__ = (
        UniqueConstraint("country_id", "language_code", name="uq_country_desc"),  # INV-REF-006
        Index("ix_country_desc_lang_name", "language_code", "name"),  # BR-REF-LST-001 hot path
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.country.id", ondelete="CASCADE"), nullable=False
    )
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # BR-REF-LST-001

    country: Mapped[Country] = relationship(back_populates="descriptions")


# ─────────────────────────────────────────────────────────────
# ZONE (maps to legacy ZONE)
# ─────────────────────────────────────────────────────────────
class Zone(Base):
    __tablename__ = "zone"
    __table_args__ = (
        UniqueConstraint("code", name="uq_zone_code"),  # INV-REF-005 (global, not per-country)
        Index("ix_zone_country", "country_id"),  # hot path
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)  # BR-REF-RES-004
    country_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.country.id"), nullable=False
    )  # INV-REF-004: every zone has exactly one country
    geozone_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.geozone.id"), nullable=True
    )  # always null in legacy
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    country: Mapped[Country] = relationship(back_populates="zones")
    descriptions: Mapped[list["ZoneDescription"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )


class ZoneDescription(Base):
    __tablename__ = "zone_description"
    __table_args__ = (
        UniqueConstraint("zone_id", "language_code", name="uq_zone_desc"),  # INV-REF-006
        Index("ix_zone_desc_lang_name", "language_code", "name"),  # BR-REF-LST-002 hot path
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    zone_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.zone.id", ondelete="CASCADE"), nullable=False
    )
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # BR-REF-LST-002

    zone: Mapped[Zone] = relationship(back_populates="descriptions")
