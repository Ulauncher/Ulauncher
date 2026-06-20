from __future__ import annotations

import ast
import logging
import math
import operator as op
import re
from decimal import Decimal
from typing import Callable

from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.calc.calc_result import CalcErrorResult, CalcResult
from ulauncher.modes.mode import Mode
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.lru_cache import lru_cache

_events = EventBus()

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
logger = logging.getLogger(__name__)


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
    return _eval_normalized(normalize_expr(expr))


@lru_cache(maxsize=1000)
def _eval_normalized(expr: str) -> str:
    tree = ast.parse(expr, mode="eval").body
    result = Decimal(_eval(tree)).quantize(Decimal("1e-15"))
    int_result = int(result)
    if result == int_result:
        return str(int_result)
    return str(result.normalize())  # normalize strips trailing zeros from decimal


def _is_math_operand(node: ast.expr) -> bool:
    # ensure every leaf is a number, or a known constant or function call, but don't validate the operator type,
    # because invalid math expressions should still count as expressions so we can show an error message
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    if isinstance(node, ast.BinOp):
        return _is_math_operand(node.left) and _is_math_operand(node.right)
    if isinstance(node, ast.UnaryOp):
        return _is_math_operand(node.operand)
    if isinstance(node, ast.Name):
        return node.id in constants
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id in functions and all(map(_is_math_operand, node.args))
    return False


@lru_cache(maxsize=1000)
def _is_enabled(query_str: str) -> bool:
    try:
        node = ast.parse(query_str, mode="eval").body
        # A lone constant name (e.g. "pi") is a word, not a query worth answering, so unlike a nested operand it
        # only counts as math inside an operator, call, or unary minus.
        if isinstance(node, ast.Constant):
            return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
        if isinstance(node, ast.BinOp):
            return _is_math_operand(node)
        if isinstance(node, ast.UnaryOp):
            return isinstance(node.op, ast.USub) and _is_math_operand(node.operand)
        if isinstance(node, ast.Call):
            return _is_math_operand(node)
    except SyntaxError:
        pass
    except (ValueError, TypeError, AttributeError, RecursionError, MemoryError) as e:
        logger.warning("Calc mode parse error for query: '%s', (%s)", query_str, e)
    return False


def _eval(node: ast.expr) -> int | float | Decimal:
    if isinstance(node, ast.Constant):  # <constant> (number)
        # older versions of python has .n instead of .value
        value = node.value if hasattr(node, "value") else node.n  # pyrefly: ignore[deprecated]
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


class CalcMode(Mode):
    def matches_query_str(self, query_str: str) -> bool:
        return _is_enabled(normalize_expr(query_str))

    def handle_query(self, query: Query, callback: Callable[[effects.EffectMessage], None]) -> None:
        try:
            calc_result = eval_expr(query.argument or "")
            result: Result = CalcResult(
                name=f"{Decimal(calc_result):n}",
                description="Enter to copy to the clipboard",
                result=calc_result,
            )
        except (SyntaxError, TypeError, IndexError):
            logger.warning("Calc mode error triggered while handling query: '%s'", query.argument)
            result = CalcErrorResult()

        callback(effects.render_results([result]))

    def activate_result(
        self,
        action_id: str,
        result: Result,
        _query: Query,
        callback: Callable[[effects.EffectMessage], None],
    ) -> None:
        if action_id == "copy":
            if not isinstance(result, CalcResult):
                logger.error("Unexpected result type for calc copy action: %s", type(result).__name__)
                callback(effects.do_nothing())
                return
            _events.emit("app:copy_and_close", result.result)
            callback(effects.close_window())
        else:
            logger.error("Unexpected action '%s' for Calc mode result '%s'", action_id, result)
            callback(effects.do_nothing())
