# -*- Mode: Python; coding: utf-8;

import unittest
import mock
from gi.repository import Gtk, GdkPixbuf
from ulauncher.results.ResultItem import ResultItem


class TestResultItem(unittest.TestCase):

    def setUp(self):
        self.result_item = ResultItem()

        self.builderMock = mock.MagicMock()
        self.builderMock.get_object.return_value = mock.MagicMock()
        self.result_item.set_builder(self.builderMock)

    @mock.patch.object(ResultItem, 'set_shortcut', autospec=True)
    def test_set_index(self, mock_set_shortcut):
        self.result_item.set_index(2)
        mock_set_shortcut.assert_called_once_with(self.result_item, 'Alt+3')

    @mock.patch('gi.repository.Gtk.StyleContext.add_class')
    @mock.patch.object(ResultItem, 'set_shortcut', autospec=True)
    def test_select(self, mock_set_shortcut, mock_add_class):
        self.result_item.select()
        mock_set_shortcut.assert_called_once_with(self.result_item, '⏎')
        mock_add_class.assert_called_once_with('selected')

    @mock.patch('gi.repository.Gtk.StyleContext.remove_class')
    @mock.patch.object(ResultItem, 'set_shortcut', autospec=True)
    def test_deselect(self, mock_set_shortcut, mock_remove_class):
        self.result_item.deselect()
        mock_set_shortcut.assert_called_once_with(self.result_item, self.result_item.shortcut)
        mock_remove_class.assert_called_once_with('selected')

    @mock.patch.object(ResultItem, 'load_icon')
    @mock.patch.object(ResultItem, 'set_default_icon')
    def test_set_icon_called_with_path(self, mock_set_default_icon, mock_load_icon):
        pixbuf = mock.Mock(spec=GdkPixbuf.Pixbuf)
        mock_load_icon.return_value = pixbuf

        iconWgt = mock.MagicMock()
        self.builderMock.get_object.return_value = iconWgt

        self.result_item.set_icon('path')
        self.builderMock.get_object.assert_called_with('item-icon')
        mock_load_icon.assert_called_once_with('path')
        iconWgt.set_from_pixbuf.assert_called_once_with(pixbuf)

    @mock.patch.object(ResultItem, 'load_icon')
    @mock.patch.object(ResultItem, 'set_default_icon')
    def test_set_icon_called_with_pixbuf(self, mock_set_default_icon, mock_load_icon):
        pixbuf = mock.Mock(spec=GdkPixbuf.Pixbuf)
        mock_load_icon.return_value = pixbuf

        iconWgt = mock.MagicMock()
        self.builderMock.get_object.return_value = iconWgt

        self.result_item.set_icon(pixbuf)
        self.builderMock.get_object.assert_called_with('item-icon')
        assert not mock_load_icon.called
        iconWgt.set_from_pixbuf.assert_called_once_with(pixbuf)

    def test_set_name(self):
        self.result_item.set_name('test name')
        self.builderMock.get_object.return_value.set_text.assert_called_with('test name')

    @mock.patch.object(ResultItem, 'get_toplevel')
    def test_on_click(self, mock_get_toplevel):
        mock_get_toplevel.return_value = mock.MagicMock()
        self.result_item.set_index(3)
        self.result_item.on_click(None, None)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(3)
        assert mock_get_toplevel.return_value.enter_result_item.called

    @mock.patch.object(ResultItem, 'get_toplevel')
    def test_on_mouse_hover(self, mock_get_toplevel):
        mock_get_toplevel.return_value = mock.MagicMock()
        self.result_item.set_index(4)
        self.result_item.on_mouse_hover(None, None)
        mock_get_toplevel.return_value.select_result_item.assert_called_with(4)

    def test_set_description(self):
        self.result_item.set_description('test description')
        self.builderMock.get_object.return_value.set_text.assert_called_with('test description')

    def test_no_description(self):
        self.result_item.set_description(None)
        self.builderMock.get_object.return_value.destroy.assert_called_with()

    def test_set_shortcut(self):
        self.result_item.set_shortcut('Alt+1')
        self.builderMock.get_object.return_value.set_text.assert_called_with('Alt+1')
