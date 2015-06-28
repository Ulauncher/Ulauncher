import mock
import pytest
from ulauncher.search.file_browser.FileBrowserResultItem import FileBrowserResultItem
from ulauncher.search.file_browser.Path import Path
from ulauncher.search.file_browser.FileQueries import FileQueries


class TestFileBrowserResultItem:

    @pytest.fixture
    def path(self):
        return mock.create_autospec(Path)

    @pytest.fixture
    def file_queries(self):
        return mock.create_autospec(FileQueries)

    @pytest.fixture
    def result_item(self, path, file_queries, mocker):
        FileQueries = mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.FileQueries')
        FileQueries.get_instance.return_value = file_queries
        return FileBrowserResultItem(path)

    def test_get_name(self, result_item, path):
        assert result_item.get_name() == path.get_basename.return_value

    def test_icon(self, result_item, path, mocker):
        get_file_icon = mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.get_file_icon')
        assert result_item.get_icon() == get_file_icon.return_value
        get_file_icon.assert_called_with(path, result_item.ICON_SIZE)

    def test_on_enter(self, result_item, path, mocker, file_queries):
        ActionList = mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.ActionList')
        SetUserQueryAction = mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.SetUserQueryAction')
        assert result_item.on_enter('query') == ActionList.return_value
        assert SetUserQueryAction.called
        file_queries.put.assert_called_with(str(path))

        # is not dir
        path.is_dir.return_value = False
        assert result_item.on_enter('query') == ActionList.return_value
