from ulauncher.api.shared.action.LaunchAppAction import LaunchAppAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.search.QueryHistoryDb import QueryHistoryDb
from ulauncher.search.apps.AppStatDb import AppStatDb


class AppResultItem(ResultItem):
    """
    :param dict record:
    """

    # pylint: disable=super-init-not-called
    def __init__(self, record):
        self.record = record
        self._query_history = QueryHistoryDb.get_instance()
        self._app_stat_db = AppStatDb.get_instance()

    def get_name(self):
        return self.record.get('name')

    def get_search_name(self):
        return self.record.get('search_name')

    def get_description(self, query):
        return self.record.get('description')

    def selected_by_default(self, query):
        """
        :param ~ulauncher.search.Query.Query query:
        """
        return self._query_history.find(query) == self.record.get('name')

    def get_icon(self):
        return self.record.get('icon')

    def on_enter(self, query):
        self._query_history.save_query(str(query), self.record.get('name'))

        self._app_stat_db.inc_count(self.record.get('desktop_file'))
        self._app_stat_db.commit()

        return LaunchAppAction(self.record.get('desktop_file'))
