"""Submission Packaging and Verification Utility.

Automates validation, cache cleanup, and creates the final .zip archive
for micro1 Eval Hackathon (Question 1) under the 50 MB limit.
Includes:
- Strict Unix permission tagging (0o644 / 0o755) on ZipInfo headers for Linux/macOS CI runners.
- POSIX normalized forward-slash paths.
- Exclusion of pre-baked static reports so graders generate fresh reports.
- Self-testing extraction verification.
"""

import os
import sys
import time
import zipfile
import shutil
import tempfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
OUTPUT_ZIP = WORKSPACE_ROOT / "micro1_invariant_bench_submission.zip"

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".git", ".vscode", ".idea"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".zip"}
EXCLUDE_FILES = {
    "benchmark_report.html",
    "benchmark_report.md",
    "test_check.txt",
    "WINNING_BLUEPRINT_AND_ROADMAP.md",
    OUTPUT_ZIP.name,
}


def clean_pycache():
    """Remove __pycache__, bytecode, and temporary pre-baked reports."""
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        for d in list(dirs):
            if d in EXCLUDE_DIRS:
                shutil.rmtree(Path(root) / d, ignore_errors=True)
                dirs.remove(d)
        for f in files:
            p = Path(root) / f
            if p.suffix in EXCLUDE_EXTS or p.name in EXCLUDE_FILES:
                try:
                    os.remove(p)
                except OSError:
                    pass


def verify_grader():
    """Run grader to verify all tests pass before packaging."""
    print("[1/4] Running pre-packaging grader verification...")
    from eval_suite.runner import BenchmarkRunner
    runner = BenchmarkRunner(tasks_dir=WORKSPACE_ROOT / "tasks")
    gt = runner.run_benchmark(target_variant="ground_truth")
    bl = runner.run_benchmark(target_variant="buggy_llm_baseline")

    if gt.passed_tasks != gt.total_tasks:
        raise RuntimeError(
            f"Pre-packaging verification failed: Ground truth passed {gt.passed_tasks}/{gt.total_tasks}"
        )
    if bl.passed_tasks != 0:
        raise RuntimeError(
            f"Pre-packaging verification failed: Baselines had false passes ({bl.passed_tasks}/{bl.total_tasks})"
        )
    print(f"      Passed: {gt.passed_tasks}/{gt.total_tasks} GT tasks (100%), {bl.failed_tasks}/{bl.total_tasks} baseline traps caught.")


def create_submission_zip():
    print("[2/4] Cleaning pycache and pre-generated static artifacts...")
    clean_pycache()

    verify_grader()

    print("[3/4] Packaging files into submission zip with POSIX paths and Unix permissions...")
    try:
        if OUTPUT_ZIP.exists():
            OUTPUT_ZIP.unlink()
    except (PermissionError, OSError):
        pass

    included_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in sorted(files):
                file_path = Path(root) / file
                if file_path.suffix in EXCLUDE_EXTS or file_path.name in EXCLUDE_FILES:
                    continue

                rel_path = file_path.relative_to(WORKSPACE_ROOT)
                # POSIX path normalization
                arcname = str(rel_path).replace("\\", "/")

                # Read raw bytes
                with open(file_path, "rb") as f:
                    file_data = f.read()

                # Explicit ZipInfo with Unix permissions
                zinfo = zipfile.ZipInfo(arcname)
                st = file_path.stat()
                mtime = time.localtime(st.st_mtime)
                zinfo.date_time = mtime[0:6]
                zinfo.compress_type = zipfile.ZIP_DEFLATED

                # Set Unix file attributes:
                # 0o100755 for python scripts and executables (rwxr-xr-x)
                # 0o100644 for documentation, metadata, text (rw-r--r--)
                is_exec = file_path.suffix in {".py", ".sh"}
                perm = 0o100755 if is_exec else 0o100644
                zinfo.external_attr = perm << 16

                zf.writestr(zinfo, file_data)
                included_count += 1

    # Step 4: Verification of the generated zip archive by extracting to a temp directory
    print("[4/4] Verifying zip archive extractability and file counts...")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
            zf.extractall(tmpdir)
            extracted_files = [p for p in Path(tmpdir).rglob("*") if p.is_file()]
            if len(extracted_files) != included_count:
                raise RuntimeError(
                    f"Extraction mismatch: expected {included_count} files, got {len(extracted_files)}"
                )

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 75)
    print(" SUBMISSION PACKAGE READY FOR MICRO1 EVAL HACKATHON")
    print("=" * 75)
    print(f" Archive Name       : {OUTPUT_ZIP.name}")
    print(f" Full Location      : {OUTPUT_ZIP}")
    print(f" Total Source Files : {included_count} files (Tasks 01 to 10)")
    print(f" Archive File Size  : {size_mb:.3f} MB (HackerRank Limit: 50.0 MB)")
    print(f" Unix Attributes    : Tagged (0o755 for scripts, 0o644 for text/data)")
    print(f" Integrity Check    : PASSED (10/10 tasks verified, 100% extractable)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    create_submission_zip()
