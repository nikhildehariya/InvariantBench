# Task 03: Deterministic Financial Allocation with Zero Penny Drift

## Problem Description
In banking and financial ledger accounting, dividing monetary amounts across accounts proportional to weights is a classic source of critical audit failures. Naive division causes "penny drift" where the sum of rounded values deviates from the input total, violating the fundamental **Conservation of Money** invariant.

Implement a function `allocate_funds`:

```python
def allocate_funds(
    total_amount: Decimal,
    shares: List[Tuple[str, Decimal]],
    currency_precision: int = 2
) -> List[Tuple[str, Decimal]]:
```

### Parameters:
- `total_amount`: The total monetary amount to allocate (positive `Decimal`).
- `shares`: A list of `(account_id, weight)` tuples, where `account_id` is a unique string and `weight` is a non-negative `Decimal`.
- `currency_precision`: Number of decimal places (default 2 for standard fiat cents, i.e. smallest quantum is $10^{-2}$).

### Invariant Rules:
1. **Conservation of Money Invariant:**
   The sum of all returned allocations must be **identically equal** to `total_amount`:
   $$\sum_{i=1}^{N} \text{allocation}_i \equiv \text{total\_amount}$$
   Zero pennies, cents, or fractional units may be created or lost.

2. **Fair Largest Remainder Method (Hare-Niemeyer Algorithm):**
   - Each account initially receives their truncated base units: $\lfloor \frac{\text{weight}_i}{\sum \text{weight}} \times \text{total\_units} \rfloor$.
   - The remaining leftover units must be awarded one-by-one to accounts having the largest fractional remainders.
   - **No Last-Item Dumping Trap:** Leftover pennies must NOT simply be dumped onto the last index or first index. They must be awarded in order of highest fractional share.

3. **Deterministic Tie-Breaking:**
   If two accounts have the exact same fractional remainder, break ties deterministically by sorting alphabetically by `account_id` in ascending order.

4. **Preserved Ordering & Zero Weight Handling:**
   - The returned list must match the original ordering of accounts in `shares`.
   - Accounts with weight 0 receive 0 allocation.
   - If total weight is 0 or shares is empty, raise `ValueError`.
