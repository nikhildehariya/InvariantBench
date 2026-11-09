"""Buggy LLM Baseline for Task 09.

Representative of typical frontier LLM outputs:
1. Eagerly calls list() on intermediate stages, defeating laziness and
   crashing on infinite iterables.
2. StopIteration raised inside a user fn leaks through, silently
   terminating the generator instead of raising RuntimeError (PEP-479).
"""

from typing import Callable, Iterable, List, Any


class LazyPipeline:
    def __init__(self, iterable: Iterable):
        # LLM TRAP: Materializes entire source immediately!
        self._data = list(iterable)

    def map(self, fn: Callable[[Any], Any]) -> "LazyPipeline":
        # LLM TRAP: Eagerly maps into a new list
        new = LazyPipeline.__new__(LazyPipeline)
        new._data = [fn(x) for x in self._data]
        return new

    def filter(self, predicate: Callable[[Any], bool]) -> "LazyPipeline":
        new = LazyPipeline.__new__(LazyPipeline)
        new._data = [x for x in self._data if predicate(x)]
        return new

    def take(self, n: int) -> "LazyPipeline":
        new = LazyPipeline.__new__(LazyPipeline)
        new._data = self._data[:n]
        return new

    def skip(self, n: int) -> "LazyPipeline":
        new = LazyPipeline.__new__(LazyPipeline)
        new._data = self._data[n:]
        return new

    def flat_map(self, fn: Callable[[Any], Iterable]) -> "LazyPipeline":
        new = LazyPipeline.__new__(LazyPipeline)
        new._data = [item for x in self._data for item in fn(x)]
        return new

    def __iter__(self):
        return iter(self._data)

    def to_list(self) -> List:
        return list(self._data)
