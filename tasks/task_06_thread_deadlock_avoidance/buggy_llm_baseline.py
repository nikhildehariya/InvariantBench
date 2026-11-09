"""Buggy LLM Baseline Implementation for Task 06.

Representative of typical frontier LLM outputs:
1. Acquires locks in the arbitrary order passed by the caller without total ordering,
   causing classic circular wait deadlocks under concurrent contention.
2. Fails to deduplicate resource names, resulting in self-deadlock when a resource
   name appears multiple times in a single call.
"""

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
        acquired = lock.acquire(blocking=False)
        if acquired:
            lock.release()
            return False
        return True

    @contextmanager
    def lock_resources(self, *resource_names: str):
        # LLM TRAP 1: Does NOT deduplicate, self-deadlocking on duplicate keys!
        # LLM TRAP 2: Iterates in caller-provided order rather than global total sort!
        for name in resource_names:
            if name not in self._locks:
                raise KeyError(f"Unknown resource: {name}")

        acquired = []
        try:
            for name in resource_names:
                l = self._locks[name]
                l.acquire()
                acquired.append(l)
            yield
        finally:
            for l in acquired:
                l.release()
