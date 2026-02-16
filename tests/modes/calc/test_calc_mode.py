from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.effects import EffectType
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.calc.calc_mode import CalcMode, eval_expr
from ulauncher.modes.calc.calc_result import CalcErrorResult


def get_results(mode: CalcMode, query: Query) -> list[Result]:
    """Helper to collect results from callback-based handle_query."""
    results = []
    mode.handle_query(query, results.extend)
    return results


class TestCalcMode:
    @pytest.fixture
    def mode(self) -> CalcMode:
        return CalcMode()

    @pytest.fixture
    def event_emit(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.modes.calc.calc_mode._events.emit")

    def test_is_enabled(self, mode: CalcMode) -> None:
        assert mode.matches_query_str("5")
        assert mode.matches_query_str("-5")
        assert mode.matches_query_str("5+")
        assert mode.matches_query_str("(5/0")
        assert mode.matches_query_str("0.5/0")
        assert mode.matches_query_str("0.5e3+ (11**3+-2^3)")
        assert mode.matches_query_str("5%2")
        assert mode.matches_query_str("sqrt(2)")
        assert mode.matches_query_str("1+sin(pi/2)")
        assert mode.matches_query_str("pi * 2")
        assert mode.matches_query_str("sqrt()+1")

        assert not mode.matches_query_str("a+b")
        assert not mode.matches_query_str("Add/Remove")
        assert not mode.matches_query_str("+2")
        assert not mode.matches_query_str(")+3")
        assert not mode.matches_query_str("asdf()")
        assert not mode.matches_query_str("pi")
        assert not mode.matches_query_str("e")
        assert not mode.matches_query_str("exp")
        assert not mode.matches_query_str("cos")
        assert not mode.matches_query_str("tan")
        assert not mode.matches_query_str("pi e")
        assert not mode.matches_query_str("pie")
        assert not mode.matches_query_str("pi2")
        assert not mode.matches_query_str("cospitanagamma")

    def test_eval_expr_no_floating_point_errors(self) -> None:
        assert eval_expr("110 / 3") == "36.666666666666667"
        assert eval_expr("1.1 + 2.2") == "3.3"
        assert eval_expr("sin(pi)") == "0"
        assert abs(Decimal(eval_expr("e**2")) - Decimal(eval_expr("exp(2)"))) < Decimal("1e-10")

    def test_eval_expr_rounding(self) -> None:
        assert str(eval_expr("3.300 + 7.1")) == "10.4"
        assert str(eval_expr("5.5 + 3.50")) == "9"
        assert str(eval_expr("10 / 3.0")) == "3.333333333333333"

    def test_eval_expr_syntax_variation(self) -> None:
        assert eval_expr("5.5 * 10") == "55"
        assert eval_expr("12 / 1,5") == eval_expr("12 / 1.5") == "8"
        assert eval_expr("3 ** 2") == eval_expr("3^2") == "9"
        assert eval_expr("7+") == eval_expr("7 **") == eval_expr("(7") == "7"
        assert eval_expr("sqrt(2)**2") == "2"
        assert eval_expr("gamma(6)") == "120"
        assert eval_expr("lgamma(3)") == eval_expr("ln(gamma(3))") == "0.693147180559945"
        # Nonsense expressions probably. I justed wanted to cover all methods
        assert eval_expr("pi * 2 + exp(4)") == "60.881335340323825"
        assert eval_expr("log10(e) / cos(5)") == "1.531027060212625"
        assert eval_expr("cos(tanh(tan(2") == "0.561155145812412"
        assert eval_expr("atan(sin(erf(8") == "0.69952164434852"
        assert eval_expr("cosh(erfc(1.2))") == "1.004024487774208"
        assert eval_expr("asin(acosh(1.2))") == "0.671757384841459"
        assert eval_expr("sinh(acos(0.4") == "1.436961780213685"
        assert eval_expr("asinh(6) + atanh(0.9) + ln(0.7)") == "3.6073243982894"

    def test_handle_query(self, mode: CalcMode) -> None:
        assert get_results(mode, Query(None, "3+2"))[0].result == "5"
        assert get_results(mode, Query(None, "3+2*"))[0].result == "5"
        assert get_results(mode, Query(None, "2-2"))[0].result == "0"
        assert get_results(mode, Query(None, "5%2"))[0].result == "1"

    def test_handle_query__copy_called(self, mode: CalcMode, event_emit: MagicMock, mocker: MockerFixture) -> None:
        query = Query(None, "3+2")
        result = get_results(mode, query)[0]
        assert result.result == "5"
        callback = mocker.MagicMock()
        mode.activate_result("copy", result, query, callback)
        event_emit.assert_called_once_with("app:clipboard_store", "5")
        callback.assert_called_once()
        # Verify callback was called with close_window effect
        assert callback.call_args[0][0]["type"] == EffectType.CLOSE_WINDOW

    def test_handle_query__invalid_expr(self, mode: CalcMode, caplog: pytest.LogCaptureFixture) -> None:
        bad_queries = [
            "3++",
            "6 2",
            "()*2",
            "a+b",
            "sqrt()+1",
            "2pi",
        ]

        # Suppress expected warning and error logs for this test
        with caplog.at_level("CRITICAL"):
            for query_str in bad_queries:
                query = Query(None, query_str)
                result = get_results(mode, query)[0]
                # CalcErrorResult have no actions, so they never reach activate_result
                assert isinstance(result, CalcErrorResult)
