import os
import sys
from ulauncher.api.result.searchable_result import SearchableResult
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.icon import get_icon_path


class ExtensionResult(SearchableResult):
    """
    Should be used in extensions.

    Cannot be subclassed there because :func:`pickle.loads` won't work in Ulauncher app
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.extension_path = os.path.dirname(sys.argv[0])

        self.icon = get_icon_path(self.icon, self.ICON_SIZE, self.extension_path)

        if self._on_enter and not isinstance(self._on_enter, BaseAction):
            raise Exception("Invalid on_enter argument. Expected BaseAction")

    def on_enter(self, query):
        return self._on_enter

    def on_alt_enter(self, query):
        return self._on_alt_enter
