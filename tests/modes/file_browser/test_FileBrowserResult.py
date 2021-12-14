import mock
import pytest
from ulauncher.modes.file_browser.FileBrowserResult import FileBrowserResult
from ulauncher.modes.file_browser.FileQueries import FileQueries
from ulauncher.utils.Path import Path


class TestFileBrowserResult:

    @pytest.fixture
    def path(self):
        path = mock.create_autospec(Path)
        path.get_user_path.return_value = '/test/path'
        return path

    @pytest.fixture
    def file_queries(self):
        return mock.create_autospec(FileQueries)

    @pytest.fixture
    def Path(self, mocker):
        return mocker.patch('ulauncher.modes.file_browser.FileBrowserResult.Path')

    @pytest.fixture
    def OpenFolderItem(self, mocker):
        return mocker.patch('ulauncher.modes.file_browser.FileBrowserResult.OpenFolderItem')

    @pytest.fixture(autouse=True)
    def SetUserQueryAction(self, mocker):
        return mocker.patch('ulauncher.modes.file_browser.FileBrowserResult.SetUserQueryAction')

    @pytest.fixture(autouse=True)
    def OpenAction(self, mocker):
        return mocker.patch('ulauncher.modes.file_browser.FileBrowserResult.OpenAction')

    @pytest.fixture(autouse=True)
    def CopyPathToClipboardItem(self, mocker):
        return mocker.patch('ulauncher.modes.file_browser.FileBrowserResult.CopyPathToClipboardItem')

    @pytest.fixture
    def result(self, path, file_queries, mocker):
        FileQueriesMock = mocker.patch('ulauncher.modes.file_browser.FileBrowserResult.FileQueries')
        FileQueriesMock.get_instance.return_value = file_queries
        return FileBrowserResult(path)

    def test_get_name(self, result, path):
        assert result.get_name() == path.get_basename.return_value

    def test_icon(self, result):
        assert isinstance(result.get_icon(), str)

    # pylint: disable=too-many-arguments
    def test_on_enter(self, result, path, file_queries, OpenAction, SetUserQueryAction):
        assert result.on_enter('query') == SetUserQueryAction.return_value
        file_queries.save_query.assert_called_with(path.get_abs_path.return_value)

        # is not dir
        path.is_dir.return_value = False
        assert result.on_enter('query') == OpenAction.return_value

    def test_on_alt_enter_dir(self, result, OpenFolderItem, CopyPathToClipboardItem):
        assert result.on_alt_enter('query') == [OpenFolderItem.return_value, CopyPathToClipboardItem.return_value]

    # pylint: disable=too-many-arguments, redefined-outer-name
    def test_on_alt_enter_file(self, result, path, OpenFolderItem, Path, CopyPathToClipboardItem):
        path.is_dir.return_value = False
        assert result.on_alt_enter('query') == [OpenFolderItem.return_value, CopyPathToClipboardItem.return_value]
        Path.assert_called_with(path.get_dirname.return_value)
        OpenFolderItem.assert_called_with(Path.return_value)
