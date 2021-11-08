from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.apps.AppResultItem import AppResultItem


class AppSearchMode(BaseSearchMode):
    """
    :type list search_modes: a list of other :class:`SearchMode` objects that provide additional result items
    """

    def __init__(self, search_modes):
        self.search_modes = search_modes

    def is_enabled(self, _):
        """
        AppSearchMode is a default search mode and is always enabled
        """
        return True

    def handle_query(self, query):
        return RenderResultListAction(AppResultItem.search(query))
