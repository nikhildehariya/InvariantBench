"""Test suite for Task 07: AST Function Instrumentation."""

import time
import asyncio
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    instrument_source = getattr(candidate_module, "instrument_source", None)

    if instrument_source is None:
        results.append(
            TestCaseResult(
                name="function_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="instrument_source function not found in candidate module",
            )
        )
        return results

    # Test 1: Docstring Preservation Invariant
    def _test_docstring():
        source = '''
def calculate_tax(income: float) -> float:
    """Calculates effective tax rate accurately."""
    return income * 0.25
'''
        instrumented = instrument_source(source)
        env = {}
        calls = []
        env["__trace__"] = lambda name: calls.append(name)
        exec(instrumented, env)

        fn = env["calculate_tax"]
        assert fn.__doc__ is not None, (
            "Docstring Destruction Trap! fn.__doc__ is None. "
            "Model inserted instrumentation before docstring statement."
        )
        assert fn.__doc__.strip() == "Calculates effective tax rate accurately."
        assert fn(100.0) == 25.0
        assert calls == ["calculate_tax"]

    t0 = time.perf_counter()
    try:
        _test_docstring()
        results.append(TestCaseResult("test_docstring_preservation_invariant", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_docstring_preservation_invariant", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Async Coroutine Function Instrumentation Support
    def _test_async_support():
        source = '''
async def fetch_user(user_id: int):
    """Fetch user asynchronously."""
    return f"user_{user_id}"
'''
        instrumented = instrument_source(source)
        env = {}
        calls = []
        env["__trace__"] = lambda name: calls.append(name)
        exec(instrumented, env)

        fn = env["fetch_user"]
        assert fn.__doc__.strip() == "Fetch user asynchronously."

        res = asyncio.run(fn(42))
        assert res == "user_42"
        assert calls == ["fetch_user"], f"Async function was not instrumented! Calls: {calls}"

    t0 = time.perf_counter()
    try:
        _test_async_support()
        results.append(TestCaseResult("test_async_function_support", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_async_function_support", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Multiple Functions & Execution Trace Fidelity
    def _test_trace_fidelity():
        source = '''
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
'''
        instrumented = instrument_source(source, tracer_func_name="audit_log")
        env = {}
        audit = []
        env["audit_log"] = lambda name: audit.append(name)
        exec(instrumented, env)

        assert env["add"](2, 3) == 5
        assert env["multiply"](4, 5) == 20
        assert audit == ["add", "multiply"]

    t0 = time.perf_counter()
    try:
        _test_trace_fidelity()
        results.append(TestCaseResult("test_trace_fidelity", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_trace_fidelity", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Nested Functions and Scope Hygiene
    def _test_nested_scope():
        source = '''
def outer_fn(x):
    """Outer docstring."""
    def inner_fn(y):
        """Inner docstring."""
        return y * 2
    return inner_fn(x) + 1
'''
        instrumented = instrument_source(source)
        env = {}
        calls = []
        env["__trace__"] = lambda name: calls.append(name)
        exec(instrumented, env)

        res = env["outer_fn"](10)
        assert res == 21
        assert "outer_fn" in calls and "inner_fn" in calls, f"Nested calls missing: {calls}"

    t0 = time.perf_counter()
    try:
        _test_nested_scope()
        results.append(TestCaseResult("test_nested_functions_scope", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_nested_functions_scope", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
