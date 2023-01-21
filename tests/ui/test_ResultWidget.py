from unittest import mock
import pytest
from gi.repository import GdkPixbuf

from ulauncher.api.result import Result
from ulauncher.ui.ResultWidget import ResultWidget


# pylint: disable=too-many-public-methods
class TestResultWidget:
    @pytest.fixture
    def result(self):
        res = mock.create_autospec(Result)
        res.compact = False
        return res

    @pytest.fixture(autouse=True)
    def Theme(self, mocker):
        return mocker.patch("ulauncher.ui.ResultWidget.Theme")

    @pytest.fixture(autouse=True)
    def scroll_to_focus(self, mocker):
        return mocker.patch("ulauncher.ui.ResultWidget.ResultWidget.scroll_to_focus")

    @pytest.fixture(autouse=True)
    def unicodedata(self, mocker):
        return mocker.patch("ulauncher.utils.fuzzy_search.unicodedata")

    @pytest.fixture
    def result_wgt(self, builder, result):
        result_wgt = ResultWidget()
        result_wgt.initialize(builder, result, 3, "query")
        return result_wgt

    @pytest.fixture
    def item_box(self, result_wgt):
        return result_wgt.item_box

    @pytest.fixture(autouse=True)
    def builder(self):
        return mock.MagicMock()

    @pytest.fixture
    def pixbuf(self):
        return mock.Mock(spec=GdkPixbuf.Pixbuf)

    def test_initialize(self, builder, result, mocker):
        result_wgt = ResultWidget()
        set_index = mocker.patch.object(result_wgt, "set_index")
        set_name = mocker.patch.object(result_wgt, "set_name")
        set_description = mocker.patch.object(result_wgt, "set_description")

        result_wgt.initialize(builder, result, 3, "query")

        builder.get_object.return_value.connect.assert_any_call("button-release-event", result_wgt.on_click)
        builder.get_object.return_value.connect.assert_any_call("enter_notify_event", result_wgt.on_mouse_hover)
        set_index.assert_called_with(3)
        set_name.assert_called()
        set_description.assert_called_with(result.get_description.return_value)
        result.get_description.assert_called_with("query")

    def test_set_index(self, result_wgt, mocker):
        mock_set_shortcut = mocker.patch.object(result_wgt, "set_shortcut")

        result_wgt.set_index(2)
        mock_set_shortcut.assert_called_once_with("Alt+3")

    def test_select(self, result_wgt, item_box, mocker):
        mock_get_style_context = mocker.patch.object(item_box, "get_style_context")
        result_wgt.select()
        mock_get_style_context.return_value.add_class.assert_called_once_with("selected")

    def test_deselect(self, result_wgt, item_box, mocker):
        mock_get_style_context = mocker.patch.object(item_box, "get_style_context")
        result_wgt.deselect()
        mock_get_style_context.return_value.remove_class.assert_called_once_with("selected")

    def test_set_icon(self, result_wgt, builder, pixbuf):
        iconWgt = mock.MagicMock()
        builder.get_object.return_value = iconWgt

        result_wgt.set_icon(pixbuf)
        iconWgt.set_from_surface.assert_called_with(pixbuf)

    def test_set_name(self, result_wgt, builder):
        result_wgt.set_name("test name")
        builder.get_object.return_value.set_text.assert_called_with("test name")

    def test_on_click(self, mocker, result_wgt):
        mock_get_toplevel = mocker.patch.object(result_wgt, "get_toplevel")

        result_wgt.set_index(3)
        result_wgt.on_click(None, None)
        mock_get_toplevel.return_value.select_result.assert_called_with(3)
        mock_get_toplevel.return_value.enter_result.assert_called_with(alt=False)

    def test_on_click_alt_enter(self, mocker, result_wgt):
        mock_get_toplevel = mocker.patch.object(result_wgt, "get_toplevel")

        event = mock.MagicMock()
        event.button = 3
        result_wgt.set_index(3)
        result_wgt.on_click(None, event)
        mock_get_toplevel.return_value.select_result.assert_called_with(3)
        mock_get_toplevel.return_value.enter_result.assert_called_with(alt=True)

    def test_set_description(self, result_wgt, builder):
        result_wgt.set_description("test description")
        builder.get_object.return_value.set_text.assert_called_with("test description")

    def test_no_description(self, result_wgt, builder):
        result_wgt.set_description(None)
        builder.get_object.return_value.destroy.assert_called_with()

    def test_set_shortcut(self, result_wgt, builder):
        result_wgt.set_shortcut("Alt+1")
        builder.get_object.return_value.set_text.assert_called_with("Alt+1")

    def test_keyword(self, result_wgt, result):
        assert result_wgt.get_keyword() is result.keyword
