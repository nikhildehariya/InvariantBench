"""Buggy LLM Baseline Implementation for Task 07.

Representative of typical frontier LLM outputs:
1. Blindly inserts tracer node at index 0 of function body, destroying function docstrings.
2. Omits `visit_AsyncFunctionDef`, failing to instrument modern async coroutine functions.
3. Forgets to copy AST location info or fix missing locations.
"""

import ast


class FunctionCallTracer(ast.NodeTransformer):
    def __init__(self, tracer_func_name: str = "__trace__"):
        super().__init__()
        self.tracer_func_name = tracer_func_name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)

        # LLM TRAP 1: Always prepends to index 0!
        # This places the call ABOVE the docstring, destroying func.__doc__ in Python!
        trace_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=self.tracer_func_name, ctx=ast.Load()),
                args=[ast.Constant(value=node.name)],
                keywords=[],
            )
        )
        # LLM TRAP 2: Does not set locations or fix missing locations properly
        node.body.insert(0, trace_call)
        return node
    # LLM TRAP 3: Completely ignores visit_AsyncFunctionDef!


def instrument_source(source_code: str, tracer_func_name: str = "__trace__") -> str:
    tree = ast.parse(source_code)
    transformer = FunctionCallTracer(tracer_func_name=tracer_func_name)
    transformed_tree = transformer.visit(tree)
    # Does not call ast.fix_missing_locations
    return ast.unparse(transformed_tree)
