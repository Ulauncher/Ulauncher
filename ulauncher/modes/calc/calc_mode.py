from __future__ import annotations

import ast
import logging
import math
import operator as op
import re
from decimal import Decimal
from functools import lru_cache
from typing import Callable

from ulauncher.internals import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.calc.calc_result import CalcResult

# supported operators
operators: dict[type, Callable[..., int | float]] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg,
    ast.Mod: op.mod,
}

functions: dict[str, Callable[..., float | Decimal]] = {
    "sqrt": Decimal.sqrt,
    "exp": Decimal.exp,
    "ln": Decimal.ln,
    "log10": Decimal.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "asinh": math.asinh,
    "acosh": math.acosh,
    "atanh": math.atanh,
    "erf": math.erf,
    "erfc": math.erfc,
    "gamma": math.gamma,
    "lgamma": math.lgamma,
}

constants = {"pi": Decimal(math.pi), "e": Decimal(math.e)}
logger = logging.getLogger()


# Show a friendlier output for incomplete queries, instead of "Invalid"
def normalize_expr(expr: str) -> str:
    # Dot is the Python notation for decimals
    expr = expr.replace(",", ".")
    # ^ means xor in Python. ** is the Python notation for pow
    expr = expr.replace("^", "**")
    # Strip trailing operator
    expr = re.sub(r"\s*[\.\+\-\*/%\(]\*?\s*$", "", expr)
    # Complete unfinished brackets
    expr = expr + ")" * (expr.count("(") - expr.count(")"))
    return expr  # noqa: RET504


@lru_cache(maxsize=1000)
def eval_expr(expr: str) -> str:
    """
    >>> eval_expr('2^6')
    64
    >>> eval_expr('2**6')
    64
    >>> eval_expr('2*6+')
    12
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    expr = normalize_expr(expr)
    tree = ast.parse(expr, mode="eval").body
    result = Decimal(_eval(tree)).quantize(Decimal("1e-15"))
    int_result = int(result)
    if result == int_result:
        return str(int_result)
    return str(result.normalize())  # normalize strips trailing zeros from decimal


@lru_cache(maxsize=1000)
def _is_enabled(query_str: str) -> bool:
    query_str = normalize_expr(query_str)
    try:
        node = ast.parse(query_str, mode="eval").body
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, ast.BinOp):
            # Check that left and right are valid constants if they are strings
            if isinstance(node.left, ast.Name) and node.left.id not in constants:
                return False
            return not (isinstance(node.right, ast.Name) and node.right.id not in constants)
        if isinstance(node, ast.UnaryOp):
            # Allow for minus, but no other operators
            return isinstance(node.op, ast.USub)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id in functions
    except SyntaxError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.warning("Calc mode parse error for query: '%s', (%s)", query_str, e)
    return False


def _eval(node: ast.expr) -> int | float | Decimal:
    if isinstance(node, ast.Constant):  # <constant> (number)
        value = node.value if hasattr(node, "value") else node.n  # older versions of python has .n instead of .value
        return Decimal(str(value))
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        operator = operators.get(type(node.op))
        if not operator:
            msg = f"Unsupported operator: {node.op}"
            raise TypeError(msg)
        return operator(_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        operator = operators.get(type(node.op))
        if not operator:
            msg = f"Unsupported operator: {node.op}"
            raise TypeError(msg)
        return operator(_eval(node.operand))
    if isinstance(node, ast.Name) and node.id in constants:  # <name>
        return constants[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:  # <func>(<args>)
        func = functions.get(node.func.id)
        if func:
            value = Decimal(func(_eval(node.args[0])))
            if isinstance(value, float):
                value = Decimal(value)
            return value

    raise TypeError(node)


class CalcMode(BaseMode):
    def parse_query_str(self, query_str: str) -> Query | None:
        return Query(None, query_str) if _is_enabled(query_str) else None

    def handle_query(self, query: Query) -> list[CalcResult]:
        try:
            calc_result = str(eval_expr(query.argument))
            result = CalcResult(
                name=f"{Decimal(calc_result):n}",
                description="Enter to copy to the clipboard",
                result=calc_result,
            )
        except (SyntaxError, TypeError, IndexError):
            logger.warning("Calc mode error triggered while handling query: '%s'", query.argument)
            result = CalcResult(
                name="Error!",
                description="Invalid expression",
            )

        return [result]

    def activate_result(self, result: Result, _query: Query, _alt: bool) -> ActionMetadata:
        if isinstance(result, CalcResult) and result.result is not None:
            return actions.copy(result.result)
        logger.error("Unexpected result type for Calc mode '%s'", result)
        return True
