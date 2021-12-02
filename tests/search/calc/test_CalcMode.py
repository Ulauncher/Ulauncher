import pytest
from ulauncher.modes.calc.CalcMode import CalcMode


class TestCalcMode:

    @pytest.fixture
    def RenderResultListAction(self, mocker):
        return mocker.patch('ulauncher.modes.calc.CalcMode.RenderResultListAction')

    @pytest.fixture
    def CalcResultItem(self, mocker):
        return mocker.patch('ulauncher.modes.calc.CalcMode.CalcResultItem')

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
