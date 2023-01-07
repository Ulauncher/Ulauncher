from decimal import Decimal
import pytest
from ulauncher.modes.calc.CalcMode import CalcMode, eval_expr


class TestCalcMode:
    @pytest.fixture
    def mode(self):
        return CalcMode()

    def test_is_enabled(self, mode):
        assert mode.is_enabled("5")
        assert mode.is_enabled("-5")
        assert mode.is_enabled("5+")
        assert mode.is_enabled("(5/0")
        assert mode.is_enabled("0.5/0")
        assert mode.is_enabled("0.5e3+ (11**3+-2^3)")
        assert mode.is_enabled("5%2")
        assert mode.is_enabled("sqrt(2)")
        assert mode.is_enabled("1+sin(pi/2)")
        assert mode.is_enabled("pi * 2")
        assert mode.is_enabled("sqrt()+1")

        assert not mode.is_enabled("a+b")
        assert not mode.is_enabled("Add/Remove")
        assert not mode.is_enabled("+2")
        assert not mode.is_enabled(")+3")
        assert not mode.is_enabled("asdf()")
        assert not mode.is_enabled("pi")
        assert not mode.is_enabled("e")
        assert not mode.is_enabled("exp")
        assert not mode.is_enabled("cos")
        assert not mode.is_enabled("tan")
        assert not mode.is_enabled("pi e")
        assert not mode.is_enabled("pie")
        assert not mode.is_enabled("pi2")
        assert not mode.is_enabled("cospitanagamma")

    def test_eval_expr_no_floating_point_errors(self):
        assert eval_expr("110 / 3") == Decimal("36.666666666666667")
        assert eval_expr("1.1 + 2.2") == Decimal("3.3")
        assert eval_expr("sin(pi)") == Decimal("0")
        assert abs(eval_expr("e**2") - eval_expr("exp(2)")) < Decimal("1e-10")

    def test_eval_expr_rounding(self):
        assert str(eval_expr("3.300 + 7.1")) == "10.4"
        assert str(eval_expr("5.5 + 3.50")) == "9"
        assert str(eval_expr("10 / 3.0")) == "3.333333333333333"

    def test_eval_expr_syntax_variation(self):
        assert eval_expr("5.5 * 10") == Decimal("55")
        assert eval_expr("12 / 1,5") == eval_expr("12 / 1.5") == Decimal("8")
        assert eval_expr("3 ** 2") == eval_expr("3^2") == Decimal("9")
        assert eval_expr("7+") == eval_expr("7 **") == eval_expr("(7") == Decimal("7")
        assert eval_expr("sqrt(2)**2") == Decimal("2")
        assert eval_expr("gamma(6)") == Decimal("120")
        assert eval_expr("lgamma(3)") == eval_expr("ln(gamma(3))") == Decimal("0.693147180559945")
        # Nonsense expressions probably. I justed wanted to cover all methods
        assert eval_expr("pi * 2 + exp(4)") == Decimal("60.881335340323825")
        assert eval_expr("log10(e) / cos(5)") == Decimal("1.531027060212625")
        assert eval_expr("cos(tanh(tan(2") == Decimal("0.561155145812412")
        assert eval_expr("atan(sin(erf(8") == Decimal("0.69952164434852")
        assert eval_expr("cosh(erfc(1.2))") == Decimal("1.004024487774208")
        assert eval_expr("asin(acosh(1.2))") == Decimal("0.671757384841459")
        assert eval_expr("sinh(acos(0.4") == Decimal("1.436961780213685")
        assert eval_expr("asinh(6) + atanh(0.9) + ln(0.7)") == Decimal("3.6073243982894")

    def test_handle_query(self, mode):
        assert mode.handle_query("3+2")[0].result == 5
        assert mode.handle_query("3+2*")[0].result == 5
        assert mode.handle_query("2-2")[0].result == 0
        assert mode.handle_query("5%2")[0].result == 1

    def test_handle_query__invalid_expr(self, mode):
        [invalid_result] = mode.handle_query("3++")
        assert invalid_result.name == "Error!"
        assert invalid_result.description == "Invalid expression"
        assert mode.handle_query("6 2")[0].name == "Error!"
        assert mode.handle_query("()*2")[0].name == "Error!"
        assert mode.handle_query("a+b")[0].name == "Error!"
        assert mode.handle_query("sqrt()+1")[0].name == "Error!"
        assert mode.handle_query("2pi")[0].name == "Error!"
