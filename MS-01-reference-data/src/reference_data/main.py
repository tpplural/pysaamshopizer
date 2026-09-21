"""FastAPI application for reference-data (MS-01).

Mounts the 14 read endpoints under /api/v1/reference, wires the shared error handlers, exposes the
health probes from spec/shared/infrastructure-patterns.md, and runs the one-time atomic seed on
startup (only when the database is empty — BR-REF-SEED-001).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .config import get_settings
from .database import SessionLocal, engine
from .errors import register_exception_handlers
from .routers import (
    countries_router,
    currencies_router,
    form_support_router,
    languages_router,
    zones_router,
)
from .service import SeedService

logger = logging.getLogger("reference_data")

BASE_PATH = "/api/v1/reference"


def _run_startup_seed() -> None:
    """BR-REF-SEED-001/002: seed on startup only when empty; atomic (commit/rollback in populate)."""
    session = SessionLocal()
    try:
        seed = SeedService(session)
        if seed.is_empty():
            seeded = seed.populate()
            if seeded:
                logger.info("reference-data seed complete (Empty -> Seeded)")
        else:
            logger.info("reference-data already seeded — seed skipped (BR-REF-SEED-001 guard)")
    except Exception as exc:  # a failed seed rolls back; aggregate stays Empty, retry next boot
        logger.error("reference-data seed failed and rolled back: %s", exc)
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # In dev/test Alembic runs as a separate step (see README); the seed runs here on startup.
    try:
        _run_startup_seed()
    except Exception as exc:  # never block startup on a seed failure (fail-soft boot)
        logger.error("startup seed error (continuing): %s", exc)
    yield


app = FastAPI(
    title="reference-data API",
    version="1.0.0",
    description="MS-01 reference-data — global read-only reference provider.",
    lifespan=lifespan,
)

register_exception_handlers(app)

# 14 read endpoints, all under the contract base path.
app.include_router(countries_router, prefix=BASE_PATH, tags=["countries"])
app.include_router(zones_router, prefix=BASE_PATH, tags=["zones"])
app.include_router(currencies_router, prefix=BASE_PATH, tags=["currencies"])
app.include_router(languages_router, prefix=BASE_PATH, tags=["languages"])
app.include_router(form_support_router, prefix=BASE_PATH, tags=["form-support"])


# ── Health probes (infrastructure-patterns.md) ──────────────────
@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy"}


@app.get("/health/alive", tags=["health"])
def health_alive() -> dict:
    return {"status": "healthy"}


@app.get("/health/ready", tags=["health"])
def health_ready():
    # Readiness = DB reachable. reference-data does NOT touch the bus, so no broker check.
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "unhealthy"})


def run() -> None:  # pragma: no cover - convenience entrypoint
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "reference_data.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        log_level=settings.log_level.lower(),
    )
