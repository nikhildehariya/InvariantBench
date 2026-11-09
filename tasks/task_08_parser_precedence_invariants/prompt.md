# Task 08: Recursive Descent Expression Parser with Strict Precedence Invariants

## Problem Description
Expression parsers are a canonical test of operator precedence and associativity handling. Frontier LLMs consistently produce parsers that evaluate `2 + 3 * 4` as 20 (wrong) instead of 14 (correct), or treat `2 ** 3 ** 2` as `(2**3)**2 = 512` instead of `2**(3**2) = 512`... wait — they get `2**9 = 512` vs `8**2 = 64`, which differ significantly.

Implement a function `evaluate(expression: str) -> float` that parses and evaluates arithmetic expressions containing:
- **Operators:** `+`, `-`, `*`, `/`, `**` (exponentiation), unary `-`
- **Atoms:** non-negative integer and float literals, parenthesized sub-expressions

### Invariant Rules (in strict priority order):
1. **Precedence Invariant:**
   `**` (highest) > unary `-` > `*`, `/` > `+`, `-` (lowest)
2. **Right-Associativity of `**`:**
   `2 ** 3 ** 2` must evaluate as `2 ** (3 ** 2)` = `2 ** 9` = **512**, NOT `(2**3)**2` = 64.
3. **Parenthesis Override:**
   Sub-expressions in parentheses must evaluate as an isolated unit overriding default precedence.
4. **No `eval()` Shortcut:**
   Implementation must be a genuine recursive descent or Pratt parser — using Python's built-in `eval()` or `ast.literal_eval()` directly as the entire implementation is disallowed.
