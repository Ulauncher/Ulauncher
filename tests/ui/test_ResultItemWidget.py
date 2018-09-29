import pytest
import mock

from collections import namedtuple

from gi.repository import GdkPixbuf

from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.ui.ResultItemWidget import ResultItemWidget


class TestResultItemWidget(object):

    @pytest.fixture
    def item_obj(self):
        return mock.create_autospec(ResultItem)

    @pytest.fixture(autouse=True)
    def Theme(self, mocker):
        return mocker.patch('ulauncher.ui.ResultItemWidget.Theme')

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.ui.windows.PreferencesUlauncherDialog'
                            '.Settings.get_instance').return_value

    @pytest.fixture
    def result_item_wgt(self, builder, item_obj):
        result_item_wgt = ResultItemWidget()
        result_item_wgt.initialize(builder, item_obj, 3, 'query')
        return result_item_wgt

    @pytest.fixture
    def item_box(self, result_item_wgt):
        return result_item_wgt.item_box

    @pytest.fixture
    def builder(self):
        return mock.MagicMock()

    @pytest.fixture
    def pixbuf(self):
        return mock.Mock(spec=GdkPixbuf.Pixbuf)

    def test_initialize_enabled_shortcut_keys(self, builder, item_obj, mocker,
                                              settings):

        def enable_short_key_is_true(key):
            if key == 'enable-shortcut-keys':
                return True
            else:
                raise AssertionError("wrong keys is being looked up: %s" % key)
        settings.get_property.side_effect = enable_short_key_is_true

        result_item_wgt = ResultItemWidget()
        set_index = mocker.patch.object(result_item_wgt, 'set_index')
        set_icon = mocker.patch.object(result_item_wgt, 'set_icon')
        set_name = mocker.patch.object(result_item_wgt, 'set_name')
        set_description = mocker.patch.object(result_item_wgt, 'set_description')

        result_item_wgt.initialize(builder, item_obj, 3, 'query')

        builder.get_object.return_value.connect.assert_any_call("button-release-event", result_item_wgt.on_click)
        builder.get_object.return_value.connect.assert_any_call("enter_notify_event", result_item_wgt.on_mouse_hover)
        set_index.assert_called_with(3)
        set_name.assert_called_with(item_obj.get_name_highlighted.return_value)
        set_description.assert_called_with(item_obj.get_description.return_value)
        item_obj.get_description.assert_called_with('query')

    def test_initialize_disabled_shortcut_keys(self, builder, item_obj, mocker, settings):

        def enable_short_key_is_false(key):
            if key == 'enable-shortcut-keys':
                return False
            else:
                raise AssertionError("wrong keys is being looked up: %s" % key)
        settings.get_property.side_effect = enable_short_key_is_false

        result_item_wgt = ResultItemWidget()
        hide_shortcut = mocker.patch.object(result_item_wgt, 'hide_shortcut')
        set_icon = mocker.patch.object(result_item_wgt, 'set_icon')
        set_name = mocker.patch.object(result_item_wgt, 'set_name')
        set_description = mocker.patch.object(result_item_wgt, 'set_description')

        result_item_wgt.initialize(builder, item_obj, 3, 'query')

        builder.get_object.return_value.connect.assert_any_call("button-release-event", result_item_wgt.on_click)
        builder.get_object.return_value.connect.assert_any_call("enter_notify_event", result_item_wgt.on_mouse_hover)
        hide_shortcut.assert_called_once()
        set_name.assert_called_with(item_obj.get_name_highlighted.return_value)
        set_description.assert_called_with(item_obj.get_description.return_value)
        item_obj.get_description.assert_called_with('query')

    def test_set_index(self, result_item_wgt, mocker):
        mock_set_shortcut = mocker.patch.object(result_item_wgt, 'set_shortcut')

        result_item_wgt.set_index(2)
        mock_set_shortcut.assert_called_once_with('Alt+3')

    def test_hide_shortcut(self, result_item_wgt, mocker, builder):

        # namedtuple to be returned by get_size_request
        Size = namedtuple("Size", "width height")

        # test values
        shortcut_width = 10
        shortcut_margin_left = 2
        shortcut_margin_right = 4
        descr_width = 20
        descr_height = 30
        expected_new_descr_width = \
            descr_width + \
            shortcut_width + \
            shortcut_margin_left + \
            shortcut_margin_right

        # patch for set_shortut
        mock_set_shortcut = mocker.patch.object(result_item_wgt,
                                                'set_shortcut')

        # mock for shortcut widget
        shortcut_object = mock.MagicMock()
        shortcut_object.get_size_request.return_value = \
            Size(width=shortcut_width, height=None)
        shortcut_object.get_margin_left.return_value = shortcut_margin_left
        shortcut_object.get_margin_right.return_value = shortcut_margin_right

        # mock for descriptions widget
        descr_object = mock.MagicMock()
        descr_object.get_size_request.return_value = \
            Size(width=descr_width, height=descr_height)

        # mock for builder get_object that returns correct object based on
        # the requested id
        def get_object(item_id):
            if item_id == "item-shortcut":
                return shortcut_object
            elif item_id == "item-descr":
                return descr_object
            else:
                raise AssertionError("wrong items is being looked up: %s"
                                     % item_id)
        builder.get_object.side_effect = get_object

        # callFUT
        result_item_wgt.hide_shortcut()

        # assert that we set shortcut widget to not show on show_all
        shortcut_object.set_no_show_all.assert_called_once_with(True)
        # assert that we hide shortcut widget
        shortcut_object.hide.assert_called_once()
        # assert set_shortcut was called with empty string
        mock_set_shortcut.assert_called_once_with('')
        # assert that we set new size
        descr_object.set_size_request.assert_called_once_with(
            width=expected_new_descr_width,
            height=descr_height,
        )

    def test_select(self, result_item_wgt, item_box, mocker, builder):
        mock_get_style_context = mocker.patch.object(item_box, 'get_style_context')
        result_item_wgt.select()
        mock_get_style_context.return_value.add_class.assert_called_once_with('selected')

    def test_deselect(self, result_item_wgt, item_box, mocker, builder):
        mock_get_style_context = mocker.patch.object(item_box, 'get_style_context')
        result_item_wgt.deselect()
        mock_get_style_context.return_value.remove_class.assert_called_once_with('selected')

    def test_set_icon(self, result_item_wgt, builder, pixbuf):
        iconWgt = mock.MagicMock()
        builder.get_object.return_value = iconWgt

        result_item_wgt.set_icon(pixbuf)
        iconWgt.set_from_pixbuf.assert_called_with(pixbuf)

    def test_set_name(self, result_item_wgt, builder):
        result_item_wgt.set_name('test name')
        builder.get_object.return_value.set_text.assert_called_with('test name')

    def test_on_click(self, mocker, result_item_wgt):
        mock_get_toplevel = mocker.patch.object(result_item_wgt, 'get_toplevel')

        result_item_wgt.set_index(3)
        result_item_wgt.on_click(None, None)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(3)
        mock_get_toplevel.return_value.enter_result_item.assert_called_with(alt=False)

    def test_on_click_alt_enter(self, mocker, result_item_wgt):
        mock_get_toplevel = mocker.patch.object(result_item_wgt, 'get_toplevel')

        event = mock.MagicMock()
        event.button = 3
        result_item_wgt.set_index(3)
        result_item_wgt.on_click(None, event)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(3)
        mock_get_toplevel.return_value.enter_result_item.assert_called_with(alt=True)

    def test_on_mouse_hover(self, mocker, result_item_wgt):
        mock_get_toplevel = mocker.patch.object(result_item_wgt, 'get_toplevel')

        result_item_wgt.set_index(4)
        result_item_wgt.on_mouse_hover(None, None)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(4, onHover=True)

    def test_set_description(self, result_item_wgt, builder):
        result_item_wgt.set_description('test description')
        builder.get_object.return_value.set_text.assert_called_with('test description')

    def test_no_description(self, result_item_wgt, builder):
        result_item_wgt.set_description(None)
        builder.get_object.return_value.destroy.assert_called_with()

    def test_set_shortcut(self, result_item_wgt, builder):
        result_item_wgt.set_shortcut('Alt+1')
        builder.get_object.return_value.set_text.assert_called_with('Alt+1')

    def test_on_enter(self, result_item_wgt, item_obj):
        assert result_item_wgt.on_enter('test') is item_obj.on_enter.return_value
        item_obj.on_enter.assert_called_with('test')

    def test_on_alt_enter(self, result_item_wgt, item_obj):
        assert result_item_wgt.on_alt_enter('test') is item_obj.on_alt_enter.return_value
        item_obj.on_alt_enter.assert_called_with('test')

    def test_get_keyword(self, result_item_wgt, item_obj):
        assert result_item_wgt.get_keyword() is item_obj.get_keyword.return_value

    def test_selected_by_default(self, result_item_wgt, item_obj):
        assert result_item_wgt.selected_by_default('q') is item_obj.selected_by_default.return_value
