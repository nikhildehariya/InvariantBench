"""Ground Truth Reference Implementation for Task 09: Lazy Iterator Pipeline."""

from typing import Callable, Iterable, Iterator, TypeVar, Any, List

T = TypeVar("T")
U = TypeVar("U")


class LazyPipeline:
    def __init__(self, iterable: Iterable):
        # Wrap in iter() to ensure single-pass iterator semantics
        self._source = iter(iterable)

    def map(self, fn: Callable[[Any], Any]) -> "LazyPipeline":
        def _gen():
            for item in self._source:
                yield fn(item)
        return LazyPipeline(_gen())

    def filter(self, predicate: Callable[[Any], bool]) -> "LazyPipeline":
        def _gen():
            for item in self._source:
                if predicate(item):
                    yield item
        return LazyPipeline(_gen())

    def take(self, n: int) -> "LazyPipeline":
        def _gen():
            if n <= 0:
                return
            count = 0
            for item in self._source:
                yield item
                count += 1
                if count >= n:
                    break
        return LazyPipeline(_gen())

    def skip(self, n: int) -> "LazyPipeline":
        def _gen():
            skipped = 0
            for item in self._source:
                if skipped < n:
                    skipped += 1
                    continue
                yield item
        return LazyPipeline(_gen())

    def flat_map(self, fn: Callable[[Any], Iterable]) -> "LazyPipeline":
        def _gen():
            for item in self._source:
                yield from fn(item)
        return LazyPipeline(_gen())

    def __iter__(self) -> Iterator:
        return self._source

    def to_list(self) -> List:
        return list(self._source)
