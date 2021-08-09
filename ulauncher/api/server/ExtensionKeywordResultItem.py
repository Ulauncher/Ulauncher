from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.search.QueryHistoryDb import QueryHistoryDb


class ExtensionKeywordResultItem(ResultItem):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._query_history = QueryHistoryDb.get_instance()

    def selected_by_default(self, query):
        """
        :param ~ulauncher.search.Query.Query query:
        """
        return self._query_history.find(query) == self.get_name()

    def on_enter(self, query):
        """
        :param ~ulauncher.search.Query.Query query: query
        """
        self._query_history.save_query(query, self.get_name())
        return SetUserQueryAction('%s ' % self.get_keyword())
