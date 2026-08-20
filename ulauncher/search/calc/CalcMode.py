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

_trailing_operator_re = re.compile(r'\s*[.+\-*/]\*?\s*$')


def normalize_expr(expr):
    """
    Makes a half-written expression evaluable, so that it shows a result
    while the user is still typing instead of an error
    """
    # dot is the Python notation for decimals
    expr = expr.replace(',', '.')
    # ^ means xor in Python, ** is the Python notation for pow
    expr = expr.replace('^', '**')
    expr = _trailing_operator_re.sub('', expr)
    # complete unfinished brackets
    return expr + ')' * (expr.count('(') - expr.count(')'))


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
    return _eval(ast.parse(normalize_expr(expr), mode='eval').body)


def _eval(node):
    # python 3.7 and older parse a number into ast.Num, which keeps it in .n instead of .value
    value = node.value if isinstance(node, ast.Constant) else getattr(node, 'n', None)
    if value is not None:  # <constant> (number)
        return Decimal(str(value))
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))

    raise TypeError(node)


class CalcMode(BaseSearchMode):
    RE_CALC = re.compile(r'^[\d\-\(\.,][\d\*+\/\-\.,e\(\)\^ ]*$', flags=re.IGNORECASE)

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
