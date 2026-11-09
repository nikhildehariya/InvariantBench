"""Ground Truth Reference Implementation for Task 03: Deterministic Financial Allocation."""

from decimal import Decimal, ROUND_FLOOR
from typing import List, Tuple


def allocate_funds(
    total_amount: Decimal,
    shares: List[Tuple[str, Decimal]],
    currency_precision: int = 2
) -> List[Tuple[str, Decimal]]:
    if not shares:
        raise ValueError("Shares list cannot be empty")
    if total_amount < Decimal("0"):
        raise ValueError("Total amount cannot be negative")

    total_weight = sum(w for _, w in shares)
    if total_weight <= Decimal("0"):
        raise ValueError("Total weight must be positive")

    # Quantum unit, e.g. Decimal('0.01') for precision 2
    quantum = Decimal("10") ** -currency_precision
    total_units = int(total_amount / quantum)

    # Compute base allocation and fractional remainders in exact Decimal arithmetic
    # exact_units_i = (weight_i * total_units) / total_weight
    allocations = []
    remainders = []

    for idx, (acc_id, weight) in enumerate(shares):
        if weight < Decimal("0"):
            raise ValueError(f"Negative weight for account {acc_id}")
        exact_units = (weight * Decimal(total_units)) / total_weight
        base_units = int(exact_units.quantize(Decimal("1"), rounding=ROUND_FLOOR))
        remainder = exact_units - Decimal(base_units)

        allocations.append(base_units)
        remainders.append((remainder, acc_id, idx))

    # Calculate leftover units to distribute
    allocated_units = sum(allocations)
    leftover = total_units - allocated_units

    # Sort remainders: largest remainder first (-remainder).
    # Break ties by account_id in ascending order.
    # We sort by (-remainder, acc_id)
    remainders.sort(key=lambda item: (-item[0], item[1]))

    # Distribute leftover 1 unit at a time
    for i in range(leftover):
        target_idx = remainders[i][2]
        allocations[target_idx] += 1

    # Convert back to Decimal amounts
    result = []
    for (acc_id, _), units in zip(shares, allocations):
        amount = Decimal(units) * quantum
        result.append((acc_id, amount))

    # Verify conservation invariant
    assert sum(amt for _, amt in result) == total_amount, "Internal invariant failed: money conservation"
    return result
