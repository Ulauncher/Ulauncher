from ulauncher.modes.calc.calc_result import CalcResult


class TestCalcResult:
    def test_get_name(self) -> None:
        assert CalcResult(result="52").name == "52"
        assert CalcResult("42").name == "42"
        assert CalcResult(error="message").name == "Error!"

    def test_get_description(self) -> None:
        assert CalcResult(result="52").description == "Enter to copy to the clipboard"
        assert CalcResult(error="message").description == "message"
