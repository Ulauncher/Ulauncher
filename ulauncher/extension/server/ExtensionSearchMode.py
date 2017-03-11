from functools import partial
from ulauncher.search.BaseSearchMode import BaseSearchMode
from ulauncher.extension.server.ExtensionServer import ExtensionServer
from ulauncher.extension.server.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.result_list.result_item.ResultItem import ResultItem
from ulauncher.result_list.item_action.SetUserQueryAction import SetUserQueryAction


class ExtensionSearchMode(BaseSearchMode):

    def __init__(self):
        self.extensionServer = ExtensionServer.get_instance()
        self.deferredResultRenderer = DeferredResultRenderer.get_instance()

    def is_enabled(self, query):
        """
        Return True if mode should be enabled for a query
        """
        return bool(self._get_controller_by_keyword(query.get_keyword())) and query.is_mode_active()

    def on_query_change(self, query):
        """
        Triggered when user changes a search query
        """
        self.deferredResultRenderer.on_query_change()

    def handle_query(self, query):
        """
        @return Action object
        """
        controller = self._get_controller_by_keyword(query.get_keyword())

        if not controller:
            raise RuntimeException("Controller not found. (This line shouldn't be entered)")

        return controller.handle_query(query)

    def _get_controller_by_keyword(self, kw):
        return self.extensionServer.get_controller_by_keyword(kw)

    def get_searchable_items(self):
        items = []
        for c in self.extensionServer.get_controllers():
            for pref in c.preferences.get_items(type='keyword'):
                if not pref['value']:
                    continue

                items.append(ResultItem(name=pref['name'],
                                        description=pref['description'],
                                        keyword=pref['value'],
                                        icon=c.manifest.load_icon(ResultItem.ICON_SIZE),
                                        on_enter=partial(self._on_item_enter, pref['value'])))

        return items

    def _on_item_enter(self, keyword, query):
        return SetUserQueryAction('%s ' % keyword)
