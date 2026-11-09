"""Buggy LLM Baseline Implementation for Task 01.

Representative of typical frontier LLM outputs (GPT-4o, Claude 3.5 Sonnet):
1. Fails to track shielded inner tasks separately; when caller cancels, the task
   becomes an untracked zombie in the event loop.
2. In shutdown(), issues t.cancel() without properly awaiting task teardown,
   leaving lingering pending tasks and triggering EventLoop warnings.
"""

import asyncio
from typing import Callable, Any, Optional, List


class ShieldedWorkerPool:
    def __init__(self, max_concurrency: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._running_tasks: List[asyncio.Task] = []
        self._closed = False

    @property
    def active_count(self) -> int:
        # LLM bug: filters finished tasks lazily, but doesn't track shielded orphan tasks
        return len([t for t in self._running_tasks if not t.done()])

    async def submit(
        self,
        coro_fn: Callable[..., Any],
        *args,
        shield_execution: bool = False,
        **kwargs
    ) -> Any:
        if self._closed:
            raise RuntimeError("Pool is closed")

        if shield_execution:
            # LLM TRAP: creates a task, wraps with shield, but on CancelledError
            # removes it from _running_tasks, completely losing tracking!
            async with self._semaphore:
                task = asyncio.create_task(coro_fn(*args, **kwargs))
                self._running_tasks.append(task)
                try:
                    return await asyncio.shield(task)
                except asyncio.CancelledError:
                    # Bug: deletes task from list, leaving it orphaned in loop
                    if task in self._running_tasks:
                        self._running_tasks.remove(task)
                    raise
        else:
            async with self._semaphore:
                return await coro_fn(*args, **kwargs)

    async def shutdown(self, wait: bool = True, timeout: Optional[float] = 2.0) -> None:
        self._closed = True
        # LLM TRAP: If wait=False or on timeout, cancels without awaiting gather(),
        # leaving tasks executing in background after shutdown returns!
        for t in self._running_tasks:
            if not t.done():
                t.cancel()
        # Does not await cancellation of cancelled tasks!
