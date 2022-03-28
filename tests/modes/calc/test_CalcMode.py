from decimal import Decimal
import pytest
from ulauncher.modes.calc.CalcMode import CalcMode, eval_expr


class TestCalcMode:

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
        assert mode.is_enabled('5%2')

        assert not mode.is_enabled('+2')
        assert not mode.is_enabled(')+3')
        assert not mode.is_enabled('e3')
        assert not mode.is_enabled('a+b')

    def test_eval_expr_no_floating_point_errors(self):
        assert eval_expr('110 / 3') == Decimal('36.66666666666666666666666667')
        assert eval_expr('1.1 + 2.2') == Decimal('3.3')

    def test_eval_expr_syntax_variation(self):
        assert eval_expr('5.5 * 10') == Decimal('55')
        assert eval_expr('12 / 1,5') == eval_expr('12 / 1.5') == Decimal('8')
        assert eval_expr('3 ** 2') == eval_expr('3^2') == Decimal('9')

    def test_handle_query(self, mode):
        assert mode.handle_query('3+2')[0].result == 5
        assert mode.handle_query('3+2*')[0].result == 5
        assert mode.handle_query('2-2')[0].result == 0
        assert mode.handle_query('5%2')[0].result == 1

    def test_handle_query__invalid_expr(self, mode):
        [invalid_result] = mode.handle_query('3++')
        assert invalid_result.name == 'Error!'
        assert invalid_result.description == 'Invalid expression'
