import pytest
from ulauncher.search.calc.CalcMode import CalcMode, _number_value, eval_expr, normalize_expr


class TestCalcMode:

    @pytest.fixture
    def RenderResultListAction(self, mocker):
        return mocker.patch('ulauncher.search.calc.CalcMode.RenderResultListAction')

    @pytest.fixture
    def CalcResultItem(self, mocker):
        return mocker.patch('ulauncher.search.calc.CalcMode.CalcResultItem')

    @pytest.fixture
    def mode(self):
        return CalcMode()

    def test_is_enabled(self, mode):
        assert mode.is_enabled('5')
        assert mode.is_enabled('-5')
        assert mode.is_enabled('5+')
        assert mode.is_enabled('(5/0')
        assert mode.is_enabled('0.5/0')
        assert mode.is_enabled('0.5e3+ (11**3+-2^3)')

        assert not mode.is_enabled('+2')
        assert not mode.is_enabled(')+3')
        assert not mode.is_enabled('e3')
        assert not mode.is_enabled('a+b')

        # the old regex claimed these, and then had to show "Invalid expression" for them
        assert not mode.is_enabled('5e')
        assert not mode.is_enabled('1 2 3')
        assert not mode.is_enabled('3--')
        assert not mode.is_enabled('True')

    def test_normalize_expr(self):
        assert normalize_expr('2*6+') == '2*6'
        assert normalize_expr('5**') == '5'
        assert normalize_expr('5.') == '5'
        assert normalize_expr('12 / 1,5') == '12 / 1.5'
        assert normalize_expr('3^2') == '3**2'
        assert normalize_expr('((1+2') == '((1+2))'
        assert normalize_expr('5*sqrt(') == '5'
        assert normalize_expr('sqrt(2') == 'sqrt(2)'

    def test_is_enabled__functions_and_constants(self, mode):
        assert mode.is_enabled('sqrt(9)')
        assert mode.is_enabled('2*pi')
        assert mode.is_enabled('ln(e)')
        assert mode.is_enabled('5*sqrt(')

        # a name on its own is a word, not a question
        assert not mode.is_enabled('pi')
        assert not mode.is_enabled('sqrt')
        # an unknown name is not math, even next to numbers
        assert not mode.is_enabled('5*foo(')

    def test_eval_expr_functions_and_constants(self):
        assert eval_expr('sqrt(9)') == '3'
        assert eval_expr('log10(1000)') == '3'
        assert eval_expr('sin(0)') == '0'
        assert eval_expr('2^10+sqrt(4)') == '1026'

    def test_number_value_reads_the_pre_3_8_number_node(self):
        # python 3.7 and older parse a number into ast.Num, which has no value attribute.
        # that node type is gone in 3.14, so it can only be stood in for here
        class Num:
            def __init__(self, n):
                self.n = n

        assert _number_value(Num(5)) == 5
        assert _number_value(Num(0.5)) == 0.5
        assert _number_value(Num(True)) is None
        assert _number_value(Num('5')) is None

    def test_eval_expr_no_floating_point_errors(self):
        assert eval_expr('1.1 + 2.2') == '3.3'
        assert eval_expr('0.1 + 0.2') == '0.3'

    def test_eval_expr_hides_the_noise_digits_of_a_division(self):
        assert eval_expr('110 / 3') == '36.666666666666667'
        assert eval_expr('1 / 3') == '0.333333333333333'

    def test_eval_expr_keeps_a_number_too_large_to_round(self):
        # rounding these to 15 decimals needs more significant digits than Decimal keeps
        assert eval_expr('2^50') == '1125899906842624'
        assert eval_expr('10^30') == '1' + '0' * 30
        assert eval_expr('10000000000000.5') == '10000000000000.5'
        assert eval_expr('123456789012345.6789') == '123456789012345.67'

    def test_eval_expr_rounds_before_checking_for_an_integer(self):
        # exp(ln(x)) lands just short of x, and only rounding makes it integral
        assert eval_expr('exp(ln(100))') == '100'
        assert eval_expr('exp(ln(1000000))') == '1000000'

    def test_eval_expr_rejects_results_with_too_many_digits(self):
        assert eval_expr('10^1000') == '1' + '0' * 1000
        with pytest.raises(OverflowError):
            eval_expr('2^1000000')

    def test_eval_expr_syntax_variation(self):
        assert eval_expr('5.5 * 10') == '55'
        assert eval_expr('12 / 1,5') == eval_expr('12 / 1.5') == '8'
        assert eval_expr('3 ** 2') == eval_expr('3^2') == '9'
        assert eval_expr('7 % 3') == '1'

    def test_handle_query(self, mode, RenderResultListAction, CalcResultItem):
        assert mode.handle_query('3+2') == RenderResultListAction.return_value
        assert mode.handle_query('3+2*') == RenderResultListAction.return_value
        RenderResultListAction.assert_called_with([CalcResultItem.return_value])
        CalcResultItem.assert_called_with(result='5')

    def test_handle_query__unfinished_bracket(self, mode, RenderResultListAction, CalcResultItem):
        assert mode.handle_query('(3+2') == RenderResultListAction.return_value
        CalcResultItem.assert_called_with(result='5')

    def test_handle_query__invalid_expr(self, mode, RenderResultListAction, CalcResultItem):
        assert mode.handle_query('3++') == RenderResultListAction.return_value
        RenderResultListAction.assert_called_with([CalcResultItem.return_value])
        CalcResultItem.assert_called_with(error='Invalid expression')

    def test_handle_query__result_is_0__returns_0(self, mode, CalcResultItem):
        mode.handle_query('2-2')
        CalcResultItem.assert_called_with(result='0')
