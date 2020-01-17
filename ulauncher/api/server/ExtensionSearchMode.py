import html

from ulauncher.api.server.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.api.server.ExtensionServer import ExtensionServer
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.api.server.ExtensionKeywordResultItem import ExtensionKeywordResultItem


class ExtensionSearchMode(BaseSearchMode):

    def __init__(self):
        self.extensionServer = ExtensionServer.get_instance()
        self.deferredResultRenderer = DeferredResultRenderer.get_instance()

    def is_enabled(self, query):
        """
        :param ~ulauncher.search.Query.Query query:
        :rtype: `True` if mode should be enabled for a query
        """
        return bool(self._get_controller_by_keyword(query.get_keyword())) and query.is_mode_active()

    def on_query_change(self, query):
        """
        Triggered when user changes a search query

        :param ~ulauncher.search.Query.Query query:
        """
        self.deferredResultRenderer.on_query_change()

    def handle_query(self, query):
        """
        :param ~ulauncher.search.Query.Query query:
        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction`
        """
        controller = self._get_controller_by_keyword(query.get_keyword())

        if not controller:
            raise Exception("Controller not found. (This line shouldn't be entered)")

        return controller.handle_query(query)

    def _get_controller_by_keyword(self, kw):
        """
        :param str kw: Keyword
        """
        return self.extensionServer.get_controller_by_keyword(kw)

    def get_searchable_items(self):
        """
        :rtype: list of :class:`~ulauncher.api.shared.item.ResultItem.ResultItem`
        """
        items = []
        for c in self.extensionServer.get_controllers():
            for pref in c.preferences.get_items(type='keyword'):
                if not pref['value']:
                    continue

                icon = c.manifest.load_icon(ExtensionKeywordResultItem.get_icon_size())
                items.append(ExtensionKeywordResultItem(name=html.escape(pref['name']),
                                                        description=html.escape(pref['description']),
                                                        keyword=pref['value'],
                                                        icon=icon))

        return items
