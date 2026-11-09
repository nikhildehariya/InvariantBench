"""Buggy LLM Baseline Implementation for Task 10.

Representative of typical frontier LLM outputs:
1. Promotes keys to MRU before checking TTL, corrupting the LRU queue on expired hits.
2. Directly mutates OrderedDict during iteration in prune_expired(), causing RuntimeError.
3. Blindly pops the valid LRU entry on capacity overflow instead of checking if any item is expired.
4. Uses time.time() instead of time.monotonic(), making it vulnerable to wall-clock skew.
"""

import time
import threading
from collections import OrderedDict
from typing import Any, Optional


class ConcurrentLRUTTLCache:
    def __init__(self, capacity: int, default_ttl: Optional[float] = None):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key not in self._cache:
                return default

            # LLM TRAP 1: Promotes to MRU BEFORE checking expiration!
            self._cache.move_to_end(key)

            value, expire_at = self._cache[key]
            # LLM TRAP 2: Uses time.time() instead of time.monotonic()
            if expire_at is not None and time.time() >= expire_at:
                del self._cache[key]
                return default

            return value

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            eff_ttl = ttl if ttl is not None else self.default_ttl
            expire_at = (time.time() + eff_ttl) if eff_ttl is not None else None

            if key in self._cache:
                self._cache[key] = (value, expire_at)
                self._cache.move_to_end(key)
                return

            # LLM TRAP 3: Blindly pops the LRU item without checking if any expired item exists!
            if len(self._cache) >= self.capacity:
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
            now = time.time()
            count = 0
            # LLM TRAP 4: Mutates OrderedDict during direct iteration!
            for k in list(self._cache.keys()):
                _, exp = self._cache[k]
                if exp is not None and now >= exp:
                    del self._cache[k]
                    count += 1
            return count

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)
