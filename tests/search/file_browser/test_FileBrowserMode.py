import mock
import pytest
from gi.repository import Gdk
from ulauncher.search.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.utils.Path import Path, InvalidPathError
from ulauncher.search.file_browser.FileQueries import FileQueries
from ulauncher.search.file_browser.FileBrowserResultItem import FileBrowserResultItem


class TestFileBrowserMode:

    @pytest.fixture
    def path(self):
        return mock.create_autospec(Path)

    @pytest.fixture
    def file_queries(self):
        return mock.create_autospec(FileQueries)

    @pytest.fixture
    def ActionList(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserMode.ActionList')

    @pytest.fixture
    def SetUserQueryAction(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserMode.SetUserQueryAction')

    @pytest.fixture
    def SortedResultList(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserMode.SortedResultList')

    @pytest.fixture
    def RenderResultListAction(self, mocker):
        return mocker.patch('ulauncher.search.file_browser.FileBrowserMode.RenderResultListAction')

    @pytest.fixture
    def mode(self, file_queries, mocker):
        FileQueries = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.FileQueries')
        FileQueries.get_instance.return_value = file_queries
        return FileBrowserMode()

    def test_is_enabled(self, mode):
        assert mode.is_enabled('~/Downloads')
        assert mode.is_enabled('~')
        assert mode.is_enabled('$USER/Videos')
        assert mode.is_enabled('/usr/bin')
        assert mode.is_enabled('/')
        assert mode.is_enabled(' /foo/bar')

        assert not mode.is_enabled('test')
        assert not mode.is_enabled('+')
        assert not mode.is_enabled(' ')

    def test_list_files(self, mode, mocker, file_queries):
        listdir = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.os.listdir')
        listdir.return_value = ['a', 'd', 'b', 'c']
        file_queries.find.side_effect = lambda i: i
        assert mode.list_files('path') == sorted(listdir.return_value)
        assert mode.list_files('path', sort_by_usage=True) == sorted(listdir.return_value, reverse=True)

    def test_create_result_item(self, mode, mocker):
        FileBrowserResultItem = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.FileBrowserResultItem')
        Path = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Path')
        assert mode.create_result_item('path') == FileBrowserResultItem.return_value
        FileBrowserResultItem.assert_called_once_with(Path.return_value)
        Path.assert_called_once_with('path')

    def test_filter_dot_files(self, mode):
        assert mode.filter_dot_files(['a', '.b', 'c', '.d']) == ['a', 'c']

    def test_on_query__return_value(self, mode, mocker, ActionList, RenderResultListAction):
        mocker.patch.object(mode, 'list_files', return_value=['a', 'd', 'b', 'c'])
        assert mode.on_query('/usr/bin') == ActionList.return_value
        ActionList.assert_called_once_with((RenderResultListAction.return_value,))

        # invalid path
        mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Path.get_existing_dir',
                     side_effect=InvalidPathError)
        assert mode.on_query('~~') == ActionList.return_value
        ActionList.assert_called_with((RenderResultListAction.return_value,))
        RenderResultListAction.assert_called_with([])

    def test_on_query__existing_path(self, mode, mocker, ActionList, RenderResultListAction):
        mode.RESULT_LIMIT = 3
        mocker.patch.object(mode, 'list_files', return_value=sorted(['a', 'd', 'b', '.c', 'e'], reverse=True))
        mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Path.get_existing_dir',
                     return_value='/usr/bin')
        mocker.patch.object(mode, 'create_result_item', side_effect=lambda i: i)
        assert mode.on_query('/usr/bin') == ActionList.return_value
        RenderResultListAction.assert_called_with(['/usr/bin/e', '/usr/bin/d', '/usr/bin/b'])

    def test_on_query__non_existing_path(self, mode, mocker, ActionList, RenderResultListAction, SortedResultList):
        mode.RESULT_LIMIT = 3
        mocker.patch.object(mode, 'list_files', return_value=sorted(['a', 'd', 'b', '.c', 'e'], reverse=True))
        path = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Path').return_value
        mocker.patch.object(mode, 'create_result_item', side_effect=lambda i: i)
        assert mode.on_query('/usr/bin/foo') == ActionList.return_value
        SortedResultList.assert_called_with(path.get_search_part.return_value, min_score=40, limit=3)
        RenderResultListAction.assert_called_with(SortedResultList.return_value)

    def test_on_key_press_event(self, mode, mocker, SetUserQueryAction):
        keyval_name = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Gdk.keyval_name',
                                   return_value='BackSpace')
        widget = mock.MagicMock()
        event = mock.MagicMock()
        event.state = 0
        query = '/usr/bin/'
        widget.get_position.return_value = len(query)
        widget.get_selection_bounds.return_value = tuple()
        mode.on_key_press_event(widget, event, query)

        SetUserQueryAction.assert_called_with('/usr/')
        SetUserQueryAction.return_value.run.assert_called_with()
        widget.emit_stop_by_name.assert_called_with('key-press-event')

    def test_on_key_press_event__not_backspace(self, mode, mocker, SetUserQueryAction):
        keyval_name = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Gdk.keyval_name',
                                   return_value='Enter')
        widget = mock.MagicMock()
        event = mock.MagicMock()
        event.state = 0
        query = '/usr/bin/'
        widget.get_position.return_value = len(query)
        mode.on_key_press_event(widget, event, query)

        assert not SetUserQueryAction.called
        assert not widget.emit_stop_by_name.called

    def test_on_key_press_event__ctrl_pressed(self, mode, mocker, SetUserQueryAction):
        keyval_name = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Gdk.keyval_name',
                                   return_value='BackSpace')
        widget = mock.MagicMock()
        event = mock.MagicMock()
        event.state = Gdk.ModifierType.MOD2_MASK | Gdk.ModifierType.CONTROL_MASK
        query = '/usr/bin/'
        widget.get_position.return_value = len(query)
        mode.on_key_press_event(widget, event, query)

        assert not SetUserQueryAction.called
        assert not widget.emit_stop_by_name.called

    def test_on_key_press_event__wrong_cursor_position(self, mode, mocker, SetUserQueryAction):
        keyval_name = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Gdk.keyval_name',
                                   return_value='BackSpace')
        widget = mock.MagicMock()
        event = mock.MagicMock()
        event.state = 0
        query = '/usr/bin/'
        widget.get_position.return_value = 3
        mode.on_key_press_event(widget, event, query)

        assert not SetUserQueryAction.called
        assert not widget.emit_stop_by_name.called

    def test_on_key_press_event__not_dir(self, mode, mocker, SetUserQueryAction):
        keyval_name = mocker.patch('ulauncher.search.file_browser.FileBrowserMode.Gdk.keyval_name',
                                   return_value='BackSpace')
        widget = mock.MagicMock()
        event = mock.MagicMock()
        event.state = 0
        query = '/usr/b/'
        widget.get_position.return_value = len(query)
        mode.on_key_press_event(widget, event, query)

        assert not SetUserQueryAction.called
        assert not widget.emit_stop_by_name.called
