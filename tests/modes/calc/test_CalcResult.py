import pytest
from ulauncher.modes.calc.CalcResult import CalcResult


class TestCalcResult:
    @pytest.fixture
    def DoNothingAction(self, mocker):
        return mocker.patch("ulauncher.modes.calc.CalcResult.DoNothingAction")

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

    def test_on_enter(self, CopyToClipboardAction):
        item = CalcResult(52)
        assert item.on_enter("q") == CopyToClipboardAction.return_value
        CopyToClipboardAction.assert_called_with("52")

    def test_on_enter__error__DoNothingAction_returned(self, DoNothingAction, CopyToClipboardAction):
        item = CalcResult(error="message")
        assert item.on_enter("q") == DoNothingAction.return_value
        DoNothingAction.assert_called_with()
        assert not CopyToClipboardAction.called
