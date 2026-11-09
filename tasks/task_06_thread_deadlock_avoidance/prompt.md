# Task 06: Deadlock-Free Multi-Resource Lock Manager

## Problem Description
In multi-threaded banking systems, database row locks, or game servers, operations frequently require exclusive access to multiple named resources simultaneously (e.g., transferring funds between Account A and Account B). When threads request sets of locks in arbitrary orders, circular wait deadlocks inevitably freeze the system under high load.

Implement a thread-safe `ResourceManager` with the following interface:

```python
class ResourceManager:
    def __init__(self, resource_names: List[str]): ...
    def lock_resources(self, *resource_names: str) -> ContextManager[None]: ...
    def is_locked(self, resource_name: str) -> bool: ...
```

### Invariant Requirements:
1. **Deadlock-Free Total Ordering (Coffman Circular Wait Elimination):**
   - When multiple threads attempt to acquire different overlapping subsets of resources (e.g. Thread 1 requests `("res_A", "res_B")` while Thread 2 requests `("res_B", "res_A")`), the manager MUST guarantee that deadlocks CANNOT occur under any schedule.
   - Resource acquisition must follow a deterministic global total ordering.

2. **Deduplication & Self-Deadlock Prevention:**
   - Calling `lock_resources("res_A", "res_A")` must deduplicate keys and acquire `res_A` exactly once without deadlocking on itself.

3. **Guaranteed LIFO Release on Exception:**
   - If an exception is raised inside `with manager.lock_resources(...):`, all locks acquired for that block MUST be completely released in reverse (LIFO) order.
   - No resource locks may remain orphaned.

4. **Invalid Resource Validation:**
   - Requesting an unmanaged resource name raises `KeyError`.
