import os
from gi.repository import Gdk
from ulauncher.ext.SearchMode import SearchMode
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.search.SortedResultList import SortedResultList
from .Path import Path, InvalidPathError
from .FileBrowserResultItem import FileBrowserResultItem
from .FileQueries import FileQueries


class FileBrowserMode(SearchMode):
    RESULT_LIMIT = 17

    def __init__(self):
        self._file_queries = FileQueries.get_instance()

    def is_enabled(self, query):
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

    def list_files(self, path_str, sort_by_usage=False):
        files = os.listdir(path_str)
        if sort_by_usage:
            return sorted(files, reverse=True, key=lambda f: self._file_queries.find(os.path.join(path_str, f)))
        else:
            return sorted(files)

    def create_result_item(self, path_srt):
        return FileBrowserResultItem(Path(path_srt))

    def filter_dot_files(self, file_list):
        return filter(lambda f: not f.startswith('.'), file_list)

    def on_key_press_event(self, widget, event, query):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        path = Path(query)
        if keyname == 'BackSpace' and not ctrl and widget.get_position() == len(query) and path.is_dir():
            # stop key press event if:
            # it's a BackSpace key and
            # Ctrl modifier is not pressed and
            # cursor is at the last position and
            # path exists and it's a directory
            widget.emit_stop_by_name('key-press-event')
            SetUserQueryAction(os.path.join(path.get_dirname(), '')).run()

    def on_query(self, query):
        if query == '~':
            return ActionList((SetUserQueryAction('~/'),))

        path = Path(query)

        try:
            existing_dir = path.get_existing_dir()
            if existing_dir == str(path):
                results = self.list_files(str(path), sort_by_usage=True)
                result_items = map(self.create_result_item, map(lambda name: os.path.join(existing_dir, name),
                                   self.filter_dot_files(results)[:self.RESULT_LIMIT]))
            else:
                results = self.list_files(existing_dir)
                search_for = path.get_search_part()
                if not search_for.startswith('.'):
                    # don't show dot files in the results
                    results = map(lambda name: os.path.join(existing_dir, name), self.filter_dot_files(results))
                else:
                    results = map(lambda name: os.path.join(existing_dir, name), results)

                result_items = SortedResultList(search_for, min_score=40, limit=self.RESULT_LIMIT)
                result_items.extend(map(self.create_result_item, reversed(results)))
        except (InvalidPathError, OSError):
            return ActionList((RenderResultListAction([]),))

        return ActionList((RenderResultListAction(result_items),))
