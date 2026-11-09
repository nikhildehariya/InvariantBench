"""Test suite for Task 04: Deterministic Dependency Graph."""

import time
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    GraphClass = getattr(candidate_module, "DependencyGraph", None)
    CycleErr = getattr(candidate_module, "CycleDetectedError", None)

    if GraphClass is None or CycleErr is None:
        results.append(
            TestCaseResult(
                name="classes_exist",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="DependencyGraph or CycleDetectedError not found in candidate module",
            )
        )
        return results

    # Test 1: Basic Dependency Ordering Invariant
    def _test_basic():
        g = GraphClass()
        g.add_dependency("app", "db")
        g.add_dependency("db", "os")
        g.add_dependency("app", "auth")
        g.add_dependency("auth", "os")

        order = g.resolve()
        assert order.index("os") < order.index("db")
        assert order.index("os") < order.index("auth")
        assert order.index("db") < order.index("app")
        assert order.index("auth") < order.index("app")

    t0 = time.perf_counter()
    try:
        _test_basic()
        results.append(TestCaseResult("test_basic_dependency_order", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_basic_dependency_order", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Deterministic Alphabetical Tie-Breaking Invariant
    def _test_tie_breaking():
        # Independent nodes: "zebra", "apple", "mango" all ready at start
        # "finish" depends on all three
        g = GraphClass()
        g.add_dependency("finish", "zebra")
        g.add_dependency("finish", "apple")
        g.add_dependency("finish", "mango")

        order = g.resolve()
        # Must resolve in exact alphabetical order: apple, mango, zebra, finish
        expected = ["apple", "mango", "zebra", "finish"]
        assert order == expected, f"Tie-breaking non-deterministic! Got {order}, expected {expected}"

    t0 = time.perf_counter()
    try:
        _test_tie_breaking()
        results.append(TestCaseResult("test_deterministic_tie_breaking", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_deterministic_tie_breaking", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Minimal Cycle Path Extraction Invariant
    def _test_cycle_path():
        g = GraphClass()
        # Innocent branch
        g.add_dependency("clean_app", "clean_lib")
        # Directed cycle: C1 -> C2 -> C3 -> C1
        # C2 depends on C1, C3 depends on C2, C1 depends on C3
        g.add_dependency("C2", "C1")
        g.add_dependency("C3", "C2")
        g.add_dependency("C1", "C3")

        try:
            g.resolve()
            assert False, "Failed to raise CycleDetectedError on cyclic graph"
        except CycleErr as err:
            cycle = err.cycle_path
            assert isinstance(cycle, list), "cycle_path must be a list"
            assert len(cycle) >= 3, f"Cycle path too short: {cycle}"
            assert cycle[0] == cycle[-1], f"Cycle path must start and end at same node: {cycle}"
            # Check every consecutive pair is part of the cycle nodes
            cycle_nodes = {"C1", "C2", "C3"}
            for node in cycle:
                assert node in cycle_nodes, f"Extraneous non-cycle node in cycle_path: {node}"

    t0 = time.perf_counter()
    try:
        _test_cycle_path()
        results.append(TestCaseResult("test_minimal_cycle_path_extraction", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_minimal_cycle_path_extraction", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Deep Recursion Safety Invariant (3,000 Depth Chain)
    def _test_deep_chain():
        g = GraphClass()
        N = 3000
        for i in range(N - 1):
            # pkg_{i+1} depends on pkg_{i}
            g.add_dependency(f"pkg_{i+1}", f"pkg_{i}")

        order = g.resolve()
        assert len(order) == N, f"Expected {N} resolved packages, got {len(order)}"
        assert order[0] == "pkg_0"
        assert order[-1] == f"pkg_{N-1}"

    t0 = time.perf_counter()
    try:
        _test_deep_chain()
        results.append(TestCaseResult("test_deep_chain_recursion_safety", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_deep_chain_recursion_safety", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
