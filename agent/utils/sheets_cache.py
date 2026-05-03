"""
Sheets Cache Layer — rate limit protection for Google Sheets API.

Provides:
- TTL-based read cache (60s default) to avoid repeated reads
- Batched write queue (flush every 10 items or 2 seconds)
- Thread-safe operations

Used by all agent modules that interact with Google Sheets.
"""

from time import time
from threading import Lock
from collections import OrderedDict


class TTLCache:
    """Simple TTL cache implementation (no external dependency needed)."""

    def __init__(self, maxsize: int = 1000, ttl: float = 60.0):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = Lock()

    def get(self, key):
        """Get value if exists and not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            if time() - self._timestamps[key] > self.ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key, value):
        """Set value with current timestamp."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            self._timestamps[key] = time()
            while len(self._cache) > self.maxsize:
                oldest_key, _ = self._cache.popitem(last=False)
                del self._timestamps[oldest_key]

    def __contains__(self, key):
        return self.get(key) is not None

    def invalidate(self, key):
        """Remove a specific key from cache."""
        with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


class SheetsCache:
    """
    Caching layer for Google Sheets API calls.

    - Read cache: TTL-based, avoids hitting API for repeated reads
    - Write queue: batches writes to reduce API calls
    """

    def __init__(self, read_ttl: float = 60.0, flush_threshold: int = 10,
                 flush_interval: float = 2.0):
        self.read_cache = TTLCache(maxsize=1000, ttl=read_ttl)
        self.write_queue = []
        self.write_lock = Lock()
        self.last_flush = 0.0
        self.flush_threshold = flush_threshold
        self.flush_interval = flush_interval
        self._api_read_fn = None
        self._api_write_fn = None

    def set_api_functions(self, read_fn, write_fn):
        """
        Set the actual API functions for reading/writing.

        Args:
            read_fn: callable(sheet_id, range_a1) -> list of rows
            write_fn: callable(sheet_id, rows) -> None
        """
        self._api_read_fn = read_fn
        self._api_write_fn = write_fn

    def read(self, sheet_id: str, range_a1: str):
        """
        Read from sheet with caching.

        Returns cached result if available and fresh,
        otherwise fetches from API.
        """
        cache_key = f"{sheet_id}:{range_a1}"
        cached = self.read_cache.get(cache_key)
        if cached is not None:
            return cached

        if self._api_read_fn is None:
            raise RuntimeError("API read function not configured. Call set_api_functions() first.")

        data = self._api_read_fn(sheet_id, range_a1)
        self.read_cache.set(cache_key, data)
        return data

    def queue_write(self, sheet_id: str, row_data: list):
        """
        Queue a row for batched writing.

        Automatically flushes when threshold or interval is reached.
        """
        with self.write_lock:
            self.write_queue.append({
                "sheet_id": sheet_id,
                "data": row_data,
                "timestamp": time()
            })

        if self._should_flush():
            self.flush()

    def _should_flush(self) -> bool:
        """Check if we should flush the write queue."""
        if len(self.write_queue) >= self.flush_threshold:
            return True
        if self.write_queue and (time() - self.last_flush) > self.flush_interval:
            return True
        return False

    def flush(self):
        """Flush all pending writes to the API."""
        with self.write_lock:
            if not self.write_queue:
                return

            if self._api_write_fn is None:
                raise RuntimeError("API write function not configured. Call set_api_functions() first.")

            # Group writes by sheet_id for batching
            by_sheet = {}
            for item in self.write_queue:
                sid = item["sheet_id"]
                if sid not in by_sheet:
                    by_sheet[sid] = []
                by_sheet[sid].append(item["data"])

            # Execute batched writes
            for sheet_id, rows in by_sheet.items():
                self._api_write_fn(sheet_id, rows)

            self.write_queue.clear()
            self.last_flush = time()

    def invalidate_read(self, sheet_id: str, range_a1: str):
        """Invalidate a specific read cache entry."""
        cache_key = f"{sheet_id}:{range_a1}"
        self.read_cache.invalidate(cache_key)

    def clear_all(self):
        """Clear read cache and flush pending writes."""
        self.flush()
        self.read_cache.clear()
