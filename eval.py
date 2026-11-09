"""InvariantBench CLI Interface.

Allows running evaluations on specific tasks, custom files, or full benchmarks.
Usage:
    python eval.py --target ground_truth
    python eval.py --target buggy_llm_baseline
    python eval.py --task TASK-01
    python eval.py --custom path/to/my_solution.py --task TASK-03
"""

import sys
import argparse
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from eval_suite.runner import BenchmarkRunner
from eval_suite.reporter import BenchmarkReporter


def main():
    parser = argparse.ArgumentParser(
        description="InvariantBench: Evaluation Suite for Frontier AI Code Models"
    )
    parser.add_argument(
        "--target",
        choices=["ground_truth", "buggy_llm_baseline"],
        default="ground_truth",
        help="Target implementation variant to evaluate (default: ground_truth)",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Filter evaluation to a specific task ID (e.g. TASK-01) or substring",
    )
    parser.add_argument(
        "--custom",
        type=str,
        default=None,
        help="Path to a custom candidate Python file to evaluate against a task",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run comparative evaluation between ground truth and frontier baseline",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Export Markdown and HTML benchmark reports",
    )

    args = parser.parse_args()
    runner = BenchmarkRunner(tasks_dir=WORKSPACE_ROOT / "tasks")

    if args.custom:
        if not args.task:
            print("Error: --task must be specified when using --custom.")
            sys.exit(1)

        # Fix #10: Check file existence upfront before any discovery
        custom_path = Path(args.custom).resolve()
        if not custom_path.exists():
            print(f"Error: Custom file not found: {custom_path}")
            sys.exit(1)
        if not custom_path.is_file():
            print(f"Error: Path is not a file: {custom_path}")
            sys.exit(1)

        task_dirs = [d for d in runner.discover_tasks() if args.task.lower() in d.name.lower()]
        if not task_dirs:
            print(f"Error: Task '{args.task}' not found in tasks/ directory.")
            sys.exit(1)
        res = runner.evaluate_task(task_dirs[0], custom_file=custom_path)
        print(f"Task: {res.task_id} ({res.title})")
        print(f"Result: {'PASS' if res.passed else 'FAIL'} ({res.passed_tests}/{res.total_tests} tests)")
        if not res.passed and res.failure_summary:
            print(f"Reason: {res.failure_summary}")
        sys.exit(0 if res.passed else 1)

    if args.compare:
        gt_summary = runner.run_benchmark(target_variant="ground_truth", task_filter=args.task)
        bl_summary = runner.run_benchmark(target_variant="buggy_llm_baseline", task_filter=args.task)
        BenchmarkReporter.print_comparison(gt_summary, bl_summary)
        if args.report:
            BenchmarkReporter.generate_markdown_report(gt_summary, bl_summary, WORKSPACE_ROOT / "benchmark_report.md")
            BenchmarkReporter.generate_html_report(gt_summary, bl_summary, WORKSPACE_ROOT / "benchmark_report.html")
            print("Reports saved to benchmark_report.md and benchmark_report.html")
        return

    summary = runner.run_benchmark(target_variant=args.target, task_filter=args.task)
    BenchmarkReporter.print_summary(summary)


if __name__ == "__main__":
    main()
