import os
import sys

from ulauncher.api import SearchableResult

from ulauncher.api.shared.action.BaseAction import BaseAction


class ExtensionResult(SearchableResult):
    """
    Should be used in extensions.

    Cannot be subclassed there because :func:`pickle.loads` won't work in Ulauncher app
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.is_extension = True
        self.extension_path = os.path.dirname(sys.argv[0])

        if self._on_enter and not isinstance(self._on_enter, BaseAction):
            raise Exception("Incorrect type of on_enter argument")

    def on_enter(self, query):
        return self._on_enter

    def on_alt_enter(self, query):
        return self._on_alt_enter
