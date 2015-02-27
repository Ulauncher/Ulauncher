# -*- Mode: Python; coding: utf-8;

import pytest
import mock
from gi.repository import Gtk, GdkPixbuf
from ulauncher.results.ResultItem import ResultItem


class TestResultItem(object):

    @pytest.fixture
    def result_item(self, builder):
        result_item = ResultItem()
        result_item.set_builder(builder)
        return result_item

    @pytest.fixture
    def builder(self):
        return mock.MagicMock()

    @pytest.fixture
    def pixbuf(self):
        return mock.Mock(spec=GdkPixbuf.Pixbuf)

    @pytest.fixture
    def mock_load_icon(self, pixbuf, result_item, mocker):
        mock_load_icon = mocker.patch.object(result_item, 'load_icon')
        mock_load_icon.return_value = pixbuf
        return mock_load_icon

    def test_set_index(self, result_item, mocker):
        mock_set_shortcut = mocker.patch.object(result_item, 'set_shortcut')

        result_item.set_index(2)
        mock_set_shortcut.assert_called_once_with('Alt+3')

    def test_select(self, result_item, mocker):
        mock_set_shortcut = mocker.patch.object(result_item, 'set_shortcut')
        mock_get_style_context = mocker.patch.object(result_item, 'get_style_context')

        result_item.select()
        mock_set_shortcut.assert_called_once_with('⏎')
        mock_get_style_context.return_value.add_class.assert_called_once_with('selected')

    def test_deselect(self, result_item, mocker):
        mock_set_shortcut = mocker.patch.object(result_item, 'set_shortcut')
        mock_get_style_context = mocker.patch.object(result_item, 'get_style_context')

        result_item.deselect()
        mock_set_shortcut.assert_called_once_with(result_item.shortcut)
        mock_get_style_context.return_value.remove_class.assert_called_once_with('selected')

    def test_set_icon_called_with_path(self, result_item, builder, mock_load_icon, pixbuf):
        iconWgt = mock.MagicMock()
        builder.get_object.return_value = iconWgt

        result_item.set_icon('path')
        builder.get_object.assert_called_with('item-icon')
        mock_load_icon.assert_called_once_with('path')
        iconWgt.set_from_pixbuf.assert_called_once_with(pixbuf)

    def test_set_icon_called_with_pixbuf(self, result_item, builder, mock_load_icon, pixbuf):
        iconWgt = mock.MagicMock()
        builder.get_object.return_value = iconWgt

        result_item.set_icon(pixbuf)
        builder.get_object.assert_called_with('item-icon')
        assert not mock_load_icon.called
        iconWgt.set_from_pixbuf.assert_called_once_with(pixbuf)

    def test_set_name(self, result_item, builder):
        result_item.set_name('test name')
        builder.get_object.return_value.set_text.assert_called_with('test name')

    def test_on_click(self, mocker, result_item):
        mock_get_toplevel = mocker.patch.object(result_item, 'get_toplevel')

        result_item.set_index(3)
        result_item.on_click(None, None)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(3)
        assert mock_get_toplevel.return_value.enter_result_item.called

    def test_on_mouse_hover(self, mocker, result_item):
        mock_get_toplevel = mocker.patch.object(result_item, 'get_toplevel')

        result_item.set_index(4)
        result_item.on_mouse_hover(None, None)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(4)

    def test_set_description(self, result_item, builder):
        result_item.set_description('test description')
        builder.get_object.return_value.set_text.assert_called_with('test description')

    def test_no_description(self, result_item, builder):
        result_item.set_description(None)
        builder.get_object.return_value.destroy.assert_called_with()

    def test_set_shortcut(self, result_item, builder):
        result_item.set_shortcut('Alt+1')
        builder.get_object.return_value.set_text.assert_called_with('Alt+1')
