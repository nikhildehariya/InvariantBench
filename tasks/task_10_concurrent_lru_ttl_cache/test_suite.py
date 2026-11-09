"""Test suite for Task 10: Concurrent LRU-TTL Cache."""

import time
import threading
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    CacheClass = getattr(candidate_module, "ConcurrentLRUTTLCache", None)

    if CacheClass is None:
        results.append(
            TestCaseResult(
                name="class_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="ConcurrentLRUTTLCache class not found in candidate module",
            )
        )
        return results

    # Test 1: Basic LRU Eviction Invariant
    def _test_lru_basic():
        cache = CacheClass(capacity=3)
        cache.put("A", 1)
        cache.put("B", 2)
        cache.put("C", 3)

        # Access A so order of usage is: B (LRU), C, A (MRU)
        assert cache.get("A") == 1

        # Put D: capacity reached, B must be evicted
        cache.put("D", 4)
        assert cache.get("B") is None, "LRU Invariant Violated: B should have been evicted"
        assert cache.get("A") == 1
        assert cache.get("C") == 3
        assert cache.get("D") == 4

    t0 = time.perf_counter()
    try:
        _test_lru_basic()
        results.append(TestCaseResult("test_lru_eviction_order", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_lru_eviction_order", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: TTL Expiration and Length Invariant
    def _test_ttl_expiration():
        cache = CacheClass(capacity=5)
        cache.put("short", "data", ttl=0.03)
        cache.put("long", "persist", ttl=1.0)

        assert cache.get("short") == "data"
        time.sleep(0.04)

        # short must now be expired
        assert cache.get("short") is None, "TTL Invariant Violated: short key was accessed after expiration"
        assert cache.get("long") == "persist"
        assert len(cache) == 1, f"len(cache) was {len(cache)}, expected 1 (expired key should not count)"

    t0 = time.perf_counter()
    try:
        _test_ttl_expiration()
        results.append(TestCaseResult("test_ttl_expiration_accuracy", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_ttl_expiration_accuracy", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Smart Capacity Eviction: Evict Expired Items BEFORE Valid LRU Items
    def _test_smart_eviction():
        # Capacity 2
        cache = CacheClass(capacity=2)
        # Put k1 (valid, no ttl)
        cache.put("k1", "valid_data", ttl=None)
        # Put k2 (short ttl, expires soon)
        cache.put("k2", "temp_data", ttl=0.03)

        # k1 is LRU, k2 is MRU.
        time.sleep(0.04)
        # Now k2 is expired.

        # Insert k3: capacity is 2.
        # Smart eviction invariant: k2 is expired, so k2 MUST be evicted to make room for k3.
        # k1 is valid and MUST NOT be evicted!
        cache.put("k3", "new_data", ttl=None)

        assert cache.get("k1") == "valid_data", (
            "Smart Eviction Trap! Cache evicted valid LRU key 'k1' instead of pruning "
            "expired key 'k2' when capacity was full."
        )
        assert cache.get("k3") == "new_data"
        assert cache.get("k2") is None

    t0 = time.perf_counter()
    try:
        _test_smart_eviction()
        results.append(TestCaseResult("test_smart_capacity_eviction", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_smart_capacity_eviction", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Prune Expired Clean Sweep
    def _test_prune():
        cache = CacheClass(capacity=10)
        cache.put("e1", 1, ttl=0.02)
        cache.put("e2", 2, ttl=0.02)
        cache.put("v1", 3, ttl=1.0)
        time.sleep(0.03)

        pruned = cache.prune_expired()
        assert pruned == 2, f"Expected 2 pruned keys, got {pruned}"
        assert len(cache) == 1
        assert cache.get("v1") == 3

    t0 = time.perf_counter()
    try:
        _test_prune()
        results.append(TestCaseResult("test_prune_expired_sweep", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_prune_expired_sweep", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 5: Concurrent Multi-Threaded Stress Test
    def _test_concurrent_stress():
        cache = CacheClass(capacity=10, default_ttl=0.05)
        errors = []

        def worker(worker_id: int):
            try:
                for i in range(30):
                    key = f"key_{worker_id}_{i % 5}"
                    cache.put(key, f"val_{i}")
                    val = cache.get(key)
                    if i % 10 == 0:
                        cache.prune_expired()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=3.5)

        assert len(errors) == 0, f"Concurrent execution errors: {errors}"

    t0 = time.perf_counter()
    try:
        _test_concurrent_stress()
        results.append(TestCaseResult("test_concurrent_thread_safety", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_concurrent_thread_safety", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
