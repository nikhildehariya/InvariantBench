"""Test suite for Task 01: Async Shielded Worker Pool."""

import asyncio
import time
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    WorkerPool = getattr(candidate_module, "ShieldedWorkerPool", None)

    if WorkerPool is None:
        results.append(
            TestCaseResult(
                name="class_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="ShieldedWorkerPool class not defined in candidate module",
            )
        )
        return results

    # Test 1: Standard Execution & Concurrency Limit
    async def _test_concurrency():
        pool = WorkerPool(max_concurrency=2)
        concurrent_peak = 0
        current_running = 0
        lock = asyncio.Lock()

        async def worker_job(val: int):
            nonlocal concurrent_peak, current_running
            async with lock:
                current_running += 1
                if current_running > concurrent_peak:
                    concurrent_peak = current_running
            await asyncio.sleep(0.05)
            async with lock:
                current_running -= 1
            return val * 2

        futs = [pool.submit(worker_job, i) for i in range(6)]
        res = await asyncio.gather(*futs)
        await pool.shutdown(wait=True)

        assert res == [0, 2, 4, 6, 8, 10], f"Unexpected results: {res}"
        assert concurrent_peak <= 2, f"Concurrency limit exceeded: {concurrent_peak} > 2"

    t0 = time.perf_counter()
    try:
        asyncio.run(_test_concurrency())
        results.append(TestCaseResult("test_standard_concurrency", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_standard_concurrency", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Shielded Cancellation Orphan Prevention
    async def _test_shielded_orphan():
        pool = WorkerPool(max_concurrency=3)
        job_completed = False

        async def critical_job():
            nonlocal job_completed
            await asyncio.sleep(0.1)
            job_completed = True
            return "done"

        async def caller():
            return await pool.submit(critical_job, shield_execution=True)

        caller_task = asyncio.create_task(caller())
        await asyncio.sleep(0.02)
        # Cancel the outer caller
        caller_task.cancel()

        # Caller task should raise CancelledError
        try:
            await caller_task
            assert False, "Caller task should have raised CancelledError"
        except asyncio.CancelledError:
            pass

        # Invariant check: Pool must STILL track the task in active_count!
        # It must NOT be orphaned or forgotten.
        assert pool.active_count >= 1, (
            f"Invariant violation: Active count is {pool.active_count}; "
            "pool orphaned shielded background task after caller cancellation."
        )

        # Wait for the critical job to finish
        await pool.shutdown(wait=True, timeout=1.0)
        assert job_completed is True, "Shielded job failed to complete critical section"
        assert pool.active_count == 0, "Pool active_count did not drain to zero"

    t0 = time.perf_counter()
    try:
        asyncio.run(_test_shielded_orphan())
        results.append(TestCaseResult("test_shielded_cancellation_orphan_prevention", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_shielded_cancellation_orphan_prevention", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Shutdown Cleanly Awaits Teardown (Zero Lingering Pending Tasks)
    async def _test_shutdown_draining():
        pool = WorkerPool(max_concurrency=5)

        async def long_hanging_task():
            await asyncio.sleep(10.0)

        t = asyncio.create_task(pool.submit(long_hanging_task, shield_execution=False))
        await asyncio.sleep(0.02)

        # Force immediate shutdown without waiting for full 10s
        await pool.shutdown(wait=False)

        # All internal tasks must have finished cancellation, none should still be running
        loop = asyncio.get_running_loop()
        # Find any tasks created by this test that are still pending
        lingering = [
            task for task in asyncio.all_tasks(loop)
            if task is not asyncio.current_task() and not task.done()
        ]
        # Allow at most 0 lingering tasks
        assert len(lingering) == 0, (
            f"Invariant violation: {len(lingering)} un-awaited pending tasks remained "
            "in event loop after pool.shutdown(wait=False)"
        )
        try:
            await t
        except (asyncio.CancelledError, RuntimeError):
            pass

    t0 = time.perf_counter()
    try:
        asyncio.run(_test_shutdown_draining())
        results.append(TestCaseResult("test_shutdown_clean_draining", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_shutdown_clean_draining", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Rejection After Shutdown
    async def _test_rejection():
        pool = WorkerPool(max_concurrency=2)
        await pool.shutdown(wait=True)
        try:
            await pool.submit(asyncio.sleep, 0.01)
            assert False, "Pool accepted submit() after shutdown"
        except RuntimeError:
            pass

    t0 = time.perf_counter()
    try:
        asyncio.run(_test_rejection())
        results.append(TestCaseResult("test_shutdown_rejection", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_shutdown_rejection", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 5: Exception Propagation  -  Non-Shielded Submit Propagates Exceptions
    async def _test_exception_propagation():
        pool = WorkerPool(max_concurrency=3)

        async def failing_job():
            await asyncio.sleep(0.01)
            raise ValueError("Job failed internally")

        try:
            await pool.submit(failing_job)
            assert False, "Exception from worker job was silently swallowed"
        except ValueError as e:
            assert "Job failed internally" in str(e)
        finally:
            await pool.shutdown(wait=True)

        assert pool.active_count == 0, "Active count not zero after exception job drained"

    t0 = time.perf_counter()
    try:
        asyncio.run(_test_exception_propagation())
        results.append(TestCaseResult("test_exception_propagation", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_exception_propagation", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 6: Repeated Shielded Submissions  -  Pool Stable Under Burst Load
    async def _test_burst_shielded():
        pool = WorkerPool(max_concurrency=4)
        completed = []

        async def quick_job(n: int):
            await asyncio.sleep(0.02)
            completed.append(n)
            return n

        # Submit 8 shielded jobs; immediately cancel all caller tasks
        caller_tasks = [asyncio.create_task(pool.submit(quick_job, i, shield_execution=True)) for i in range(8)]
        await asyncio.sleep(0.01)
        for ct in caller_tasks:
            ct.cancel()
        await asyncio.gather(*caller_tasks, return_exceptions=True)

        # Pool must still be tracking in-flight work
        assert pool.active_count > 0, "All shielded jobs were dropped  -  pool lost track of in-flight work"

        # Drain via shutdown and verify all 8 jobs completed
        await pool.shutdown(wait=True, timeout=2.0)
        assert len(completed) == 8, f"Expected 8 shielded completions, got {len(completed)}"
        assert pool.active_count == 0

    t0 = time.perf_counter()
    try:
        asyncio.run(_test_burst_shielded())
        results.append(TestCaseResult("test_burst_shielded_stability", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_burst_shielded_stability", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
