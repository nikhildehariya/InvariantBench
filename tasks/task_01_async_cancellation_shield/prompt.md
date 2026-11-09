# Task 01: Resilient Async Worker Pool with Shielded Cancellation

## Problem Description
In high-throughput microservices, background jobs must be shielded against unexpected client disconnections, while simultaneously ensuring that worker pools do not leak orphan tasks into the Python `asyncio` event loop when outer coroutines are cancelled.

Implement a class `ShieldedWorkerPool` with the following requirements:

1. **`__init__(max_concurrency: int = 5)`**:
   Initializes the pool with a semaphore limiting maximum concurrent jobs.

2. **`async submit(coro_fn, *args, shield_execution: bool = False, **kwargs) -> Any`**:
   - Submits `coro_fn(*args, **kwargs)` for execution under concurrency control.
   - If `shield_execution=True`, the internal coroutine's critical work must NOT be abruptly aborted if the caller's `submit()` awaiting task is cancelled.
   - **Crucial Invariant:** If the outer caller task is cancelled, the pool MUST still internally track the ongoing shielded task. It must not become an untracked 'zombie' or 'orphan' task in the event loop.
   - If the outer caller is cancelled while awaiting `submit()`, the cancellation exception should propagate to the caller, but the shielded task must continue to completion within the pool's lifecycle.

3. **`async shutdown(wait: bool = True, timeout: Optional[float] = 2.0) -> None`**:
   - Stops accepting new submissions (subsequent `submit()` calls raise `RuntimeError("Pool is closed")`).
   - If `wait=True`, waits for all active (and shielded in-flight) tasks to complete up to `timeout` seconds.
   - If tasks are still running after `timeout` (or if `wait=False`), cancels remaining tasks and awaits their cancellation cleanly so that no tasks remain in `pending` state when `shutdown()` returns.

4. **`active_count -> int`**:
   Property returning the number of currently active in-flight worker tasks (including ongoing shielded tasks whose outer callers have cancelled).
