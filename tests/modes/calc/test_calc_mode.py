from decimal import Decimal

import pytest

from ulauncher.modes.calc.calc_mode import CalcMode, eval_expr


class TestCalcMode:
    @pytest.fixture
    def mode(self):
        return CalcMode()

    def test_is_enabled(self, mode):
        assert mode.parse_query_str("5")
        assert mode.parse_query_str("-5")
        assert mode.parse_query_str("5+")
        assert mode.parse_query_str("(5/0")
        assert mode.parse_query_str("0.5/0")
        assert mode.parse_query_str("0.5e3+ (11**3+-2^3)")
        assert mode.parse_query_str("5%2")
        assert mode.parse_query_str("sqrt(2)")
        assert mode.parse_query_str("1+sin(pi/2)")
        assert mode.parse_query_str("pi * 2")
        assert mode.parse_query_str("sqrt()+1")

        assert not mode.parse_query_str("a+b")
        assert not mode.parse_query_str("Add/Remove")
        assert not mode.parse_query_str("+2")
        assert not mode.parse_query_str(")+3")
        assert not mode.parse_query_str("asdf()")
        assert not mode.parse_query_str("pi")
        assert not mode.parse_query_str("e")
        assert not mode.parse_query_str("exp")
        assert not mode.parse_query_str("cos")
        assert not mode.parse_query_str("tan")
        assert not mode.parse_query_str("pi e")
        assert not mode.parse_query_str("pie")
        assert not mode.parse_query_str("pi2")
        assert not mode.parse_query_str("cospitanagamma")

    def test_eval_expr_no_floating_point_errors(self):
        assert eval_expr("110 / 3") == "36.666666666666667"
        assert eval_expr("1.1 + 2.2") == "3.3"
        assert eval_expr("sin(pi)") == "0"
        assert abs(Decimal(eval_expr("e**2")) - Decimal(eval_expr("exp(2)"))) < Decimal("1e-10")

    def test_eval_expr_rounding(self):
        assert str(eval_expr("3.300 + 7.1")) == "10.4"
        assert str(eval_expr("5.5 + 3.50")) == "9"
        assert str(eval_expr("10 / 3.0")) == "3.333333333333333"

    def test_eval_expr_syntax_variation(self):
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

    def test_handle_query(self, mode):
        assert mode.handle_query("3+2")[0].result == "5"
        assert mode.handle_query("3+2*")[0].result == "5"
        assert mode.handle_query("2-2")[0].result == "0"
        assert mode.handle_query("5%2")[0].result == "1"

    def test_handle_query__invalid_expr(self, mode):
        [invalid_result] = mode.handle_query("3++")
        assert invalid_result.name == "Error!"
        assert invalid_result.description == "Invalid expression"
        assert mode.handle_query("6 2")[0].name == "Error!"
        assert mode.handle_query("()*2")[0].name == "Error!"
        assert mode.handle_query("a+b")[0].name == "Error!"
        assert mode.handle_query("sqrt()+1")[0].name == "Error!"
        assert mode.handle_query("2pi")[0].name == "Error!"
