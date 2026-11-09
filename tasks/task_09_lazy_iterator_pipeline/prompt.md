# Task 09: Lazy Iterator Pipeline with Strict Protocol Invariants

## Problem Description
Data processing pipelines over large or infinite streams must be fully lazy — processing elements one at a time without materializing the entire sequence into memory. Frontier models often produce implementations that appear lazy but secretly call `list()`, `sorted()`, or `[... for ...]` on intermediate stages, consuming O(N) memory instead of O(1).

Implement a composable lazy iterator pipeline class `LazyPipeline`:

```python
class LazyPipeline:
    def __init__(self, iterable): ...
    def map(self, fn) -> "LazyPipeline": ...
    def filter(self, predicate) -> "LazyPipeline": ...
    def take(self, n: int) -> "LazyPipeline": ...
    def skip(self, n: int) -> "LazyPipeline": ...
    def flat_map(self, fn) -> "LazyPipeline": ...
    def __iter__(self): ...
    def to_list(self) -> list: ...
```

### Critical Invariants:
1. **Strict Laziness — O(1) Peak Memory:**
   No pipeline stage may materialize a full intermediate collection. Every transformation must produce elements one-at-a-time via Python's iterator protocol.

2. **Infinite Stream Support:**
   `LazyPipeline` must support infinite input iterables (e.g., `itertools.count()`). Methods like `take(n)` must terminate on infinite sources.

3. **Exactly-Once Evaluation:**
   Each source element must be consumed exactly once — no double-iteration over the source.

4. **PEP-479 Compliance:**
   If any user-supplied `fn` or `predicate` raises `StopIteration` internally (accidentally or intentionally), the pipeline must NOT silently terminate the outer iteration. It must propagate the exception as `RuntimeError` (this is Python 3.7+ PEP-479 behavior inside generators).
