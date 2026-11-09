# Task 05: ACID Transaction Manager with Generator-Exit & Savepoint Invariance

## Problem Description
In high-reliability database and state-store systems, transaction context managers must guarantee atomicity even when Python's execution flow is prematurely interrupted (e.g., via early loop `break`, generator termination, or unexpected signals).

Implement an in-memory key-value transactional store with the following interface:

```python
class TransactionStore:
    def __init__(self): ...
    def get(self, key: str) -> Optional[Any]: ...
    def transaction(self) -> ContextManager[Transaction]: ...
```

### Requirements:
1. **`Transaction` Interface**:
   - `set(key: str, value: Any) -> None`
   - `delete(key: str) -> None`
   - `get(key: str) -> Optional[Any]` (reads through transaction overlay, then parent state)

2. **Transactional Lifecycle**:
   - Changes made within `with store.transaction() as tx:` must only become visible on `store.get()` AFTER the transaction cleanly exits (Atomicity / Isolation).
   - If an exception occurs inside the `with` block, all changes must be completely discarded (Rollback).

3. **Critical Invariants**:
   - **GeneratorExit Invariant:** When a transaction is used inside an abandoned generator or an early loop exit occurs (triggering Python's `GeneratorExit`, which inherits from `BaseException` rather than `Exception`), the transaction MUST execute rollback and release any acquired locks.
   - **Nested Savepoint Isolation:** Supports nested transactions (`with store.transaction() as tx1: with store.transaction() as tx2:`). If the nested inner transaction fails and rolls back, the outer transaction should still be able to continue or commit its own independent changes.
   - **Lock & Active State Invariant:** No dangling locks or half-committed mutations may remain in the store after any abnormal exit.
