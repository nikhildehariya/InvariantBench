"""Buggy LLM Baseline Implementation for Task 05.

Representative of typical frontier LLM outputs:
1. Catches only standard `Exception` rather than `BaseException`. When GeneratorExit
   is thrown (e.g. from early generator termination), rollback logic is completely
   bypassed and the active transaction is left hanging.
2. In-place mutation of the store with an incomplete undo log that corrupts state
   during nested transaction failures.
"""

from contextlib import contextmanager
from typing import Dict, Any, Optional


class Transaction:
    def __init__(self, store):
        self.store = store
        self.changes = {}

    def set(self, key: str, value: Any) -> None:
        self.changes[key] = value

    def delete(self, key: str) -> None:
        self.changes[key] = None

    def get(self, key: str) -> Optional[Any]:
        if key in self.changes:
            return self.changes[key]
        return self.store.get(key)


class TransactionStore:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._in_tx = False

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key, None)

    @property
    def is_in_transaction(self) -> bool:
        return self._in_tx

    @contextmanager
    def transaction(self):
        # LLM TRAP 1: Simple boolean flag doesn't support nested transactions
        self._in_tx = True
        tx = Transaction(self)
        try:
            yield tx
            # Commit changes to store
            for k, v in tx.changes.items():
                if v is None:
                    self._data.pop(k, None)
                else:
                    self._data[k] = v
            self._in_tx = False
        except Exception:
            # LLM TRAP 2: Only catches `Exception`!
            # GeneratorExit inherits directly from BaseException, so GeneratorExit
            # slips right through here, completely bypassing the rollback!
            tx.changes.clear()
            self._in_tx = False
            raise
