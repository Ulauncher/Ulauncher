from ulauncher.api.result.searchable_result import SearchableResult
from ulauncher.api.shared.action.BaseAction import BaseAction


class ExtensionResult(SearchableResult):
    """
    Should be used in extensions.

    Cannot be subclassed there because :func:`pickle.loads` won't work in Ulauncher app
    """
    is_extension = True

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        if self._on_enter and not isinstance(self._on_enter, BaseAction):
            raise Exception("Invalid on_enter argument. Expected BaseAction")

    def on_enter(self, query):
        return self._on_enter

    def on_alt_enter(self, query):
        return self._on_alt_enter
