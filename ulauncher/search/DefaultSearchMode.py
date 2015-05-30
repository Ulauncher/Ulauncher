from ulauncher.ext.SearchMode import SearchMode
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.search.apps.AppDb import AppDb


class DefaultSearchMode(SearchMode):

    def on_query(self, query):
        # TODO: append google, wiki search
        result_list = AppDb.get_instance().find(query)
        return ActionList((RenderResultListAction(result_list),))
