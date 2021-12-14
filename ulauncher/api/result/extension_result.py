import os
import sys

from ulauncher.api import Result
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.modes.QueryHistoryDb import QueryHistoryDb


class ExtensionResult(Result):
    """
    Should be used in extensions.

    Cannot be subclassed there because :func:`pickle.loads` won't work in Ulauncher app
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._is_extension = True
        self.extension_path = os.path.dirname(sys.argv[0])
        if self._on_enter and not isinstance(self._on_enter, BaseAction):
            raise Exception("Incorrect type of on_enter argument")

    def get_icon(self):
        if isinstance(self._icon, str) and not self._icon.startswith('/') and "." in self._icon:
            return os.path.join(self.extension_path, self._icon)

        # assuming it's GtkPixbuf
        return self._icon

    def on_enter(self, query):
        return self._on_enter

    def on_alt_enter(self, query):
        return self._on_alt_enter

    def selected_by_default(self, query):
        query_history = QueryHistoryDb.get_instance()
        return query_history.find(query) == self.get_name()
