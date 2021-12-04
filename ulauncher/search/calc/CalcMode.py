import re
import ast
from decimal import Decimal
import operator as op

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.calc.CalcResultItem import CalcResultItem


# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


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
    expr = expr.replace("^", "**")
    try:
        return _eval(ast.parse(expr, mode='eval').body)
    # pylint: disable=broad-except
    except Exception:
        # if failed, try without the last symbol
        return _eval(ast.parse(expr[:-1], mode='eval').body)


def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return Decimal(str(node.n))
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))

    raise TypeError(node)


class CalcMode(BaseSearchMode):
    RE_CALC = re.compile(r'^[\d\-\(\.][\d\*+\/\-\.e\(\)\^ ]*$', flags=re.IGNORECASE)

    def is_enabled(self, query):
        return re.match(self.RE_CALC, query)

    def handle_query(self, query):
        try:
            result = eval_expr(query)
            if result is None:
                raise ValueError()

            # fixes issue with division where result is represented as a float (e.g., 1.0)
            # although it is an integer (1)
            if int(result) == result:
                result = int(result)

            result_item = CalcResultItem(result=result)
        # pylint: disable=broad-except
        except Exception:
            result_item = CalcResultItem(error='Invalid expression')
        return RenderResultListAction([result_item])
