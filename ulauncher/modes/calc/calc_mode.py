from __future__ import annotations

import ast
import logging
import math
import operator as op
import re
from decimal import Decimal
from functools import lru_cache

from ulauncher.internals.query import Query
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.calc.calc_result import CalcResult

# supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg,
    ast.Mod: op.mod,
}

functions = {
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
    result = _eval(tree).quantize(Decimal("1e-15"))
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


def _eval(node: ast.expr) -> Decimal:
    if isinstance(node, ast.Constant):  # <constant> (number)
        return Decimal(str(node.n))
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))  # type: ignore[no-any-return, operator]
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))  # type: ignore[no-any-return, operator]
    if isinstance(node, ast.Name) and node.id in constants:  # <name>
        return constants[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:  # <func>(<args>)
        value = Decimal(functions[node.func.id](_eval(node.args[0])))  # type: ignore[operator]
        if isinstance(value, float):
            value = Decimal(value)
        return value

    raise TypeError(node)


class CalcMode(BaseMode):
    def parse_query_str(self, query_str: str) -> Query | None:
        return Query(None, query_str) if _is_enabled(query_str) else None

    def handle_query(self, query: Query) -> list[CalcResult]:
        try:
            result = CalcResult(result=str(eval_expr(query.argument)))
        except (SyntaxError, TypeError, IndexError):
            result = CalcResult(error="Invalid expression")
        return [result]
