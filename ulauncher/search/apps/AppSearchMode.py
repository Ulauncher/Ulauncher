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
        items = AppResultItem.search(query)
        # If the search result is empty, add the default items for all other modes (only shotcuts currently)
        if not items:
            for mode in self.search_modes:
                items.extend(mode.get_default_items())
        return RenderResultListAction(items)
