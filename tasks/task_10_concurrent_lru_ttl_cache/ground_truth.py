"""Ground Truth Reference Implementation for Task 10: Concurrent LRU-TTL Cache."""

import time
import threading
from collections import OrderedDict
from typing import Any, Optional


class ConcurrentLRUTTLCache:
    def __init__(self, capacity: int, default_ttl: Optional[float] = None):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.default_ttl = default_ttl
        # _cache maps key -> (value, expire_at)
        self._cache: OrderedDict[str, tuple[Any, Optional[float]]] = OrderedDict()
        self._lock = threading.RLock()

    def _is_expired(self, expire_at: Optional[float], now: float) -> bool:
        return expire_at is not None and now >= expire_at

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            now = time.monotonic()
            if key not in self._cache:
                return default

            value, expire_at = self._cache[key]
            if self._is_expired(expire_at, now):
                # Atomic immediate eviction without MRU promotion
                del self._cache[key]
                return default

            # Unexpired: promote to MRU (end of OrderedDict)
            self._cache.move_to_end(key)
            return value

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            now = time.monotonic()
            eff_ttl = ttl if ttl is not None else self.default_ttl
            expire_at = (now + eff_ttl) if eff_ttl is not None else None

            if key in self._cache:
                # Update existing key and move to MRU
                self._cache[key] = (value, expire_at)
                self._cache.move_to_end(key)
                return

            # If at full capacity, first try to prune any expired entries
            if len(self._cache) >= self.capacity:
                # Find the first expired key in order
                expired_key = None
                for k, (_, exp) in self._cache.items():
                    if self._is_expired(exp, now):
                        expired_key = k
                        break

                if expired_key is not None:
                    del self._cache[expired_key]
                else:
                    # All items are valid: pop standard LRU (first item)
                    self._cache.popitem(last=False)

            self._cache[key] = (value, expire_at)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def prune_expired(self) -> int:
        with self._lock:
            now = time.monotonic()
            # Capture snapshot of expired keys to avoid mutating during iteration
            expired_keys = [
                k for k, (_, exp) in self._cache.items()
                if self._is_expired(exp, now)
            ]
            for k in expired_keys:
                self._cache.pop(k, None)
            return len(expired_keys)

    def __len__(self) -> int:
        with self._lock:
            now = time.monotonic()
            # Active non-expired count
            return sum(1 for _, exp in self._cache.values() if not self._is_expired(exp, now))
