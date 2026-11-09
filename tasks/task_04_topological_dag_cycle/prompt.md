# Task 04: Deterministic Topological DAG Resolution & Cycle Path Extraction

## Problem Description
Package managers and build systems require topological dependency resolution that is strictly reproducible, handles deep dependency chains without crashing Python's recursion stack, and isolates minimal cycle paths when dependency loops occur.

Implement a dependency resolver class `DependencyGraph`:

```python
class CycleDetectedError(Exception):
    def __init__(self, cycle_path: List[str]):
        super().__init__(f"Cycle detected: {' -> '.join(cycle_path)}")
        self.cycle_path = cycle_path
```

### Requirements:
1. **`add_dependency(package: str, depends_on: str) -> None`**:
   Declares that `package` depends on `depends_on` (i.e. `depends_on` must be built/installed before `package`).
   Packages may also be added without dependencies via `add_package(package: str)`.

2. **`resolve() -> List[str]`**:
   Returns the build/installation order such that for every dependency relation, the prerequisite appears before the dependent package.

### Invariant Rules:
1. **Deterministic Order Invariant:**
   Whenever multiple packages are ready to be built simultaneously (in-degree 0), break ties deterministically by selecting packages in **lexicographical (alphabetical) ascending order**.

2. **Deep Recursion Safety:**
   The algorithm must be completely iterative ($O(V + E)$ time and space). It MUST NOT fail with `RecursionError` on linear chains of 10,000+ packages.

3. **Cycle Path Extraction Invariant:**
   If a circular dependency exists in the graph, `resolve()` MUST raise `CycleDetectedError(cycle_path)`.
   - `cycle_path` must be a valid minimal directed cycle starting and ending at the same node: e.g., `["A", "B", "C", "A"]` where each consecutive pair represents a directed dependency edge.
   - It must NOT include extraneous nodes that are not part of the cycle loop.

4. **Disconnected Graph Invariant:**
   Handles multiple isolated components without omitting or corrupting nodes.
