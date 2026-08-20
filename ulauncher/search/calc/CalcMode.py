import re
import ast
import logging
from decimal import Decimal
import operator as op

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.calc.CalcResultItem import CalcResultItem

logger = logging.getLogger(__name__)


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


def _number_value(node):
    """
    Returns the number a constant node holds, or None if it holds anything else.
    Python 3.7 and older parse a number into ast.Num, which keeps it in .n instead of .value
    """
    value = node.value if isinstance(node, ast.Constant) else getattr(node, 'n', None)
    # bools are ints, but "True" is a word rather than a number
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _is_math_operand(node):
    """
    Ensures every leaf is a number, but doesn't validate the operator type, because an
    invalid expression should still count as one, so we can show an error message for it
    """
    if _number_value(node) is not None:
        return True
    if isinstance(node, ast.BinOp):
        return _is_math_operand(node.left) and _is_math_operand(node.right)
    if isinstance(node, ast.UnaryOp):
        return _is_math_operand(node.operand)
    return False


def _is_enabled(expr):
    try:
        node = ast.parse(expr, mode='eval').body
        if _number_value(node) is not None:
            return True
        if isinstance(node, ast.BinOp):
            return _is_math_operand(node)
        if isinstance(node, ast.UnaryOp):
            # a leading minus makes a negative number, a leading plus is more likely not math at all
            return isinstance(node.op, ast.USub) and _is_math_operand(node.operand)
    except SyntaxError:
        pass
    except (ValueError, TypeError, AttributeError, RecursionError, MemoryError) as e:
        logger.warning('Calc mode parse error for query: "%s", (%s)', expr, e)
    return False


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

    def is_enabled(self, query):
        return _is_enabled(normalize_expr(query))

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
