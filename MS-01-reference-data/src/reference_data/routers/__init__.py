"""HTTP routers for reference-data (MS-01). All routes mounted under /api/v1/reference."""

from .countries import router as countries_router
from .currencies import router as currencies_router
from .form_support import router as form_support_router
from .languages import router as languages_router
from .zones import router as zones_router

__all__ = [
    "countries_router",
    "currencies_router",
    "form_support_router",
    "languages_router",
    "zones_router",
]
