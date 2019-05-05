import mock
import pytest
from ulauncher.search.file_browser.FileBrowserResultItem import FileBrowserResultItem
from ulauncher.search.file_browser.FileQueries import FileQueries
from ulauncher.utils.Path import Path


class TestFileBrowserResultItem:

    @pytest.fixture
    def path(self):
        path = mock.create_autospec(Path)
        path.get_user_path.return_value = '/test/path'
        return path

    @pytest.fixture
    def file_queries(self):
        return mock.create_autospec(FileQueries)

    @pytest.fixture
    def ActionList(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.ActionList')

    @pytest.fixture
    def Path(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.Path')

    @pytest.fixture
    def OpenFolderItem(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.OpenFolderItem')

    @pytest.fixture(autouse=True)
    def SetUserQueryAction(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.SetUserQueryAction')

    @pytest.fixture(autouse=True)
    def OpenAction(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.OpenAction')

    @pytest.fixture(autouse=True)
    def RenderAction(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.RenderResultListAction')

    @pytest.fixture(autouse=True)
    def CopyPathToClipboardItem(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.CopyPathToClipboardItem')

    @pytest.fixture
    def result_item(self, path, file_queries, mocker):
        FileQueriesMock = mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.FileQueries')
        FileQueriesMock.get_instance.return_value = file_queries
        return FileBrowserResultItem(path)

    def test_get_name(self, result_item, path):
        assert result_item.get_name() == path.get_basename.return_value

    def test_icon(self, result_item, path, mocker):
        get_file_icon = mocker.patch('ulauncher.search.file_browser.FileBrowserResultItem.get_file_icon')
        assert result_item.get_icon() == get_file_icon.return_value
        get_file_icon.assert_called_with(path, result_item.ICON_SIZE)

    # pylint: disable=too-many-arguments
    def test_on_enter(self, result_item, path, file_queries, OpenAction, SetUserQueryAction):
        assert result_item.on_enter('query') == SetUserQueryAction.return_value
        file_queries.save_query.assert_called_with(path.get_abs_path.return_value)

        # is not dir
        path.is_dir.return_value = False
        assert result_item.on_enter('query') == OpenAction.return_value

    def test_on_alt_enter_dir(self, result_item, RenderAction, OpenFolderItem, CopyPathToClipboardItem):
        assert result_item.on_alt_enter('query') == RenderAction.return_value
        RenderAction.assert_called_with([OpenFolderItem.return_value, CopyPathToClipboardItem.return_value])

    # pylint: disable=too-many-arguments, redefined-outer-name
    def test_on_alt_enter_file(self, result_item, path, OpenFolderItem, Path, RenderAction, CopyPathToClipboardItem):
        path.is_dir.return_value = False
        assert result_item.on_alt_enter('query') == RenderAction.return_value
        Path.assert_called_with(path.get_dirname.return_value)
        OpenFolderItem.assert_called_with(Path.return_value)
        RenderAction.assert_called_with([OpenFolderItem.return_value, CopyPathToClipboardItem.return_value])
