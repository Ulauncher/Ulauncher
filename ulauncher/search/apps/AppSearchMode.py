from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.search.apps.AppDb import AppDb


class AppSearchMode(BaseSearchMode):
    """
    :type list search_modes: a list of other :class:`SearchMode` objects that provide additional result items
    """

    def __init__(self, search_modes):
        self.search_modes = search_modes
        self.app_db = AppDb.get_instance()

    def is_enabled(self, query):
        """
        AppSearchMode is a default search mode and is always enabled
        """
        return True

    def handle_query(self, query):
        result_list = self.app_db.find(query)
        for mode in self.search_modes:
            result_list.extend(mode.get_searchable_items())

        if not len(result_list) and query:
            # default search
            result_list = []
            for mode in self.search_modes:
                result_list.extend(mode.get_default_items())

        return RenderResultListAction(result_list)
