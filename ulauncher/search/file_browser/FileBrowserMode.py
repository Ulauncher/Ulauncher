import os
from typing import List, Union
import gi
gi.require_version('Gdk', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import Gdk

from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.utils.Path import Path, InvalidPathError
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.SortedList import SortedList
from ulauncher.search.file_browser.FileBrowserResultItem import FileBrowserResultItem
from ulauncher.search.file_browser.FileQueries import FileQueries


class FileBrowserMode(BaseSearchMode):
    RESULT_LIMIT = 17

    def __init__(self):
        self._file_queries = FileQueries.get_instance()  # type: FileQueries

    def is_enabled(self, query: str) -> bool:
        """
        Enabled for queries like:
        ~/Downloads
        $USER/Downloads
        /usr/bin/foo
        """
        try:
            return query.lstrip()[0] in ('~', '/', '$')
        except IndexError:
            return False

    def list_files(self, path_str: str, sort_by_usage: bool = False) -> List[str]:
        files = os.listdir(path_str)

        def get_last_used_time(file: str) -> float:
            return self._file_queries.find(os.path.join(path_str, file)) or 0

        if sort_by_usage:
            return sorted(files, reverse=True, key=get_last_used_time)

        return sorted(files)

    def create_result_item(self, path_srt: str) -> FileBrowserResultItem:
        return FileBrowserResultItem(Path(path_srt))

    def filter_dot_files(self, file_list: List[str]) -> List[str]:
        return list(filter(lambda f: not f.startswith('.'), file_list))

    def handle_query(self, query: str) -> BaseAction:
        if query == '~':
            return SetUserQueryAction('~/')

        path = Path(query)  # type: Path
        result_items = []  # type: Union[List, SortedList]

        try:
            existing_dir = path.get_existing_dir()

            if existing_dir == path.get_abs_path():
                file_names = self.list_files(path.get_abs_path(), sort_by_usage=True)
                for name in self.filter_dot_files(file_names)[:self.RESULT_LIMIT]:
                    file = os.path.join(existing_dir, name)
                    result_items.append(self.create_result_item(file))

            else:
                file_names = self.list_files(existing_dir)
                search_for = path.get_search_part()

                if not search_for.startswith('.'):
                    file_names = self.filter_dot_files(file_names)

                files = [os.path.join(existing_dir, name) for name in file_names]
                result_items = SortedList(search_for, min_score=40, limit=self.RESULT_LIMIT)
                result_items.extend([self.create_result_item(name) for name in reversed(files)])

        except (InvalidPathError, OSError):
            result_items = []

        return RenderResultListAction(result_items)

    def handle_key_press_event(self, widget, event, query):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        path = Path(query)
        if keyname == 'BackSpace' and not ctrl and widget.get_position() == len(query) and path.is_dir() and \
           not widget.get_selection_bounds():
            # stop key press event if:
            # it's a BackSpace key and
            # Ctrl modifier is not pressed and
            # cursor is at the last position and
            # path exists and it's a directory and
            # input text is not selected
            widget.emit_stop_by_name('key-press-event')
            return SetUserQueryAction(os.path.join(path.get_dirname(), ''))

        return DoNothingAction()
