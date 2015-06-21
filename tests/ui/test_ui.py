import mock
import pytest
from ulauncher.ui import create_item, create_item_widgets
from ulauncher.ext.ResultItem import ResultItem


@pytest.fixture
def result_item():
    return mock.create_autospec(ResultItem)


@pytest.fixture
def Builder(mocker):
    return mocker.patch('ulauncher.ui.Gtk.Builder')


@pytest.fixture(autouse=True)
def get_data_file(mocker):
    return mocker.patch('ulauncher.ui.get_data_file')


@pytest.fixture(autouse=True)
def os_path_exists(mocker):
    return mocker.patch('ulauncher.ui.os.path.exists')


def test_create_item(result_item, Builder, get_data_file):
    assert create_item(result_item, 1, 'test') is Builder.return_value.get_object.return_value
    Builder.return_value.get_object.assert_called_with('item-frame')
    Builder.return_value.get_object.return_value.initialize.assert_called_with(
        Builder.return_value, result_item, 1, 'test')
    Builder.return_value.add_from_file.assert_called_with(get_data_file.return_value)
    get_data_file.assert_called_with('ui', '%s.ui' % result_item.UI_FILE)
