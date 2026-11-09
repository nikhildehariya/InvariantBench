# Task 07: Python AST Function Instrumentation with Strict Hygiene

## Problem Description
Automated code instrumenters (such as APM tracers, coverage profilers, and contract checkers) modify Python Abstract Syntax Trees (AST) prior to compilation. However, improper AST manipulation frequently introduces subtle bugs: destroying function `__doc__` docstrings, corrupting bytecode source maps, or crashing on `async def` functions.

Implement an AST transformer class `FunctionCallTracer(ast.NodeTransformer)` and a helper function `instrument_source(source_code: str, tracer_func_name: str = "__trace__") -> str`:

### Requirements:
1. **Target Functions**:
   Instruments both standard functions (`ast.FunctionDef`) and asynchronous functions (`ast.AsyncFunctionDef`).

2. **Injected Behavior**:
   At the start of every function body, inject a call to `tracer_func_name(func_name)`:
   ```python
   # e.g., if function name is "calculate", inject:
   __trace__("calculate")
   ```

3. **Critical AST Hygiene Invariants**:
   - **Docstring Preservation Invariant:** In Python, a docstring is recognized by the compiler ONLY if it is the very first statement in the function body. If the function has a docstring (`ast.get_docstring(node)`), the tracer call MUST be inserted **after** the docstring statement, NOT before it. `func.__doc__` must remain intact.
   - **AST Location Hygiene:** All newly created AST nodes must have valid `lineno`, `col_offset`, `end_lineno`, and `end_col_offset` so that `ast.fix_missing_locations(tree)` and `compile(tree, ...)` execute without `TypeError` or corrupted stack traces.
   - **Async Function Integrity:** Coroutine functions (`async def`) must remain valid coroutines that can be awaited cleanly.
