from __future__ import annotations

import html
from typing import Any, Iterator

from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_socket_server import ExtensionSocketServer
from ulauncher.utils.eventbus import EventBus

DEFAULT_ACTION = True  #  keep window open and do nothing
events = EventBus("extension_mode")


class ExtensionMode(BaseMode):
    def __init__(self) -> None:
        self.ext_socket_server = ExtensionSocketServer()
        ExtensionSocketServer().start()
        self.active_ext_id: str | None = None
        events.set_self(self)

    def parse_query_str(self, query_str: str) -> Query | None:
        query = Query.parse_str(query_str)
        if query.keyword and query.is_active:
            controller = self.ext_socket_server.get_controller_by_keyword(query.keyword)
            if controller:
                return query
        return None

    def handle_query(self, query: Query) -> Any:
        if query.keyword:
            events.emit("extension:on_query_change")
            controller = self.ext_socket_server.get_controller_by_keyword(query.keyword)

        if not controller:
            msg = f"Query not valid for extension mode {query}"
            raise RuntimeError(msg)

        self.active_ext_id = controller.ext_id
        return controller.handle_query(query)

    @events.on
    def handle_action(self, action_metadata: ActionMetadata | None) -> None:
        if self.active_ext_id and isinstance(action_metadata, list):
            controller = ExtensionController(self.active_ext_id)
            for result in action_metadata:
                result["icon"] = controller.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action_metadata]
            events.emit("window:show_results", results)
        else:
            events.emit("mode:handle_action", action_metadata)

    def get_triggers(self) -> Iterator[Result]:
        for ext in ExtensionController.iterate():
            for trigger_id, trigger in ext.user_triggers.items():
                action: Any = None
                if not trigger.keyword:
                    action = {
                        "type": "event:launch_trigger",
                        "args": [trigger_id],
                        "ext_id": ext.id,
                    }
                elif trigger.user_keyword:
                    action = f"{trigger.user_keyword} "

                if action:
                    yield Result(
                        name=html.escape(trigger.name),
                        description=html.escape(trigger.description),
                        icon=ext.get_normalized_icon_path(trigger.icon),
                        on_enter=action,
                        searchable=True,
                    )

    def activate_result(self, result: Result, query: Query, alt: bool) -> ActionMetadata:
        """
        Called when a result is activated.
        Override this method to handle the activation of a result.
        """
        handler = getattr(result, "on_alt_enter" if alt else "on_enter", DEFAULT_ACTION)
        return handler(query) if callable(handler) else handler
