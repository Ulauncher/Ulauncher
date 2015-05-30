# -*- Mode: Python; coding: utf-8;

import pytest
import mock
from ulauncher.ui.AppResultItemWidget import AppResultItemWidget
from ulauncher.ext.ResultItem import ResultItem


class TestAppResultItemWidget(object):

    @pytest.fixture
    def item_obj(self):
        return mock.create_autospec(ResultItem)

    @pytest.fixture
    def result_item_wgt(self, builder, item_obj):
        result_item_wgt = AppResultItemWidget()
        result_item_wgt.initialize(builder, item_obj, 3, 'query')
        return result_item_wgt

    @pytest.fixture
    def builder(self):
        return mock.MagicMock()

    @pytest.fixture(autouse=True)
    def themed_icon(self, mocker):
        return mocker.patch('ulauncher.ui.AppResultItemWidget.get_themed_icon_by_name').return_value

    def test_set_default_icon(self, result_item_wgt, builder, themed_icon):
        iconWgt = builder.get_object.return_value
        result_item_wgt.set_default_icon()
        iconWgt.set_from_pixbuf.assert_called_with(themed_icon)
