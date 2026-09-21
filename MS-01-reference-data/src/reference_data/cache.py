"""Application cache abstraction for reference-data (MS-01).

Backs BR-REF-CAC-001 (read-through memoization of reference lists with derived keys) and is the
fail-soft point for BR-REF-CAC-002 (a cache backend error NEVER surfaces — it degrades to a store
load). Values are JSON-serialized. The legacy cache had NO eviction; the target keeps the lists
cached but adds a TTL + an explicit ``invalidate`` hook (BR-REF-CAC-001 target note).

Key templates preserved from the legacy segment (BR-REF-CAC-001 Logic):
  COUNTRIES_<lang>          | ZONES_<countryIso>_<lang> | ZONES_<lang> | LANGUAGES
  CREDIT_CARD_YEARS         | MONTHS_OF_YEAR                                       (BR-REF-API-003)
"""

from __future__ import annotations

import json
import logging
from typing import Any

try:  # redis is a runtime dep; guarded so unit tests can run without it.
    import redis as _redis
except Exception:  # pragma: no cover - import guard
    _redis = None  # type: ignore[assignment]

logger = logging.getLogger("reference_data.cache")


class ReferenceCache:
    """Thin JSON cache over Redis with fail-soft semantics (BR-REF-CAC-002).

    Any Redis error on get/set is logged and swallowed: ``get`` returns None (forcing a store
    load), ``set`` is a no-op. The read path therefore never raises because of the cache.
    """

    # ── Key templates (BR-REF-CAC-001) ──────────────────────────
    @staticmethod
    def countries_key(language_code: str) -> str:
        return f"COUNTRIES_{language_code}"

    @staticmethod
    def zones_country_key(country_iso_code: str, language_code: str) -> str:
        return f"ZONES_{country_iso_code}_{language_code}"

    @staticmethod
    def zones_lang_key(language_code: str) -> str:
        return f"ZONES_{language_code}"

    LANGUAGES_KEY = "LANGUAGES"
    CREDIT_CARD_YEARS_KEY = "CREDIT_CARD_YEARS"
    MONTHS_OF_YEAR_KEY = "MONTHS_OF_YEAR"

    def __init__(self, url: str | None, ttl_seconds: int = 3600, enabled: bool = True) -> None:
        self._ttl = ttl_seconds
        self._client: Any | None = None
        if enabled and url and _redis is not None:
            try:
                self._client = _redis.Redis.from_url(url, decode_responses=True)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("reference cache init failed (fail-soft, no cache): %s", exc)
                self._client = None

    def get(self, key: str) -> Any | None:
        # BR-REF-CAC-001 read-through hit; BR-REF-CAC-002 fail-soft on error.
        if self._client is None:
            return None
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:
            logger.error("reference cache get(%s) failed (fail-soft): %s", key, exc)
            return None

    def set(self, key: str, value: Any) -> None:
        # BR-REF-CAC-001 store-on-miss; BR-REF-CAC-002 fail-soft on error.
        if self._client is None:
            return
        try:
            self._client.set(key, json.dumps(value), ex=self._ttl)
        except Exception as exc:
            logger.error("reference cache set(%s) failed (fail-soft): %s", key, exc)

    def invalidate(self, key: str) -> None:
        # Explicit invalidation hook the legacy cache lacked (BR-REF-CAC-001 target note).
        if self._client is None:
            return
        try:
            self._client.delete(key)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("reference cache invalidate(%s) failed (fail-soft): %s", key, exc)
