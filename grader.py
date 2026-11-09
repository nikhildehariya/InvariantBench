"""InvariantBench: Automated Grader and Evaluation Runner.

Entry point for the micro1 Eval Hackathon evaluation harness.
Usage:
    python grader.py
"""

import sys
import os
from pathlib import Path

# Ensure workspace root is on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from eval_suite.runner import BenchmarkRunner
from eval_suite.reporter import BenchmarkReporter


def main():
    print("\n" + "=" * 80)
    print(" InvariantBench: Automated Evaluation Suite")
    print(" micro1 Eval Hackathon Submission")
    print("=" * 80)

    runner = BenchmarkRunner(tasks_dir=WORKSPACE_ROOT / "tasks")

    discovered = runner.discover_tasks()
    if not discovered:
        print("[ERROR] No task directories discovered. Check the 'tasks/' folder.")
        sys.exit(1)

    #  Step 1: Evaluate Ground Truth Reference Implementations 
    print(f"\n[STEP 1/3] Evaluating Ground Truth Reference Implementations "
          f"({len(discovered)} tasks discovered)...")
    gt_summary = runner.run_benchmark(target_variant="ground_truth")
    BenchmarkReporter.print_summary(gt_summary)

    #  Step 2: Evaluate Frontier Model Failure Baselines 
    print("\n[STEP 2/3] Evaluating Frontier Model Failure Baselines...")
    baseline_summary = runner.run_benchmark(target_variant="buggy_llm_baseline")
    BenchmarkReporter.print_summary(baseline_summary)

    #  Step 3: Comparative Report Generation 
    print("\n[STEP 3/3] Generating Comparative Evaluation Reports...")
    BenchmarkReporter.print_comparison(gt_summary, baseline_summary)

    md_report_path = WORKSPACE_ROOT / "benchmark_report.md"
    html_report_path = WORKSPACE_ROOT / "benchmark_report.html"
    BenchmarkReporter.generate_markdown_report(gt_summary, baseline_summary, md_report_path)
    BenchmarkReporter.generate_html_report(gt_summary, baseline_summary, html_report_path)
    print(f"  -> Markdown: {md_report_path.name}")
    print(f"  -> HTML:     {html_report_path.name}")

    #  Integrity Verification 
    print("\n" + "=" * 80)
    print(" GRADER INTEGRITY CHECK")
    print("=" * 80)

    errors = []

    # Ground Truth: All tasks must pass
    if gt_summary.passed_tasks != gt_summary.total_tasks:
        errors.append(
            f"[FAIL] Ground Truth pass rate is {gt_summary.pass_rate_pct:.1f}% "
            f"({gt_summary.passed_tasks}/{gt_summary.total_tasks}). "
            "Expected 100%. Check for environment issues or missing files.\n"
            "Failed tasks:"
        )
        for r in gt_summary.results:
            if not r.passed:
                errors.append(f"  - {r.task_id}: {r.failure_summary}")

    # Baselines: All tasks must fail on at least one invariant test
    false_passes = [r for r in baseline_summary.results if r.passed]
    if false_passes:
        errors.append(
            f"[WARN] {len(false_passes)} frontier baseline(s) passed ALL invariant tests  -  "
            "these tasks may have insufficiently rigorous test suites:"
        )
        for r in false_passes:
            errors.append(f"  - {r.task_id}: {r.title}")

    if errors:
        print("\n".join(errors))
        print("\n[ACTION NEEDED] Address the above issues before final submission.")
        sys.exit(1)
    else:
        print(f"\n [OK] Ground Truth Pass Rate       : 100.0% ({gt_summary.total_tasks}/{gt_summary.total_tasks} tasks)")
        print(f" [OK] Targeted Failure Capture Rate: 100.0% ({baseline_summary.total_tasks}/{baseline_summary.total_tasks} failure modes isolated)")
        print(f" [OK] False Pass Rate              : 0.00% (all invariant traps triggered correctly)")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
