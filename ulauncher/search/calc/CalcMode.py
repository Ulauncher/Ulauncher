import re
import ast
import operator as op
from gi.repository import Gdk

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from .CalcResultItem import CalcResultItem


# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('2*6+')
    12
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    try:
        return _eval(ast.parse(expr, mode='eval').body)
    except Exception:
        # if failed, try without the last symbol
        return _eval(ast.parse(expr[:-1], mode='eval').body)


def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))
    else:
        raise TypeError(node)


class CalcMode(BaseSearchMode):
    RE_CALC = re.compile(r'^[\d\-\(\.][\d\*+\/\-\.e\(\)\^ ]*$', flags=re.IGNORECASE)

    def is_enabled(self, query):
        return re.match(self.RE_CALC, query)

    def handle_query(self, query):
        error_msg = 'Invalid expression'
        try:
            result = eval_expr(query)
            if result is None:
                raise ValueError(error_msg)

            # fixes issue with division where result is represented as a float (e.g., 1.0)
            # although it is an integer (1)
            if int(result) == result:
                result = int(result)

            result_item = CalcResultItem(result=result)
        except Exception as e:
            result_item = CalcResultItem(error=e.message or error_msg)
        return RenderResultListAction([result_item])
