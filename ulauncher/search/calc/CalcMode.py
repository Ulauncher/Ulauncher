import re
import math
import ast
import operator as op

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.calc.CalcResultItem import CalcResultItem

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

functions = {
    'sin': math.sin,
    'cos' : math.cos,
    'tan' : math.tan,
    'asin': math.asin,
    'acos' : math.acos,
    'atan' : math.atan,
    'cot' : lambda a : 1/math.tan(a),
    'sec' : lambda a : 1/math.cos(a),
    'cosec' : lambda a : 1/math.sin(a),
    'log' : math.log,
    'log10' : math.log10,
    'r' : lambda a : a*math.pi/180
}

constants = {
    'pi' : math.pi,
    'e' : math.e
}

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
    except SyntaxError:
        # if failed, try without the last symbol
        try:
            return _eval(ast.parse(expr[:-1], mode='eval').body)
        except SyntaxError:
            raise ValueError()

def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))
    elif isinstance(node, ast.Name):
        return constants[node.id]
    elif isinstance(node, ast.Call):
        if len(node.args) != 1:
            raise TypeError(node)
        return functions[node.func.id](_eval(node.args[0]))
    else:
        raise TypeError(node)

class CalcMode(BaseSearchMode):
    RE_CALC = re.compile(r'^[\d\-\(\.][\d\*+\/\-\.e\(\)\^ ]*$', flags=re.IGNORECASE)

    def is_enabled(self, query):
        try:
            res = eval_expr(query)
        except ArithmeticError:
            return True
        except Exception as e:
            return False
        return True

    def handle_query(self, query):
        error_msg = 'Invalid expression'
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
