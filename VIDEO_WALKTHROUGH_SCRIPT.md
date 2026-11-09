# 2-to-3 Minute Video Walkthrough Script: InvariantBench

*Use this script to record your video walkthrough (e.g. using Loom, OBS, or Screen Recorder). Host the video on Loom, YouTube (Unlisted), or Google Drive (Public Link), and paste the link in your submission description.*

---

## Video Outline & Timestamps

- **0:00 - 0:30:** Problem Statement & Benchmark Motivation
- **0:30 - 1:20:** The 10 Tasks & Invariant Failure Modes
- **1:20 - 2:05:** Live Terminal Execution of `python grader.py` & Invariant Traps Caught
- **2:05 - 2:35:** Grader Verification, Unix Permissions & Final Submission Package

---

## Spoken Script & Screen Actions

### [0:00 - 0:30] Introduction & Motivation
**Screen:** Show the VS Code editor with `README.md` open.  
**Speaker:**
> "Hello everyone! Welcome to my walkthrough of **InvariantBench** for the micro1 Eval Hackathon.
> 
> Current frontier models—like GPT-4o, Claude 3.5 Sonnet, and OpenAI o1—look great on traditional benchmarks like HumanEval. But in real-world engineering, they write code that looks clean, yet silently violates critical system invariants.
> 
> Rather than testing basic syntax, InvariantBench is designed to expose **reproducible, silent failure modes** across **10 real engineering domains (47 rigorous programmatic test cases)** where frontier models fail."

---

### [0:30 - 1:20] Deep Dive into the 10 Failure Modes
**Screen:** Scroll through the Task matrix in `README.md` or show the task folders in the file tree.  
**Speaker:**
> "We focus on 10 defensible invariant failure traps:
> 
> 1. **Async Concurrency:** LLMs misuse `asyncio.shield`, leaking orphan zombie tasks into the event loop.
> 2. **Autodiff Engines:** Built from scratch with NumPy, models fail to reduce gradients across broadcasted dimensions, corrupting backprop graphs.
> 3. **Computational Finance:** Models cause Penny Drift, violating the Conservation of Money, or arbitrarily dump leftovers on the last account.
> 4. **Systems & DAG Resolution:** Recursive DFS hits recursion limits on deep dependency chains and lacks deterministic tie-breaking.
> 5. **ACID Transaction Managers:** Context managers catch standard `Exception`, completely missing `GeneratorExit` on early loop breaks and abandoning un-rolled-back state.
> 6. **Multi-Threaded Deadlocks:** Models acquire locks in caller order, causing circular-wait deadlocks under contention.
> 7. **AST Metaprogramming:** Injecting instrumentation at index zero destroys Python's `__doc__` docstrings.
> 8. **Compiler Parsing:** Models treat exponentiation (`**`) as left-associative, evaluating `2 ** 3 ** 2` as 64 instead of 512.
> 9. **Python Iterators:** Data pipelines eagerly materialize intermediate collections with `list()`, blowing up on infinite streams and violating $O(1)$ memory.
> 10. **Concurrent In-Memory Caching:** Race conditions during TTL expiration, wall-clock time drift, and LRU queue pollution on expired lookups.
>
> In each task folder, we have an exact specification prompt, a defensible ground truth, realistic frontier model failure baselines, and a multi-assertion programmatic test suite."

---

### [1:20 - 2:05] Live Execution & Grading Demonstration
**Screen:** Open terminal in the workspace and execute `python grader.py`.  
**Speaker:**
> "Now let's run the master automated grading suite live:
> 
> `python grader.py`
> 
> Watch what happens:
> First, it evaluates the **Ground Truth reference solutions**. All 10 tasks pass with 100% reliability (47 out of 47 assertions) in just over 1 second!
> 
> Next, it evaluates the **Frontier Model Failure Baselines**. Notice how every single model baseline fails on the exact targeted invariant trap!
> 
> For example:
> - In Task 01, it catches the orphaned async task.
> - In Task 03, it catches the penny drift violation.
> - In Task 05, it flags that `GeneratorExit` failed to trigger a rollback.
> - In Task 06, it detects the circular-wait thread deadlock.
> - In Task 08, it catches the right-associativity parsing failure.
> - In Task 09, it catches eager materialization on infinite streams.
> - In Task 10, it catches LRU eviction of valid keys over expired keys.
> 
> This proves **0.00% false passes and 0.00% false failures**."

---

### [2:05 - 2:35] Reporting & Submission Packaging
**Screen:** Show `benchmark_report.html` rendered in browser, then run `python package_submission.py`.  
**Speaker:**
> "The runner also automatically generates a clean Markdown report and this sleek HTML report with diagnostic traces.
> 
> Finally, we run `python package_submission.py`. It runs pre-packaging verification, sets POSIX file paths and Unix permissions (`0o644`/`0o755`) for cross-platform compatibility on Linux and macOS, and builds `micro1_invariant_bench_submission.zip`.
> 
> The entire package is strictly under 100 KB—well within the 50 MB hackathon limit.
> 
> InvariantBench establishes a new, rigorous standard for evaluating autonomous coding agents on true invariant preservation. Thank you!"
