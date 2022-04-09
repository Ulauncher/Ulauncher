import re
import ast
import math
from decimal import Decimal
import operator as op
from functools import lru_cache

from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.calc.CalcResult import CalcResult


# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg, ast.Mod: op.mod}

functions = {"sqrt": Decimal.sqrt, "exp": Decimal.exp,
             "ln": Decimal.ln, "log10": Decimal.log10,
             "sin": math.sin, "cos": math.cos, "tan": math.tan,
             "asin": math.asin, "acos": math.acos, "atan": math.atan,
             "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
             "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
             "erf": math.erf, "erfc": math.erfc, "gamma": math.gamma,
             "lgamma": math.lgamma}

regex = r'^(?:[\d\*+\/\%\-\.,e\(\)\^ ]|' + "|".join(functions.keys()) + r')+$'

# Show a friendlier output for incomplete queries, instead of "Invalid"
def normalize_expr(expr):
    # Dot is the Python notation for decimals
    expr = expr.replace(",", ".")
    # ^ means xor in Python. ** is the Python notation for pow
    expr = expr.replace("^", "**")
    # Strip trailing operator
    expr = re.sub(r"\s*[\.\+\-\*/%\(]\*?\s*$", "", expr)
    # Complete unfinished brackets
    expr = expr + ")" * (expr.count("(") - expr.count(")"))
    return expr


@lru_cache(maxsize=1000)
def eval_expr(expr):
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
    tree = ast.parse(expr, mode='eval').body
    result = _eval(tree).quantize(Decimal("1e-15"))
    int_result = int(result)
    if result == int_result:
        return int_result
    return result.normalize()  # Strip trailing zeros from decimal


def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return Decimal(str(node.n))
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call): # <func>(<args>)
        if node.func.id in functions:
            value = functions[node.func.id](_eval(node.args[0]))
            if isinstance(value, float):
                value = Decimal(value)
            return value

    raise TypeError(node)


class CalcMode(BaseMode):
    RE_CALC = re.compile(regex, flags=re.IGNORECASE)

    def is_enabled(self, query):
        return bool(re.match(self.RE_CALC, query))

    def handle_query(self, query):
        try:
            result = eval_expr(query)
            if result is None:
                raise ValueError()

            result = CalcResult(result=result)
        # pylint: disable=broad-except
        except Exception:
            result = CalcResult(error='Invalid expression')
        return [result]
