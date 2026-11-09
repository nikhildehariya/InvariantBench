# micro1 Eval Hackathon: Question 2 Submission (Subjective Question)

---

### 🎥 2-to-3 Minute Video Walkthrough:
**Video Link:** [Watch Evaluation & Live Benchmark Walkthrough on YouTube](https://youtu.be/SULIIofRhXU)  
*(Hosted externally as per micro1 submission guidelines; demonstration video showcases live execution of `python grader.py` across all 10 tasks, ground truth invariant verification, and frontier model failure mode capture).*

---

### Benchmark Title:
**InvariantBench: Probing Silent Invariant Violations, Concurrency Traps, and Numerical Corruption in Frontier AI Code Models**

---

### 1. Executive Summary & Core Objective
Modern frontier LLMs (such as GPT-4o, Claude 3.5 Sonnet, and OpenAI o1) demonstrate exceptional proficiency on standard code-generation benchmarks like HumanEval and MBPP. However, these traditional benchmarks suffer from superficial evaluation: they rely on naive input-output matching on toy scripts. In production engineering, code that passes standard unit tests frequently harbors subtle, catastrophic defects: orphaned asynchronous tasks, non-zero gradient leakage in autograd graphs, floating-point penny drift in financial allocations, circular wait deadlocks under thread contention, and rollback failure when generator contexts terminate.

**InvariantBench** is an evaluation benchmark comprising **10 production-grade tasks (47 rigorous programmatic test cases)** designed specifically to probe where frontier models fail silently. Each task targets a defensible system or mathematical invariant that frontier models consistently breach despite generating syntactically valid and clean-looking code.

---

### 2. Targeted Tasks & Frontier Model Failure Modes

1. **TASK-01: Async Orphan Task Prevention & Shielded Cancellation (Async Concurrency)**
   - *Failure Mode:* Frontier models frequently misuse `asyncio.shield` without maintaining an internal registry of running tasks, or execute `task.cancel()` during pool shutdown without awaiting `asyncio.gather(..., return_exceptions=True)`.
   - *Invariant Tested:* When outer coroutines are cancelled, background shielded tasks must remain tracked, complete their critical sections, and drain to zero dangling/orphan `asyncio.Task` instances in the event loop upon shutdown.

2. **TASK-02: Reverse-Mode Autodiff Engine with Broadcast Invariants (Deep Learning / Math)**
   - *Failure Mode:* When implementing computational graphs with reverse-mode automatic differentiation from scratch, LLMs overwrite node adjoints (`grad = ...` instead of `grad += ...`) and fail to sum out broadcasted dimensions in reverse operations, causing dimension mismatch or corrupt gradients.
   - *Invariant Tested:* Reverse-mode analytical gradients must match two-sided finite-difference numerical gradients ($f'(x) \approx \frac{f(x+\epsilon)-f(x-\epsilon)}{2\epsilon}$) within $10^{-4}$ tolerance across multi-branch and broadcast-expanded dimensions.

3. **TASK-03: Discrete Financial Penny-Drift & Conservation Invariants (Computational Finance)**
   - *Failure Mode:* Models perform floating-point divisions or independent `round(..., 2)` rounding, causing cumulative penny drift ($\sum \text{allocated} \ne \text{total}$), or dump the leftover cents arbitrarily onto the last account in the list.
   - *Invariant Tested:* Strict **Conservation of Money** ($\sum a_i \equiv T$ down to 0 cents drift) implementing the Largest Remainder (Hare-Niemeyer) method with deterministic alphabetical tie-breaking.

4. **TASK-04: Deterministic DAG Resolution & Minimal Cycle Path Extraction (Systems & Graph Theory)**
   - *Failure Mode:* Models rely on recursive DFS that throws `RecursionError: maximum recursion depth exceeded` on 3,000+ deep dependency chains, produce non-deterministic build sequences due to set iteration, or fail to isolate minimal cycle paths when loops occur.
   - *Invariant Tested:* Iterative $O(V+E)$ Kahn's algorithm with min-heap priority queue; linear chain scalability up to 10,000+ nodes without recursion; exact minimal cycle loop extraction (`[A, B, C, A]`).

5. **TASK-05: ACID Transaction Rollback on Generator Exit (Database Internals / PEP 342 & 533)**
   - *Failure Mode:* Context managers implemented via generators catch only `Exception` rather than `BaseException`. When callers break out of loops or abandon generators, Python raises `GeneratorExit`. As a result, rollback logic is skipped and active transaction locks remain permanently dangling.
   - *Invariant Tested:* Guaranteed transactional rollback and lock cleanup on any premature interruption (including `GeneratorExit` and `KeyboardInterrupt`), alongside nested transaction savepoint isolation.

6. **TASK-06: Hierarchical Multi-Lock Acquisition & Deadlock Avoidance (Systems & Concurrency)**
   - *Failure Mode:* Worker threads requesting overlapping bundles of named locks (e.g., transfers between Account A and Account B) acquire locks in caller-provided order, creating Coffman circular wait deadlocks under concurrency, or self-deadlock when the same key appears twice.
   - *Invariant Tested:* Dijkstra's Global Lock Total Ordering (eliminating circular wait under 20+ concurrent contending threads) and guaranteed LIFO release under exception unwinding.

7. **TASK-07: Python AST Function Instrumentation with Strict Hygiene (Metaprogramming & Compilers)**
   - *Failure Mode:* Code transformers that instrument functions blindly inject trace calls at `body.insert(0, ...)`, destroying function `__doc__` docstrings (which must be statement 0). Models also overlook `ast.AsyncFunctionDef` and omit AST location metadata (`ast.fix_missing_locations`).
   - *Invariant Tested:* Strict preservation of function docstrings (`fn.__doc__`), transparent instrumentation of both sync and `async def` coroutines, and valid bytecode compilability.

8. **TASK-08: Operator Precedence & Associativity Invariants in Expression Parsers (Compilers & Parsing)**
   - *Failure Mode:* LLM-generated recursive descent and Pratt parsers treat exponentiation (`**`) as left-associative via while loops, evaluating `2 ** 3 ** 2` as 64 instead of 512, and miscalculate unary minus precedence (`-2 ** 2`).
   - *Invariant Tested:* Strict right-associativity of exponentiation, operator precedence ordering (`**` > unary `-` > `*` > `+`), validated via property-based fuzzing against native Python semantics.

9. **TASK-09: Lazy Iterator Pipeline Protocol Invariants (Python Internals & Streaming)**
   - *Failure Mode:* Data pipelines eagerly materialize intermediate collections via `list()`, consuming $O(N)$ memory and causing infinite loops on unbounded sources (e.g., `itertools.count`).
   - *Invariant Tested:* Guaranteed $O(1)$ peak memory, lazy evaluation over infinite streams, and single-pass consumption invariants.

10. **TASK-10: Thread-Safe LRU-TTL Cache with Atomic Eviction Invariants (In-Memory Systems)**
    - *Failure Mode:* Concurrent cache implementations mutate `OrderedDict` during iteration (`RuntimeError`), promote expired entries to MRU position upon failed lookup, and evict valid LRU entries instead of sweeping expired entries when at capacity.
    - *Invariant Tested:* Monotonic clock resilience (`time.monotonic()`), smart capacity eviction of expired entries before valid LRU entries, and lock-protected thread safety under multi-threaded contention.

---

### 3. Defensible Ground Truth & Grading Methodology

The grading framework is engineered to eliminate false passes and false failures:
- **No Heavyweight Dependencies:** The benchmark runs in < 2 seconds on standard Python 3.9+ with only NumPy. No PyTorch or CUDA required.
- **Defensible Ground Truth:** Reference implementations (`ground_truth.py`) achieve a verified **100.0% pass rate (47/47 test cases across all 10 tasks)**.
- **Zero False Passes:** Buggy baselines representative of outputs generated by GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro achieve a **0.0% task pass rate**, failing specifically on the targeted system invariants.
- **Concurrency & Deadlock Watchdogs:** Multi-threaded and async tasks incorporate generous deadline watchdogs (3.5s) to eliminate false timeouts on virtualized/single-core CI runners while deterministically catching hangs, leaks, and deadlocks.

---

### 4. Reproduction & Verification Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Execute Master Grader:**
   ```bash
   python grader.py
   ```
   *Output:* Executes both Ground Truth and Frontier Failure Baselines, prints ANSI diagnostic tables, and generates `benchmark_report.md` and `benchmark_report.html`.
3. **Run Comparative CLI Analysis:**
   ```bash
   python eval.py --compare --report
   ```
4. **Evaluate Custom Solutions:**
   ```bash
   python eval.py --custom path/to/candidate.py --task TASK-01
   ```
5. **Verify Submission Package:**
   ```bash
   python package_submission.py
   ```
   *Creates and verifies `micro1_invariant_bench_submission.zip` (< 1 MB, strictly source code).*
