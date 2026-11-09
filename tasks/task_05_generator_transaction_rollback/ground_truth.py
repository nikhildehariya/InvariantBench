"""Ground Truth Reference Implementation for Task 05: Transaction Store."""

from contextlib import contextmanager
from typing import Dict, Any, Optional, Set


_DELETED = object()


class Transaction:
    def __init__(self, parent_reader):
        self._parent_reader = parent_reader
        self._overlay: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._overlay[key] = value

    def delete(self, key: str) -> None:
        self._overlay[key] = _DELETED

    def get(self, key: str) -> Optional[Any]:
        if key in self._overlay:
            val = self._overlay[key]
            return None if val is _DELETED else val
        return self._parent_reader(key)

    def _apply_to(self, target_dict: Dict[str, Any]) -> None:
        for k, v in self._overlay.items():
            if v is _DELETED:
                target_dict.pop(k, None)
            else:
                target_dict[k] = v


class TransactionStore:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._active_stack = []

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key, None)

    @property
    def is_in_transaction(self) -> bool:
        return len(self._active_stack) > 0

    @contextmanager
    def transaction(self):
        # Determine parent reader
        if self._active_stack:
            parent_reader = self._active_stack[-1].get
        else:
            parent_reader = lambda k: self._data.get(k, None)

        tx = Transaction(parent_reader)
        self._active_stack.append(tx)

        committed = False
        try:
            yield tx
            # If we reach here without exception, commit
            committed = True
        except BaseException:
            # Crucial: catches BaseException including GeneratorExit and KeyboardInterrupt
            committed = False
            raise
        finally:
            # Guarantee rollback / cleanup even on GeneratorExit
            if self._active_stack and self._active_stack[-1] is tx:
                self._active_stack.pop()

            if committed:
                if self._active_stack:
                    # Apply changes to parent transaction
                    for k, v in tx._overlay.items():
                        tx._active_stack[-1]._overlay[k] = v if hasattr(tx, '_active_stack') else v
                    # More direct: apply to parent in stack
                    parent_tx = self._active_stack[-1]
                    for k, v in tx._overlay.items():
                        parent_tx._overlay[k] = v
                else:
                    # Apply changes to root store
                    tx._apply_to(self._data)
            else:
                # Discard transaction changes (rollback)
                tx._overlay.clear()
