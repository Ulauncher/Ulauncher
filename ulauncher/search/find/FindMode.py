import os
from gi.repository import Gdk
from ulauncher.ext.SearchMode import SearchMode
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.SetUserQueryAction import SetUserQueryAction
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.utils.Path import Path, InvalidPathError
from .FindResultItem import FindResultItem
from .FileDb import FileDb


class FindMode(SearchMode):
    RESULT_LIMIT = 17

    def __init__(self):
        self._file_db = FileDb.get_instance()

    def is_enabled(self, query):
        """
        Enabled for queries that start with 'find '
        """
        return query.get_keyword() == 'find'

    def create_result_item(self, path_srt):
        return FindResultItem(Path(path_srt))

    def on_query(self, query):
        find_query = query.get_argument()
        if find_query:
            result_items = map(self.create_result_item, self._file_db.find(find_query, limit=self.RESULT_LIMIT))
        else:
            result_items = []
        return ActionList((RenderResultListAction(result_items),))
