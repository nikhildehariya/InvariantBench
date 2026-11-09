"""Test suite for Task 06: Deadlock-Free Resource Manager."""

import time
import threading
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    ManagerClass = getattr(candidate_module, "ResourceManager", None)

    if ManagerClass is None:
        results.append(
            TestCaseResult(
                name="class_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="ResourceManager class not found in candidate module",
            )
        )
        return results

    # Test 1: Basic Locking and Release
    def _test_basic():
        mgr = ManagerClass(["res_1", "res_2"])
        assert not mgr.is_locked("res_1")
        assert not mgr.is_locked("res_2")

        with mgr.lock_resources("res_1"):
            assert mgr.is_locked("res_1")
            assert not mgr.is_locked("res_2")

        assert not mgr.is_locked("res_1")

    t0 = time.perf_counter()
    try:
        _test_basic()
        results.append(TestCaseResult("test_basic_locking_and_release", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_basic_locking_and_release", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Self-Deadlock on Duplicate Resource Keys
    def _test_duplicate():
        mgr = ManagerClass(["account_A"])
        completed = False

        def worker():
            nonlocal completed
            with mgr.lock_resources("account_A", "account_A"):
                completed = True

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(timeout=1.5)

        assert completed, "Self-Deadlock Detected! Model failed to deduplicate resource keys."

    t0 = time.perf_counter()
    try:
        _test_duplicate()
        results.append(TestCaseResult("test_duplicate_resource_self_deadlock", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_duplicate_resource_self_deadlock", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: High Concurrency Deadlock Elimination (Total Ordering Invariant)
    # Run independent trials for statistical robustness  -  a correct implementation
    # must pass; a buggy one will deadlock.
    # Per-trial deadline is platform-independent (3.5 seconds covers slow cloud containers).
    def _test_concurrency_deadlock():
        TRIALS = 2
        WORKERS_PER_DIRECTION = 4
        ITERATIONS = 20
        TRIAL_TIMEOUT_SEC = 3.5  # Generous headroom for single-core / throttled CI containers

        for trial in range(TRIALS):
            mgr = ManagerClass(["res_X", "res_Y"])
            count_lock = threading.Lock()
            finished_count = 0

            def worker_xy():
                nonlocal finished_count
                for _ in range(ITERATIONS):
                    with mgr.lock_resources("res_X", "res_Y"):
                        pass  # No sleep: deterministic contention pressure, no timing sensitivity
                with count_lock:
                    finished_count += 1

            def worker_yx():
                nonlocal finished_count
                for _ in range(ITERATIONS):
                    with mgr.lock_resources("res_Y", "res_X"):
                        pass
                with count_lock:
                    finished_count += 1

            threads = [
                threading.Thread(target=worker_xy, daemon=True)
                for _ in range(WORKERS_PER_DIRECTION)
            ] + [
                threading.Thread(target=worker_yx, daemon=True)
                for _ in range(WORKERS_PER_DIRECTION)
            ]

            for t in threads:
                t.start()

            total_threads = len(threads)
            deadline = time.time() + TRIAL_TIMEOUT_SEC
            for t in threads:
                remaining = max(0.05, deadline - time.time())
                t.join(timeout=remaining)
                if t.is_alive():
                    raise TimeoutError(
                        f"[Trial {trial + 1}/{TRIALS}] Circular-Wait Deadlock Detected! "
                        f"Threads froze when alternating ('res_X','res_Y') vs ('res_Y','res_X'). "
                        f"The implementation must acquire locks in global sorted order to eliminate circular wait."
                    )

            assert finished_count == total_threads, (
                f"[Trial {trial + 1}/{TRIALS}] Only {finished_count}/{total_threads} threads completed"
            )

    t0 = time.perf_counter()
    try:
        _test_concurrency_deadlock()
        results.append(TestCaseResult("test_concurrency_deadlock_elimination", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_concurrency_deadlock_elimination", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Exception LIFO Release
    def _test_exception_release():
        mgr = ManagerClass(["res_A", "res_B", "res_C"])
        try:
            with mgr.lock_resources("res_A", "res_B", "res_C"):
                raise ValueError("Crash inside critical section")
        except ValueError:
            pass

        assert not mgr.is_locked("res_A"), "res_A remained locked after exception"
        assert not mgr.is_locked("res_B"), "res_B remained locked after exception"
        assert not mgr.is_locked("res_C"), "res_C remained locked after exception"

    t0 = time.perf_counter()
    try:
        _test_exception_release()
        results.append(TestCaseResult("test_exception_lifo_release", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_exception_lifo_release", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
