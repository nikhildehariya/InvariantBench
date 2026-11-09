"""Test suite for Task 03: Deterministic Financial Allocation."""

import time
import random
from typing import List, Tuple
from decimal import Decimal
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    allocate_funds = getattr(candidate_module, "allocate_funds", None)

    if allocate_funds is None:
        results.append(
            TestCaseResult(
                name="function_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="allocate_funds function not defined in candidate module",
            )
        )
        return results

    # Test 1: Conservation of Money Invariant (sum == total) across 200 stress scenarios
    def _test_conservation():
        rng = random.Random(42)
        for _ in range(200):
            num_accounts = rng.randint(2, 25)
            total = Decimal(str(rng.randint(100, 1000000))) / Decimal("100")
            shares = [
                (f"user_{i}", Decimal(str(rng.randint(1, 100))))
                for i in range(num_accounts)
            ]
            allocated = allocate_funds(total, shares, currency_precision=2)
            actual_sum = sum(amt for _, amt in allocated)
            assert actual_sum == total, (
                f"Conservation invariant violated! Allocated {actual_sum} != Total {total}"
            )

    t0 = time.perf_counter()
    try:
        _test_conservation()
        results.append(TestCaseResult("test_conservation_of_money_invariant", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_conservation_of_money_invariant", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Largest Remainder Method (Hare-Niemeyer Fairness)
    def _test_largest_remainder_fairness():
        # Total $100.00. Weights 11, 10, 10. Sum of weights = 31.
        # Account high: 11/31 * 10000 = 3548.387 cents -> base 3548, remainder 0.387
        # Account mid:  10/31 * 10000 = 3225.806 cents -> base 3225, remainder 0.806
        # Account low:  10/31 * 10000 = 3225.806 cents -> base 3225, remainder 0.806
        # If the model naively dumps leftover pennies on the last account or rounds half-up,
        # it fails the Hare-Niemeyer ranking.
        # Let's test with 4 accounts where the last account has a small remainder:
        # Weights: [30.8, 30.7, 30.6, 7.9], Total = $100.00, sum = 100.0
        # exacts: 30.80, 30.70, 30.60, 7.90
        # What if Total is $100.00 and weights are [10.6, 10.6, 10.1]?
        # Sum = 31.3.
        # acc_1 (10.6): 3386.58 cents -> base 3386, remainder 0.5815
        # acc_2 (10.6): 3386.58 cents -> base 3386, remainder 0.5815
        # acc_3 (10.1): 3226.83 cents -> base 3226, remainder 0.8370
        # Leftover is 2 cents.
        # acc_3 has the highest remainder (0.837) so it MUST receive 1 cent -> 3227 cents = $32.27
        # Between acc_1 and acc_2, tie-breaker gives 1 cent to acc_1 -> 3387 cents = $33.87
        # acc_2 gets base 3386 cents = $33.86
        # Total: 32.27 + 33.87 + 33.86 = 100.00
        shares = [
            ("acc_1", Decimal("10.6")),
            ("acc_2", Decimal("10.6")),
            ("acc_3", Decimal("10.1")),
        ]
        total = Decimal("100.00")
        allocated = dict(allocate_funds(total, shares, currency_precision=2))

        assert allocated["acc_3"] == Decimal("32.27"), f"Expected 32.27 for acc_3, got {allocated['acc_3']}"
        assert allocated["acc_1"] == Decimal("33.87"), f"Expected 33.87 for acc_1, got {allocated['acc_1']}"
        assert allocated["acc_2"] == Decimal("33.86"), f"Expected 33.86 for acc_2, got {allocated['acc_2']}"

    t0 = time.perf_counter()
    try:
        _test_largest_remainder_fairness()
        results.append(TestCaseResult("test_largest_remainder_fairness", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_largest_remainder_fairness", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Deterministic Alphabetical Tie-Breaking on Identical Remainders
    def _test_tie_breaking():
        # Split $100.00 across 3 accounts with equal weights 1:1:1.
        # Base: 33.33 each = 99.99. Leftover: 1 cent.
        # Remainders are identical (0.333...).
        # Order in list: ["acc_Z", "acc_A", "acc_M"]
        # Tie-breaker rule: Sort by account_id ascending -> "acc_A" wins the extra penny.
        shares = [
            ("acc_Z", Decimal("1")),
            ("acc_A", Decimal("1")),
            ("acc_M", Decimal("1")),
        ]
        total = Decimal("100.00")
        allocated = dict(allocate_funds(total, shares, currency_precision=2))

        assert allocated["acc_A"] == Decimal("33.34"), (
            f"Tie-breaking invariant violated: acc_A should receive 33.34, got {allocated['acc_A']}"
        )
        assert allocated["acc_Z"] == Decimal("33.33")
        assert allocated["acc_M"] == Decimal("33.33")

    t0 = time.perf_counter()
    try:
        _test_tie_breaking()
        results.append(TestCaseResult("test_deterministic_tie_breaking", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_deterministic_tie_breaking", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Extreme Small Total & Zero Weights
    def _test_zero_weights():
        # $0.01 split across 3 accounts, one of which has 0 weight
        shares = [
            ("alpha", Decimal("10")),
            ("beta", Decimal("0")),
            ("gamma", Decimal("10")),
        ]
        total = Decimal("0.01")
        allocated = dict(allocate_funds(total, shares, currency_precision=2))

        assert allocated["beta"] == Decimal("0.00"), "Zero-weight account received funds"
        assert allocated["alpha"] == Decimal("0.01"), "Alphabetical tie-break failed on penny split"
        assert allocated["gamma"] == Decimal("0.00")

    t0 = time.perf_counter()
    try:
        _test_zero_weights()
        results.append(TestCaseResult("test_zero_weights_and_tiny_totals", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_zero_weights_and_tiny_totals", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
