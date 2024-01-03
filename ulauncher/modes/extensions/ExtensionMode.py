import html
from typing import Any

from ulauncher.api.result import Result
from ulauncher.api.shared.query import Query
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionSocketServer import ExtensionSocketServer


class ExtensionMode(BaseMode):
    def __init__(self):
        self.ExtensionSocketServer = ExtensionSocketServer.get_instance()
        self.deferredResultRenderer = DeferredResultRenderer.get_instance()

    def is_enabled(self, query: Query) -> bool:
        return bool(self.ExtensionSocketServer.get_controller_by_keyword(query.keyword)) and " " in query

    def on_query_change(self, _query: Query) -> None:
        """
        Triggered when user changes the query
        """
        self.deferredResultRenderer.on_query_change()

    def handle_query(self, query: Query) -> Any:
        controller = self.ExtensionSocketServer.get_controller_by_keyword(query.keyword)

        if not controller:
            msg = "Invalid extension keyword"
            raise RuntimeError(msg)

        return controller.handle_query(query)

    def get_triggers(self):
        """
        :rtype: Iterable[:class:`~ulauncher.api.result.Result`]
        """
        for controller in self.ExtensionSocketServer.controllers.values():
            data_controller = controller.data_controller
            for trigger_id, trigger in controller.manifest.triggers.items():
                action: Any = None
                if trigger.keyword is None:
                    action = {
                        "type": "event:launch_trigger",
                        "args": [trigger_id],
                        "ext_id": controller.extension_id,
                    }
                elif trigger.user_keyword:
                    action = f"{trigger.user_keyword} "

                if action:
                    yield Result(
                        name=html.escape(trigger.name),
                        description=html.escape(trigger.description),
                        icon=data_controller.get_normalized_icon_path(trigger.icon),
                        on_enter=action,
                        searchable=True,
                    )
