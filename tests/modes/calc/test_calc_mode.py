from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.effects import EffectType
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.calc.calc_mode import (
    CalcMode,
    constants,
    descriptions,
    eval_expr,
    functions,
    get_completions,
)
from ulauncher.modes.calc.calc_result import CalcCompletionResult, CalcErrorResult


def get_results(mode: CalcMode, query: Query) -> list[Result]:
    """Helper to collect results from callback-based handle_query."""
    results: list[Result] = []

    def collect(msg: object) -> None:
        if isinstance(msg, dict) and msg["type"] == EffectType.RENDER_RESULTS:
            results.extend(msg["results"])

    mode.handle_query(query, collect)
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
        assert not mode.matches_query_str("relative/path/to/file.ext")
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

    def test_is_enabled__partial_names(self, mode: CalcMode) -> None:
        assert mode.matches_query_str("5*s")
        assert mode.matches_query_str("5*sq")
        assert mode.matches_query_str("5*sqrt")
        assert mode.matches_query_str("5*sqrt(")
        assert mode.matches_query_str("5 * si")
        assert mode.matches_query_str("2*sqrt(3)+co")
        assert mode.matches_query_str("sqrt(s")
        assert mode.matches_query_str("(co")
        assert mode.matches_query_str("-s")
        assert mode.matches_query_str("5*st")
        assert mode.matches_query_str("5*ah")

        # Names can only follow an operator or bracket, so app names starting with a number are unaffected
        assert not mode.matches_query_str("0ad")
        assert not mode.matches_query_str("2fa")
        assert not mode.matches_query_str("10a")
        assert not mode.matches_query_str("2-player")
        assert not mode.matches_query_str("wifi-s")
        assert not mode.matches_query_str("5*zz")
        assert not mode.matches_query_str("5*sqx")
        assert not mode.matches_query_str("sq")

        # Only known functions are stripped, so an unknown call isn't reduced to its math prefix
        assert not mode.matches_query_str("5*foo(")
        assert not mode.matches_query_str("7-zip(")
        assert not mode.matches_query_str("5*mysin(")
        assert not mode.matches_query_str("co")

    def test_get_completions(self) -> None:
        assert get_completions("5*s") == (("sin", "5*sin("), ("sinh", "5*sinh("), ("sqrt", "5*sqrt("))
        assert get_completions("5 * sq") == (("sqrt", "5 * sqrt("),)
        assert get_completions("sqrt(2)+ta") == (("tan", "sqrt(2)+tan("), ("tanh", "sqrt(2)+tanh("))
        # Constants complete without a bracket
        assert get_completions("5*p") == (("pi", "5*pi"),)
        # A completion identical to the query is left out
        assert get_completions("5*pi") == ()
        assert get_completions("5*e") == (("erf", "5*erf("), ("erfc", "5*erfc("), ("exp", "5*exp("))
        assert get_completions("5*sqrt") == (("sqrt", "5*sqrt("),)
        assert get_completions("0ad") == ()
        assert get_completions("5*zz") == ()

    def test_get_completions__fuzzy(self) -> None:
        # The partial name matches as a subsequence
        assert get_completions("5*st") == (("sqrt", "5*sqrt("),)
        assert get_completions("5*ah") == (("acosh", "5*acosh("), ("asinh", "5*asinh("), ("atanh", "5*atanh("))
        # Prefix matches come before the rest
        assert get_completions("5*as") == (
            ("asin", "5*asin("),
            ("asinh", "5*asinh("),
            ("acos", "5*acos("),
            ("acosh", "5*acosh("),
        )
        # The first character still has to match, so unrelated app names are unaffected
        assert get_completions("5*qt") == ()

    def test_all_completions_have_descriptions(self) -> None:
        assert set(descriptions) == {*functions, *constants}

    def test_eval_expr_no_floating_point_errors(self) -> None:
        assert eval_expr("110 / 3") == "36.666666666666667"
        assert eval_expr("1.1 + 2.2") == "3.3"
        assert eval_expr("sin(pi)") == "0"
        assert abs(Decimal(eval_expr("e**2")) - Decimal(eval_expr("exp(2)"))) < Decimal("1e-10")

    def test_eval_expr_rounding(self) -> None:
        assert eval_expr("3.300 + 7.1") == "10.4"
        assert eval_expr("5.5 + 3.50") == "9"
        assert eval_expr("10 / 3.0") == "3.333333333333333"

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

    def test_handle_query__completions(self, mode: CalcMode) -> None:
        results = get_results(mode, Query(None, "5*s"))
        assert [result.name for result in results] == ["5*sin(", "5*sinh(", "5*sqrt("]
        assert results[2].description == "Square root"

        # A complete name evaluates, but still offers the longer names
        results = get_results(mode, Query(None, "5*e"))
        assert [result.name for result in results] == ["13.591409142295225", "5*erf(", "5*erfc(", "5*exp("]

    def test_handle_query__incomplete_call(self, mode: CalcMode) -> None:
        assert get_results(mode, Query(None, "5*sqrt("))[0].result == "5"
        assert get_results(mode, Query(None, "5*sqrt(2"))[0].result == "7.071067811865475"

    def test_handle_query__complete_called(self, mode: CalcMode, mocker: MockerFixture) -> None:
        query = Query(None, "5*sq")
        result = get_results(mode, query)[0]
        assert isinstance(result, CalcCompletionResult)
        callback = mocker.MagicMock()
        mode.activate_result("complete", result, query, callback)
        assert callback.call_args[0][0] == {"type": EffectType.SET_QUERY, "query": "5*sqrt("}

    def test_handle_query__copy_called(self, mode: CalcMode, event_emit: MagicMock, mocker: MockerFixture) -> None:
        query = Query(None, "3+2")
        result = get_results(mode, query)[0]
        assert result.result == "5"
        callback = mocker.MagicMock()
        mode.activate_result("copy", result, query, callback)
        event_emit.assert_called_once_with("app:copy_and_close", "5")
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

    def test_handle_query__unevaluable_expr(self, mode: CalcMode, caplog: pytest.LogCaptureFixture) -> None:
        bad_queries = [
            "1/0",
            "1%0",
            "2**100000",
            "sqrt(-1)",
            "ln(0)",
            "acos(2)",
            "gamma(-1)",
        ]

        with caplog.at_level("CRITICAL"):
            for query_str in bad_queries:
                result = get_results(mode, Query(None, query_str))[0]
                assert isinstance(result, CalcErrorResult)
