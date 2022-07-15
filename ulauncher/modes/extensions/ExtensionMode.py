import html

from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.extensions.ExtensionKeywordResult import ExtensionKeywordResult
from ulauncher.api.shared.query import Query
from ulauncher.api.shared.action.BaseAction import BaseAction


class ExtensionMode(BaseMode):

    def __init__(self):
        self.extensionServer = ExtensionServer.get_instance()
        self.deferredResultRenderer = DeferredResultRenderer.get_instance()

    def is_enabled(self, query: Query):
        return bool(self.extensionServer.get_controller_by_keyword(query.keyword)) and " " in query

    def on_query_change(self, query: Query):
        """
        Triggered when user changes the query
        """
        self.deferredResultRenderer.on_query_change()

    def handle_query(self, query: Query) -> BaseAction:
        controller = self.extensionServer.get_controller_by_keyword(query.keyword)

        if not controller:
            raise Exception("Controller not found. (This line shouldn't be entered)")

        return controller.handle_query(query)

    def get_triggers(self):
        """
        :rtype: Iterable[:class:`~ulauncher.api.Result`]
        """
        for controller in self.extensionServer.get_controllers():
            for pref in controller.manifest.preferences.values():
                if pref.type == "keyword" and pref.value:
                    yield ExtensionKeywordResult(
                        name=html.escape(pref.name),
                        description=html.escape(pref.description),
                        keyword=pref.value,
                        icon=controller.get_icon_path(path=pref.icon)
                    )
