"""Test suite for Task 05: Transaction Store."""

import time
from typing import List
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    StoreClass = getattr(candidate_module, "TransactionStore", None)

    if StoreClass is None:
        results.append(
            TestCaseResult(
                name="class_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="TransactionStore not found in candidate module",
            )
        )
        return results

    # Test 1: Commit and Isolation Invariant
    def _test_commit_isolation():
        store = StoreClass()
        with store.transaction() as tx:
            tx.set("name", "Alice")
            assert tx.get("name") == "Alice"
            # Outside store must NOT see uncommitted changes yet
            assert store.get("name") is None, "Isolation broken: uncommitted change visible in store"

        # After commit
        assert store.get("name") == "Alice", "Committed change not visible in store"

    t0 = time.perf_counter()
    try:
        _test_commit_isolation()
        results.append(TestCaseResult("test_commit_and_isolation", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_commit_and_isolation", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Standard Exception Rollback Invariant
    def _test_exception_rollback():
        store = StoreClass()
        with store.transaction() as tx:
            tx.set("balance", 100)

        try:
            with store.transaction() as tx:
                tx.set("balance", 999)
                raise RuntimeError("Simulated crash")
        except RuntimeError:
            pass

        assert store.get("balance") == 100, "Rollback failed: balance corrupted after exception"

    t0 = time.perf_counter()
    try:
        _test_exception_rollback()
        results.append(TestCaseResult("test_exception_rollback", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_exception_rollback", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: GeneratorExit Premature Termination Rollback Trap
    def _test_generator_exit():
        store = StoreClass()
        store._data["safe_key"] = "safe_value"

        def transaction_generator():
            with store.transaction() as tx:
                tx.set("safe_key", "tainted_value")
                tx.set("new_key", "ghost")
                yield "started"
                yield "finished"

        # Create generator, consume first yield, then close early
        gen = transaction_generator()
        val = next(gen)
        assert val == "started"

        # Force generator premature closure (raises GeneratorExit inside the context manager)
        gen.close()

        # Invariant checks:
        # 1. safe_key must NOT be corrupted
        assert store.get("safe_key") == "safe_value", (
            f"GeneratorExit Trap: State polluted! safe_key is '{store.get('safe_key')}', "
            "expected 'safe_value'. Model failed to rollback on GeneratorExit."
        )
        assert store.get("new_key") is None, "Ghost key remained committed after generator closed"
        # 2. Store must not be stuck in transaction state
        assert not store.is_in_transaction, "Store remained locked in transaction after GeneratorExit"

    t0 = time.perf_counter()
    try:
        _test_generator_exit()
        results.append(TestCaseResult("test_generator_exit_rollback", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_generator_exit_rollback", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Nested Transaction Savepoint Isolation
    def _test_nested_savepoints():
        store = StoreClass()
        with store.transaction() as outer_tx:
            outer_tx.set("outer_key", "outer_val")
            outer_tx.set("shared_key", "initial_val")

            # Store must report still in transaction
            assert store.is_in_transaction, "Store is_in_transaction should be True during outer tx"

            # Nested transaction that modifies shared_key and rolls back
            try:
                with store.transaction() as inner_tx:
                    inner_tx.set("inner_key", "inner_val")
                    inner_tx.set("shared_key", "overwritten_by_inner")
                    assert inner_tx.get("shared_key") == "overwritten_by_inner"
                    raise ValueError("Abort inner transaction")
            except ValueError:
                pass

            # Outer store must still be active and shared_key must revert to outer_tx's value!
            assert store.is_in_transaction, "Inner tx abort prematurely terminated outer transaction state"
            assert outer_tx.get("shared_key") == "initial_val", (
                f"Nested rollback polluted outer tx! Got {outer_tx.get('shared_key')}, expected 'initial_val'"
            )
            assert outer_tx.get("inner_key") is None, "Inner rolled-back key visible in outer tx"
            outer_tx.set("outer_key2", "outer_val2")

        assert store.get("outer_key") == "outer_val"
        assert store.get("outer_key2") == "outer_val2"
        assert store.get("shared_key") == "initial_val"
        assert store.get("inner_key") is None

    t0 = time.perf_counter()
    try:
        _test_nested_savepoints()
        results.append(TestCaseResult("test_nested_savepoint_isolation", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_nested_savepoint_isolation", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
