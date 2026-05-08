# Rate-limited data fetcher with in-memory cache for akshare API calls
import time
import threading
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class _CacheEntry:
    __slots__ = ("data", "expires_at")

    def __init__(self, data: Any, expires_at: float):
        self.data = data
        self.expires_at = expires_at

    def is_fresh(self) -> bool:
        return time.time() < self.expires_at


class DataFetcher:
    """Thread-safe rate-limited data fetcher with in-memory TTL cache."""

    def __init__(self, default_ttl: float = 1800, min_interval: float = 1.0):
        self._cache: dict[str, _CacheEntry] = {}
        self._last_call: dict[str, float] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl
        self._min_interval = min_interval

    def fetch(
        self,
        key: str,
        func: Callable[[], Any],
        ttl: Optional[float] = None,
    ) -> Any:
        """Fetch data with caching and rate limiting.

        Args:
            key: Cache key (e.g. 'industry_summary_ths').
            func: Callable that returns the data (usually an akshare function).
            ttl: Cache TTL in seconds. Defaults to self._default_ttl.

        Returns:
            Cached or fresh data.
        """
        ttl = ttl if ttl is not None else self._default_ttl
        now = time.time()

        with self._lock:
            entry = self._cache.get(key)
            if entry and entry.is_fresh():
                logger.debug("cache HIT: %s", key)
                return entry.data

        # Rate limit: wait if called too recently
        with self._lock:
            last = self._last_call.get(key, 0)
            wait = self._min_interval - (now - last)
            if wait > 0:
                time.sleep(wait)
            self._last_call[key] = time.time()

        logger.info("cache MISS: %s, calling API...", key)
        t0 = time.time()
        try:
            data = func()
        except Exception:
            # On API failure, return stale cache if available
            with self._lock:
                stale = self._cache.get(key)
            if stale:
                logger.warning("API failed for %s, returning stale cache", key)
                return stale.data
            raise
        elapsed = time.time() - t0
        logger.info("cache MISS: %s, API returned in %.1fs", key, elapsed)

        with self._lock:
            self._cache[key] = _CacheEntry(data, time.time() + ttl)

        return data

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._last_call.clear()


# Global singleton
fetcher = DataFetcher(default_ttl=1800, min_interval=1.0)
