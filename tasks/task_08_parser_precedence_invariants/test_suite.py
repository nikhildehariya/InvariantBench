"""Test suite for Task 08: Recursive Descent Expression Parser."""

import time
import random
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    evaluate = getattr(candidate_module, "evaluate", None)

    if evaluate is None:
        results.append(
            TestCaseResult(
                name="function_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="evaluate() function not found in candidate module",
            )
        )
        return results

    # Test 1: Basic Precedence (* before +)
    def _test_basic_precedence():
        cases = [
            ("2 + 3 * 4", 14.0),
            ("10 - 2 * 3", 4.0),
            ("1 + 2 + 3 * 4", 15.0),
            ("6 / 2 + 1", 4.0),
        ]
        for expr, expected in cases:
            result = evaluate(expr)
            assert abs(result - expected) < 1e-9, (
                f"Precedence error: evaluate('{expr}') = {result}, expected {expected}"
            )

    t0 = time.perf_counter()
    try:
        _test_basic_precedence()
        results.append(TestCaseResult("test_basic_precedence", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_basic_precedence", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Right-Associativity of ** (Critical Invariant)
    def _test_right_assoc_exponent():
        # 2 ** 3 ** 2 = 2 ** (3 ** 2) = 2 ** 9 = 512 (RIGHT-assoc)
        # NOT (2**3)**2 = 8**2 = 64  (LEFT-assoc is WRONG)
        result = evaluate("2 ** 3 ** 2")
        assert abs(result - 512.0) < 1e-9, (
            f"Right-Associativity Trap! evaluate('2 ** 3 ** 2') = {result}, "
            f"expected 512.0 (= 2**(3**2)). "
            f"Model produced 64.0, indicating left-associative ** (= (2**3)**2)."
        )

        # 4 ** 3 ** 2 = 4 ** 9 = 262144, NOT (4**3)**2 = 4096
        result2 = evaluate("4 ** 3 ** 2")
        assert abs(result2 - 262144.0) < 1e-9, (
            f"Right-Associativity failed: evaluate('4 ** 3 ** 2') = {result2}, expected 262144.0"
        )

    t0 = time.perf_counter()
    try:
        _test_right_assoc_exponent()
        results.append(TestCaseResult("test_right_assoc_exponent", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_right_assoc_exponent", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Parentheses Override Precedence
    def _test_parentheses():
        cases = [
            ("(2 + 3) * 4", 20.0),
            ("2 * (3 + 4)", 14.0),
            ("(2 + 3) ** 2", 25.0),
            ("((1 + 2) * (3 + 4))", 21.0),
        ]
        for expr, expected in cases:
            result = evaluate(expr)
            assert abs(result - expected) < 1e-9, (
                f"Parentheses error: evaluate('{expr}') = {result}, expected {expected}"
            )

    t0 = time.perf_counter()
    try:
        _test_parentheses()
        results.append(TestCaseResult("test_parentheses_override", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_parentheses_override", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Property-Based Validation Against Python's Own Evaluator
    # Generates random expressions using +, -, *, ** and integer literals
    def _test_property_based():
        rng = random.Random(0xDEADBEEF)

        def gen_expr(depth=0):
            if depth >= 2:
                return str(rng.randint(1, 5))
            ops = ["+", "-", "*"] + (["**"] if depth == 0 else [])
            op = rng.choice(ops)
            left = gen_expr(depth + 1)
            right = str(rng.randint(1, 3)) if op == "**" else gen_expr(depth + 1)
            return f"({left} {op} {right})"

        for _ in range(100):
            expr = gen_expr()
            try:
                expected = float(eval(expr))  # noqa: S307
            except OverflowError:
                continue
            got = evaluate(expr)
            assert abs(got - expected) < 1e-6 or abs(got - expected) / (abs(expected) + 1e-9) < 1e-6, (
                f"Property check failed: evaluate('{expr}') = {got}, Python eval = {expected}"
            )

    t0 = time.perf_counter()
    try:
        _test_property_based()
        results.append(TestCaseResult("test_property_based_vs_python_eval", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_property_based_vs_python_eval", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 5: Unary Minus Interplay with Exponentiation
    def _test_unary_minus():
        # In Python: -2**2 = -(2**2) = -4, NOT (-2)**2 = 4
        result = evaluate("-2 ** 2")
        assert abs(result - (-4.0)) < 1e-9, (
            f"Unary minus precedence error: evaluate('-2 ** 2') = {result}, "
            f"expected -4.0 (= -(2**2)), not 4.0 (= (-2)**2)"
        )

    t0 = time.perf_counter()
    try:
        _test_unary_minus()
        results.append(TestCaseResult("test_unary_minus_with_exponent", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_unary_minus_with_exponent", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
