import pytest

from ulauncher.modes.calc.CalcResult import CalcResult


class TestCalcResult:
    @pytest.fixture
    def CopyToClipboardAction(self, mocker):
        return mocker.patch("ulauncher.modes.calc.CalcResult.CopyToClipboardAction")

    def test_get_name(self):
        assert CalcResult(52).name == "52"
        assert CalcResult("42").name == "42"
        assert CalcResult(error="message").name == "Error!"

    def test_get_description(self):
        assert CalcResult(52).description == "Enter to copy to the clipboard"
        assert CalcResult(error="message").get_description("q") == "message"

    def test_on_activation(self, CopyToClipboardAction):
        item = CalcResult(52)
        assert item.on_activation("q") == CopyToClipboardAction.return_value
        CopyToClipboardAction.assert_called_with("52")

    def test_on_activation__error__returns_true(self, CopyToClipboardAction):
        item = CalcResult(error="message")
        assert item.on_activation("q") is True
        assert not CopyToClipboardAction.called
