"""Test suite for Task 09: Lazy Iterator Pipeline."""

import time
import itertools
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    LazyPipeline = getattr(candidate_module, "LazyPipeline", None)

    if LazyPipeline is None:
        results.append(
            TestCaseResult(
                name="class_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="LazyPipeline class not found in candidate module",
            )
        )
        return results

    # Test 1: Functional Correctness of Chained Operations
    def _test_correctness():
        result = (
            LazyPipeline(range(20))
            .filter(lambda x: x % 2 == 0)
            .map(lambda x: x * x)
            .skip(2)
            .take(4)
            .to_list()
        )
        expected = [16, 36, 64, 100]  # evens: 0,2,4,6,8,10... -> squares: 0,4,16,36,64,100 -> skip 2 -> [16,36,64,100]
        assert result == expected, f"Incorrect result: {result}, expected {expected}"

    t0 = time.perf_counter()
    try:
        _test_correctness()
        results.append(TestCaseResult("test_chained_correctness", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_chained_correctness", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Infinite Stream Support (Laziness Invariant)
    def _test_infinite_stream():
        # A generator that behaves like an infinite stream, but halts eagerly if a model tries list()
        def quasi_infinite():
            i = 1
            while True:
                if i > 200:
                    raise RuntimeError(
                        "Eager Materialization Trap! Pipeline attempted to consume the entire "
                        "infinite stream. Expected lazy evaluation with O(1) buffer."
                    )
                yield i
                i += 1

        result = (
            LazyPipeline(quasi_infinite())
            .filter(lambda x: x % 3 == 0)
            .map(lambda x: x * 2)
            .take(5)
            .to_list()
        )
        assert result == [6, 12, 18, 24, 30], (
            f"Infinite stream error. Expected [6, 12, 18, 24, 30], got {result}."
        )

    t0 = time.perf_counter()
    try:
        _test_infinite_stream()
        results.append(TestCaseResult("test_infinite_stream_laziness", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_infinite_stream_laziness", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: flat_map Correctness
    def _test_flat_map():
        result = (
            LazyPipeline(["hello", "world"])
            .flat_map(lambda s: list(s))
            .filter(lambda c: c in "aeiou")
            .to_list()
        )
        expected = ["e", "o", "o"]
        assert result == expected, f"flat_map error: {result}, expected {expected}"

    t0 = time.perf_counter()
    try:
        _test_flat_map()
        results.append(TestCaseResult("test_flat_map_correctness", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_flat_map_correctness", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Memory Efficiency  -  O(1) Peak via Generator Instrumentation
    def _test_memory_efficiency():
        max_seen = 0
        call_count = [0]

        def counting_source():
            nonlocal max_seen
            for i in range(10_000):
                call_count[0] += 1
                yield i

        # Take only first 5  -  a truly lazy implementation should only call next()
        # on the source 5 times, not 10,000 times.
        result = (
            LazyPipeline(counting_source())
            .take(5)
            .to_list()
        )

        assert result == [0, 1, 2, 3, 4], f"take(5) produced wrong result: {result}"
        assert call_count[0] == 5, (
            f"O(1) Laziness Invariant Violated! Source generator was advanced {call_count[0]} times, "
            f"but only 5 elements were needed. "
            f"Model eagerly consumed the entire source (expected exactly 5 calls)."
        )

    t0 = time.perf_counter()
    try:
        _test_memory_efficiency()
        results.append(TestCaseResult("test_o1_memory_laziness", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_o1_memory_laziness", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 5: Exactly-Once Iteration  -  Source Not Double-Consumed
    def _test_exactly_once():
        consumed_count = [0]

        def single_pass_source():
            for i in range(5):
                consumed_count[0] += 1
                yield i

        pipeline = LazyPipeline(single_pass_source())
        list1 = pipeline.to_list()
        list2 = list(pipeline)  # Second iteration must yield nothing (already consumed)

        assert list1 == [0, 1, 2, 3, 4], f"First pass incorrect: {list1}"
        assert list2 == [], f"Exactly-Once Invariant Violated: second pass yielded {list2}. Source was not single-pass."
        assert consumed_count[0] == 5, f"Source called {consumed_count[0]} times, expected 5"

    t0 = time.perf_counter()
    try:
        _test_exactly_once()
        results.append(TestCaseResult("test_exactly_once_evaluation", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_exactly_once_evaluation", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
