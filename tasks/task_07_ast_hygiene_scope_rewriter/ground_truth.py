"""Ground Truth Reference Implementation for Task 07: AST Function Instrumentation."""

import ast
from typing import Union


class FunctionCallTracer(ast.NodeTransformer):
    def __init__(self, tracer_func_name: str = "__trace__"):
        super().__init__()
        self.tracer_func_name = tracer_func_name

    def _instrument_func(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        self.generic_visit(node)

        # Build tracer call node: __trace__("func_name")
        trace_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=self.tracer_func_name, ctx=ast.Load()),
                args=[ast.Constant(value=node.name)],
                keywords=[],
            )
        )
        # Copy location metadata from function definition
        ast.copy_location(trace_call, node)
        ast.copy_location(trace_call.value, node)

        # Check if first statement is a docstring
        insert_idx = 0
        if node.body and isinstance(node.body[0], ast.Expr):
            val = node.body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                # First statement is docstring! Insert tracer AFTER docstring
                insert_idx = 1

        node.body.insert(insert_idx, trace_call)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self._instrument_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return self._instrument_func(node)


def instrument_source(source_code: str, tracer_func_name: str = "__trace__") -> str:
    tree = ast.parse(source_code)
    transformer = FunctionCallTracer(tracer_func_name=tracer_func_name)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return ast.unparse(transformed_tree)
