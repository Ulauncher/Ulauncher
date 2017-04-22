import pytest
from ulauncher.search.calc.CalcResultItem import CalcResultItem


class TestCalcResultItem:

    @pytest.fixture
    def DoNothingAction(self, mocker):
        return mocker.patch('ulauncher.search.calc.CalcResultItem.DoNothingAction')

    @pytest.fixture
    def CopyToClipboardAction(self, mocker):
        return mocker.patch('ulauncher.search.calc.CalcResultItem.CopyToClipboardAction')

    def test_get_name(self):
        assert CalcResultItem(52).get_name() == '52'
        assert CalcResultItem('42').get_name() == '42'
        assert CalcResultItem(error='message').get_name() == 'Error!'

    def test_get_description(self):
        assert CalcResultItem(52).get_description('q') == 'Enter to copy to the clipboard'
        assert CalcResultItem(error='message').get_description('q') == 'message'

    def test_on_enter(self, CopyToClipboardAction):
        item = CalcResultItem(52)
        assert item.on_enter('q') == CopyToClipboardAction.return_value
        CopyToClipboardAction.assert_called_with('52')

    def test_on_enter__error__DoNothingAction_returned(self, DoNothingAction, CopyToClipboardAction):
        item = CalcResultItem(error='message')
        assert item.on_enter('q') == DoNothingAction.return_value
        DoNothingAction.assert_called_with()
        assert not CopyToClipboardAction.called
