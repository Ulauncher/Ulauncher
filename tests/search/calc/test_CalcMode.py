from decimal import Decimal
import pytest
from ulauncher.search.calc.CalcMode import CalcMode, eval_expr


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

    def test_eval_expr_no_floating_point_errors(self):
        assert eval_expr('110 / 3') == Decimal('36.66666666666666666666666667')
        assert eval_expr('1.1 + 2.2') == Decimal('3.3')

    def test_eval_expr_syntax_variation(self):
        assert eval_expr('5.5 * 10') == Decimal('55')
        assert eval_expr('12 / 1,5') == eval_expr('12 / 1.5') == Decimal('8')
        assert eval_expr('3 ** 2') == eval_expr('3^2') == Decimal('9')

    def test_handle_query(self, mode, RenderResultListAction, CalcResultItem):
        assert mode.handle_query('3+2') == RenderResultListAction.return_value
        assert mode.handle_query('3+2*') == RenderResultListAction.return_value
        RenderResultListAction.assert_called_with([CalcResultItem.return_value])
        CalcResultItem.assert_called_with(result=5)

    def test_handle_query__invalid_expr(self, mode, RenderResultListAction, CalcResultItem):
        assert mode.handle_query('3++') == RenderResultListAction.return_value
        RenderResultListAction.assert_called_with([CalcResultItem.return_value])
        CalcResultItem.assert_called_with(error='Invalid expression')

    def test_handle_query__result_is_0__returns_0(self, mode, CalcResultItem):
        mode.handle_query('2-2')
        CalcResultItem.assert_called_with(result=0)
