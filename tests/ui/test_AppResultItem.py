# -*- Mode: Python; coding: utf-8;

import pytest
import mock
from ulauncher.ui.AppResultItem import AppResultItem


class TestAppResultItem(object):

    @pytest.fixture
    def result_item(self, builder, themed_icon):
        result_item = AppResultItem()
        result_item.set_builder(builder)
        return result_item

    @pytest.fixture
    def builder(self):
        return mock.MagicMock()

    @pytest.fixture
    def read_desktop_file(self, mocker):
        return mocker.patch('ulauncher.ui.AppResultItem.read_desktop_file')

    @pytest.fixture(autouse=True)
    def themed_icon(self, mocker):
        return mocker.patch('ulauncher.ui.AppResultItem.get_themed_icon_by_name').return_value

    @pytest.fixture(autouse=True)
    def metadata(self, result_item):
        result_item.metadata = {
            'desktop_file': 'test_desktop_file'
        }

    def test_enter(self, result_item, read_desktop_file):
        assert result_item.enter() == read_desktop_file.return_value.launch.return_value
        read_desktop_file.asser_called_with('test_desktop_file')

    def test_set_default_icon(self, result_item, builder, themed_icon):
        iconWgt = builder.get_object.return_value
        result_item.set_default_icon()
        iconWgt.set_from_pixbuf.assert_called_with(themed_icon)
