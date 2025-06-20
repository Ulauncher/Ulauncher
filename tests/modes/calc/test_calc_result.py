import pytest

from ulauncher.modes.calc.calc_result import CalcResult


class TestCalcResult:
    @pytest.fixture
    def copy_action(self, mocker):
        return mocker.patch("ulauncher.modes.calc.calc_result.actions.copy")

    def test_get_name(self) -> None:
        assert CalcResult(52).name == "52"
        assert CalcResult("42").name == "42"
        assert CalcResult(error="message").name == "Error!"

    def test_get_description(self) -> None:
        assert CalcResult(52).description == "Enter to copy to the clipboard"
        assert CalcResult(error="message").description == "message"

    def test_on_activation(self, copy_action) -> None:
        item = CalcResult(52)
        assert item.on_activation("q") == copy_action.return_value
        copy_action.assert_called_with("52")

    def test_on_activation__error__returns_true(self, copy_action) -> None:
        item = CalcResult(error="message")
        assert item.on_activation("q") is True
        assert not copy_action.called
