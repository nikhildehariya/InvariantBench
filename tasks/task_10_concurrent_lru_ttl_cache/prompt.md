# Task 10: Thread-Safe LRU-TTL Cache with Atomic Eviction

## Problem Description
High-performance in-memory caching systems require both capacity-based Least Recently Used (LRU) eviction and Time-To-Live (TTL) expiration. In multi-threaded production environments, naive combinations of LRU with TTL cause subtle race conditions: expired items polluting the LRU queue, `RuntimeError: dictionary changed size during iteration`, and wall-clock skew breaking expiration guarantees.

Implement a thread-safe `ConcurrentLRUTTLCache`:

```python
class ConcurrentLRUTTLCache:
    def __init__(self, capacity: int, default_ttl: Optional[float] = None): ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None: ...
    def delete(self, key: str) -> bool: ...
    def prune_expired(self) -> int: ...
    def __len__(self) -> int: ...
```

### Critical Invariants:
1. **Monotonic Clock Invariant:**
   Expiration calculations MUST use `time.monotonic()` instead of `time.time()`, rendering the cache resilient against system wall-clock adjustments (e.g., NTP adjustments or daylight saving shifts).

2. **Atomic Expired Key Lookup Invariant:**
   When `get(key)` is called for an expired key:
   - It must return `default`.
   - It MUST immediately evict the expired key from the cache.
   - It MUST NOT promote the expired key to the Most Recently Used (MRU) position.

3. **Smart Capacity Eviction Invariant:**
   When `put()` is called and the cache is at full capacity:
   - If ANY item in the cache is currently expired, the expired item must be pruned to make room.
   - Only if ALL cached items are still unexpired should the Least Recently Used (LRU) item be evicted.

4. **Thread Safety & Zero Mutation Errors:**
   All operations (`get`, `put`, `delete`, `prune_expired`, `__len__`) must be thread-safe. Concurrent access by 20+ threads must never raise `RuntimeError: dictionary changed size during iteration` or return expired items.
