import html

from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.extensions.ExtensionKeywordResult import ExtensionKeywordResult


class ExtensionMode(BaseMode):

    def __init__(self):
        self.extensionServer = ExtensionServer.get_instance()
        self.deferredResultRenderer = DeferredResultRenderer.get_instance()

    def is_enabled(self, query):
        """
        :param ~ulauncher.modes.Query.Query query:
        :rtype: `True` if mode should be enabled for a query
        """
        return bool(self._get_controller_by_keyword(query.get_keyword())) and " " in query

    def on_query_change(self, query):
        """
        Triggered when user changes a search query

        :param ~ulauncher.modes.Query.Query query:
        """
        self.deferredResultRenderer.on_query_change()

    def handle_query(self, query):
        """
        :param ~ulauncher.modes.Query.Query query:
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
        :rtype: list of :class:`~ulauncher.api.Result`
        """
        items = []
        for controller in self.extensionServer.get_controllers():
            for pref in controller.preferences.get_items(type='keyword'):
                if pref['value']:
                    icon_size = ExtensionKeywordResult.get_icon_size()
                    items.append(ExtensionKeywordResult(
                        name=html.escape(pref['name']),
                        description=html.escape(pref['description']),
                        keyword=pref['value'],
                        icon=controller.manifest.load_icon(icon_size, path=pref['icon'])
                    ))

        return items
