"""Ground Truth Reference Implementation for Task 06: Deadlock-Free Resource Manager."""

import threading
from contextlib import contextmanager
from typing import List, Dict


class ResourceManager:
    def __init__(self, resource_names: List[str]):
        self._locks: Dict[str, threading.Lock] = {
            name: threading.Lock() for name in resource_names
        }

    def is_locked(self, resource_name: str) -> bool:
        if resource_name not in self._locks:
            raise KeyError(f"Unknown resource: {resource_name}")
        lock = self._locks[resource_name]
        # Check if lock can be acquired immediately without blocking
        acquired = lock.acquire(blocking=False)
        if acquired:
            lock.release()
            return False
        return True

    @contextmanager
    def lock_resources(self, *resource_names: str):
        if not resource_names:
            yield
            return

        # Deduplicate and validate
        unique_names = set(resource_names)
        for name in unique_names:
            if name not in self._locks:
                raise KeyError(f"Unknown resource: {name}")

        # Enforce global total order (lexicographical sorting eliminates circular wait)
        ordered_names = sorted(unique_names)
        acquired_locks = []

        try:
            for name in ordered_names:
                lock = self._locks[name]
                lock.acquire()
                acquired_locks.append(lock)
            yield
        finally:
            # Release in LIFO order
            for lock in reversed(acquired_locks):
                lock.release()
