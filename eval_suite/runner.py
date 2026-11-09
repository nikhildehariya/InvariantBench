"""Evaluation test runner for InvariantBench.

Executes task test suites against candidate implementations with
timeout enforcement, structured error capture, and invariant verification.
"""

import os
import sys
import time
import json
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from eval_suite.models import (
    TestStatus,
    TestCaseResult,
    TaskMetadata,
    TaskEvaluationResult,
    BenchmarkSummary,
)


class BenchmarkRunner:
    def __init__(self, tasks_dir: Optional[Path] = None):
        if tasks_dir is None:
            self.tasks_dir = Path(__file__).resolve().parent.parent / "tasks"
        else:
            self.tasks_dir = Path(tasks_dir)

    def discover_tasks(self) -> List[Path]:
        """Discover all task directories sorted by task ID."""
        task_dirs = []
        if not self.tasks_dir.exists():
            return []
        for p in sorted(self.tasks_dir.iterdir()):
            if p.is_dir() and (p / "metadata.json").exists() and (p / "test_suite.py").exists():
                task_dirs.append(p)
        return task_dirs

    def load_metadata(self, task_dir: Path) -> TaskMetadata:
        """Load task metadata from metadata.json."""
        with open(task_dir / "metadata.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return TaskMetadata(
            task_id=data.get("task_id", task_dir.name),
            title=data.get("title", task_dir.name),
            domain=data.get("domain", "General"),
            difficulty=data.get("difficulty", "Hard"),
            failure_mode=data.get("failure_mode", ""),
            invariant_guarantee=data.get("invariant_guarantee", ""),
            targeted_llms=data.get("targeted_llms", []),
        )

    def import_module_from_path(self, module_name: str, file_path: Path):
        """Dynamically import a Python module from a file path."""
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {file_path}")
        module = importlib.util.module_from_spec(spec)
        # Add task directory to sys.path temporarily if needed
        parent_dir = str(file_path.parent)
        added_path = False
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            added_path = True
        try:
            spec.loader.exec_module(module)
        finally:
            if added_path and parent_dir in sys.path:
                sys.path.remove(parent_dir)
        return module

    def evaluate_task(
        self,
        task_dir: Path,
        target_variant: str = "ground_truth",
        custom_file: Optional[Path] = None,
    ) -> TaskEvaluationResult:
        """
        Evaluate a single task.
        target_variant: 'ground_truth' or 'buggy_llm_baseline'
        """
        meta = self.load_metadata(task_dir)

        if custom_file is not None:
            candidate_path = custom_file
            target_label = f"custom:{custom_file.name}"
        elif target_variant == "buggy_llm_baseline":
            candidate_path = task_dir / "buggy_llm_baseline.py"
            target_label = "buggy_llm_baseline"
        else:
            candidate_path = task_dir / "ground_truth.py"
            target_label = "ground_truth"

        if not candidate_path.exists():
            return TaskEvaluationResult(
                task_id=meta.task_id,
                title=meta.title,
                domain=meta.domain,
                target_evaluated=target_label,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                duration_ms=0.0,
                failure_summary=f"Candidate file not found: {candidate_path}",
            )

        test_suite_path = task_dir / "test_suite.py"
        start_time = time.perf_counter()

        try:
            # Load candidate module
            candidate_module = self.import_module_from_path(
                f"candidate_{meta.task_id}", candidate_path
            )

            # Load test suite module
            suite_module = self.import_module_from_path(
                f"suite_{meta.task_id}", test_suite_path
            )

            if not hasattr(suite_module, "run_task_tests"):
                raise AttributeError(
                    f"Test suite {test_suite_path} must define 'run_task_tests(candidate)'"
                )

            # Execute programmatic tests
            test_results: List[TestCaseResult] = suite_module.run_task_tests(candidate_module)

        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            err_case = TestCaseResult(
                name="module_execution_initialization",
                status=TestStatus.ERROR,
                duration_ms=elapsed,
                message=str(e),
                stack_trace=str(e),
            )
            return TaskEvaluationResult(
                task_id=meta.task_id,
                title=meta.title,
                domain=meta.domain,
                target_evaluated=target_label,
                passed=False,
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                duration_ms=elapsed,
                test_cases=[err_case],
                failure_summary=f"Execution error: {e}",
            )

        elapsed_total = (time.perf_counter() - start_time) * 1000
        passed_count = sum(1 for t in test_results if t.status == TestStatus.PASS)
        failed_count = sum(1 for t in test_results if t.status != TestStatus.PASS)
        all_passed = (failed_count == 0) and (len(test_results) > 0)

        failure_summary = None
        if not all_passed:
            failed_names = [t.name for t in test_results if t.status != TestStatus.PASS]
            failure_summary = f"Failed tests ({failed_count}): {', '.join(failed_names)}"

        return TaskEvaluationResult(
            task_id=meta.task_id,
            title=meta.title,
            domain=meta.domain,
            target_evaluated=target_label,
            passed=all_passed,
            total_tests=len(test_results),
            passed_tests=passed_count,
            failed_tests=failed_count,
            duration_ms=elapsed_total,
            test_cases=test_results,
            failure_summary=failure_summary,
        )

    def run_benchmark(
        self,
        target_variant: str = "ground_truth",
        task_filter: Optional[str] = None,
    ) -> BenchmarkSummary:
        """Run evaluation across all discovered tasks."""
        start_wall = time.perf_counter()
        task_dirs = self.discover_tasks()
        results: List[TaskEvaluationResult] = []

        if task_filter:
            task_dirs = [d for d in task_dirs if task_filter.lower() in d.name.lower()]

        for task_dir in task_dirs:
            res = self.evaluate_task(task_dir, target_variant=target_variant)
            results.append(res)

        total_duration = time.perf_counter() - start_wall
        passed_tasks = sum(1 for r in results if r.passed)
        failed_tasks = len(results) - passed_tasks
        pass_rate = (passed_tasks / len(results) * 100.0) if results else 0.0

        # Domain breakdown
        domain_scores: Dict[str, Dict[str, Any]] = {}
        for r in results:
            if r.domain not in domain_scores:
                domain_scores[r.domain] = {"total": 0, "passed": 0}
            domain_scores[r.domain]["total"] += 1
            if r.passed:
                domain_scores[r.domain]["passed"] += 1

        for d, data in domain_scores.items():
            data["rate"] = (data["passed"] / data["total"] * 100.0) if data["total"] else 0.0

        return BenchmarkSummary(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_evaluated=target_variant,
            total_tasks=len(results),
            passed_tasks=passed_tasks,
            failed_tasks=failed_tasks,
            pass_rate_pct=pass_rate,
            total_duration_sec=total_duration,
            domain_scores=domain_scores,
            results=results,
        )
