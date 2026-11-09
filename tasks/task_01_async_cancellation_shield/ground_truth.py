"""Ground Truth Reference Implementation for Task 01."""

import asyncio
from typing import Callable, Any, Optional, Set


class ShieldedWorkerPool:
    def __init__(self, max_concurrency: int = 5):
        self._max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks: Set[asyncio.Task] = set()
        self._closed = False
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    async def submit(
        self,
        coro_fn: Callable[..., Any],
        *args,
        shield_execution: bool = False,
        **kwargs
    ) -> Any:
        if self._closed:
            raise RuntimeError("Pool is closed")

        async def _worker():
            async with self._semaphore:
                return await coro_fn(*args, **kwargs)

        task = asyncio.create_task(_worker())
        self._tasks.add(task)
        task.add_done_callback(lambda t: self._tasks.discard(t))

        if not shield_execution:
            try:
                return await task
            except asyncio.CancelledError:
                # Cancel the inner task if not shielded
                task.cancel()
                raise
        else:
            # Shielded execution: caller's cancellation propagates to caller,
            # but inner task continues and remains in self._tasks until done
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                # Outer task was cancelled. Re-raise cancellation to caller,
                # but keep the internal task tracked in self._tasks!
                raise

    async def shutdown(self, wait: bool = True, timeout: Optional[float] = 2.0) -> None:
        self._closed = True
        if not self._tasks:
            return

        active_tasks = list(self._tasks)

        if wait:
            # Wait for active tasks up to timeout
            done, pending = await asyncio.wait(active_tasks, timeout=timeout)
            if not pending:
                return
            active_tasks = list(pending)

        # Force cancel remaining tasks and await their completion to avoid orphan warnings
        for t in active_tasks:
            t.cancel()

        if active_tasks:
            await asyncio.gather(*active_tasks, return_exceptions=True)

        self._tasks.clear()
