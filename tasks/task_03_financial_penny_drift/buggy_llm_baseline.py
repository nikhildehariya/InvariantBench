"""Buggy LLM Baseline Implementation for Task 03.

Representative of typical frontier LLM outputs:
1. Uses naive floating-point division or basic Decimal.quantize(ROUND_HALF_UP)
   without remainder tracking, causing cumulative Penny Drift (sum != total).
2. Or blindly dumps the leftover difference onto the last account in the list,
   violating fairness and deterministic largest-remainder distribution invariants.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple


def allocate_funds(
    total_amount: Decimal,
    shares: List[Tuple[str, Decimal]],
    currency_precision: int = 2
) -> List[Tuple[str, Decimal]]:
    if not shares:
        raise ValueError("Shares cannot be empty")

    total_weight = sum(w for _, w in shares)
    quantum = Decimal("10") ** -currency_precision

    # LLM TRAP 1: Rounds each allocation independently using ROUND_HALF_UP
    results = []
    current_sum = Decimal("0")
    for acc_id, weight in shares:
        exact = (total_amount * weight) / total_weight
        rounded = exact.quantize(quantum, rounding=ROUND_HALF_UP)
        results.append((acc_id, rounded))
        current_sum += rounded

    # LLM TRAP 2: Arbitrarily dumps remainder onto the last element!
    diff = total_amount - current_sum
    if diff != Decimal("0") and results:
        last_id, last_amt = results[-1]
        results[-1] = (last_id, last_amt + diff)

    return results
