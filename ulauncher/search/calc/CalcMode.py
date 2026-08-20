import re
import ast
import contextlib
import logging
import math
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import operator as op

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.calc.CalcCompletionResultItem import CalcCompletionResultItem
from ulauncher.search.calc.CalcResultItem import CalcResultItem

logger = logging.getLogger(__name__)


# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg, ast.Mod: op.mod}

functions = {
    'sqrt': Decimal.sqrt,
    'exp': Decimal.exp,
    'ln': Decimal.ln,
    'log10': Decimal.log10,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'asinh': math.asinh,
    'acosh': math.acosh,
    'atanh': math.atanh,
    'erf': math.erf,
    'erfc': math.erfc,
    'gamma': math.gamma,
    'lgamma': math.lgamma,
}

constants = {'pi': Decimal(math.pi), 'e': Decimal(math.e)}

descriptions = {
    'sqrt': 'Square root',
    'exp': 'Exponential (e to the power of x)',
    'ln': 'Natural logarithm',
    'log10': 'Base-10 logarithm',
    'sin': 'Sine (radians)',
    'cos': 'Cosine (radians)',
    'tan': 'Tangent (radians)',
    'asin': 'Arc sine (radians)',
    'acos': 'Arc cosine (radians)',
    'atan': 'Arc tangent (radians)',
    'sinh': 'Hyperbolic sine',
    'cosh': 'Hyperbolic cosine',
    'tanh': 'Hyperbolic tangent',
    'asinh': 'Inverse hyperbolic sine',
    'acosh': 'Inverse hyperbolic cosine',
    'atanh': 'Inverse hyperbolic tangent',
    'erf': 'Error function',
    'erfc': 'Complementary error function',
    'gamma': 'Gamma function',
    'lgamma': 'Natural logarithm of the gamma function',
    'pi': 'Pi (3.14159...)',
    'e': "Euler's number (2.71828...)",
}

_max_result_exponent = 1000

_trailing_operator_re = re.compile(r'\s*[.+\-*/%]\*?\s*$')
# only known function names, so that an app search like "5*foo(" isn't reduced to the math prefix "5"
_incomplete_call_re = re.compile(
    r'\s*[.+\-*/%]?\*?\s*(?:(?<![\w.])(?:' + '|'.join(functions) + r'))?\(\s*$')
# a name can only be completed where an operand can start, so it must follow an operator or a bracket
_partial_name_re = re.compile(r'^(?P<head>.*[-+*/%^(]\s*)(?P<partial>[a-zA-Z_]\w*)$')


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
    # strip calls that have no argument yet, so that "5*sqrt(" evaluates as "5"
    stripped = _incomplete_call_re.sub('', expr)
    while stripped != expr:
        expr = stripped
        stripped = _incomplete_call_re.sub('', expr)
    # complete unfinished brackets
    return expr + ')' * (expr.count('(') - expr.count(')'))


@lru_cache(maxsize=1000)
def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    '64'
    >>> eval_expr('2*6+')
    '12'
    >>> eval_expr('110/3')
    '36.666666666666667'
    """
    result = Decimal(_eval(ast.parse(normalize_expr(expr), mode='eval').body))
    # check the exponent before int() has to materialize every digit, which takes seconds
    if result.adjusted() > _max_result_exponent:
        raise OverflowError('Result has too many digits to display: 1e%s' % result.adjusted())
    # the last digits of a division are noise, and Decimal keeps 28 of them. It raises instead
    # of rounding when too few are left for 15 decimals, and then there is no noise to cut
    with contextlib.suppress(InvalidOperation):
        result = result.quantize(Decimal('1e-15'))
    # must follow the rounding, which is what makes 99.99999999999999999999999996 integral
    int_result = int(result)
    if result == int_result:
        return str(int_result)
    # normalize strips the trailing zeros that quantize added
    return str(result.normalize())


def _matches_name(partial, name):
    # anchoring on the first character keeps "5*a" from listing every name containing an "a"
    if not name.startswith(partial[0]):
        return False
    remaining = iter(name)
    return all(char in remaining for char in partial)


@lru_cache(maxsize=1000)
def get_completions(query):
    """
    A query ending in a partial name, like "5*sq", completes to a full query like "5*sqrt(".
    The partial name matches as a subsequence, so "5*st" also completes to "5*sqrt(".
    Returns pairs of the function or constant name and the completed query.
    """
    query = query.rstrip()
    match = _partial_name_re.match(query)
    if not match:
        return ()
    head, partial = match.group('head'), match.group('partial')
    # substituting a number for the partial name tells us whether the rest is math
    if not _is_enabled(normalize_expr(head + '1')):
        return ()
    names = sorted((name for name in list(functions) + list(constants) if _matches_name(partial, name)),
                   key=lambda name: (not name.startswith(partial), name))
    completions = ((name, head + name + '(' if name in functions else head + name) for name in names)
    return tuple((name, completion) for name, completion in completions if completion != query)


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
    Ensures every leaf is a number, a known constant or a known function call, but doesn't
    validate the operator type, because an invalid expression should still count as one,
    so we can show an error message for it
    """
    if _number_value(node) is not None:
        return True
    if isinstance(node, ast.BinOp):
        return _is_math_operand(node.left) and _is_math_operand(node.right)
    if isinstance(node, ast.UnaryOp):
        return _is_math_operand(node.operand)
    if isinstance(node, ast.Name):
        return node.id in constants
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id in functions and all(
            _is_math_operand(arg) for arg in node.args)
    return False


@lru_cache(maxsize=1000)
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
        if isinstance(node, ast.Call):
            return _is_math_operand(node)
        # a constant name on its own, like "pi", is a word rather than a question, so unlike
        # a nested operand it only counts as math inside an operator, a call or a unary minus
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
        operator = operators.get(type(node.op))
        if not operator:
            raise TypeError('Unsupported operator: %s' % node.op)
        return operator(_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        operator = operators.get(type(node.op))
        if not operator:
            raise TypeError('Unsupported operator: %s' % node.op)
        return operator(_eval(node.operand))
    if isinstance(node, ast.Name) and node.id in constants:  # <name>
        return constants[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:
        return Decimal(functions[node.func.id](_eval(node.args[0])))

    raise TypeError(node)


def _evaluate(expr):
    try:
        return CalcResultItem(result=eval_expr(expr))
    # ArithmeticError covers the decimal errors (dividing by zero, the square root of a
    # negative number), ValueError the domain errors of the math module
    except (SyntaxError, TypeError, IndexError, ArithmeticError, ValueError) as e:
        # half-written and impossible expressions are both normal while typing, so this is
        # only worth a debug line, and only worth one that says what went wrong
        logger.debug('Calc mode cannot evaluate "%s": %s', expr, e)
        return CalcResultItem(error='Invalid expression')


class CalcMode(BaseSearchMode):

    def is_enabled(self, query):
        return bool(get_completions(query)) or _is_enabled(normalize_expr(query))

    def handle_query(self, query):
        completions = get_completions(query)
        result_items = []
        # a half-written name has no value to show, but a complete one like "5*e" has both
        if not completions or _is_enabled(normalize_expr(query)):
            result_items.append(_evaluate(query))
        result_items.extend(CalcCompletionResultItem(completion=completion, description=descriptions[name])
                            for name, completion in completions)
        return RenderResultListAction(result_items)
