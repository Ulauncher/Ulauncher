from __future__ import annotations

import html
from typing import Any, Generator

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.modes.extensions.extension_socket_server import ExtensionSocketServer
from ulauncher.utils.eventbus import EventBus

events = EventBus("extension_mode")
ExtensionSocketServer().start()


class ExtensionMode(BaseMode):
    def __init__(self) -> None:
        self.ext_socket_server = ExtensionSocketServer()
        self.active_ext_id: str | None = None
        events.set_self(self)

    def is_enabled(self, query: Query) -> bool:
        return bool(self.ext_socket_server.get_controller_by_keyword(query.keyword)) and " " in query

    def handle_query(self, query: Query) -> Any:
        events.emit("extension:on_query_change")
        controller = self.ext_socket_server.get_controller_by_keyword(query.keyword)

        if not controller:
            msg = "Invalid extension keyword"
            raise RuntimeError(msg)

        self.active_ext_id = controller.ext_id
        return controller.handle_query(query)

    @events.on
    def handle_action(self, action: bool | list[Any] | str | dict[str, Any] | None) -> None:
        if self.active_ext_id and isinstance(action, list):
            controller = ExtensionController(self.active_ext_id)
            for result in action:
                result["icon"] = controller.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action]
            events.emit("window:show_results", results)
        else:
            events.emit("mode:handle_action", action)

    def get_triggers(self) -> Generator[Result, None, None]:
        for controller in self.ext_socket_server.controllers.values():
            data_controller = controller.data_controller
            for trigger_id, trigger in data_controller.user_triggers.items():
                action: Any = None
                if not trigger.keyword:
                    action = {
                        "type": "event:launch_trigger",
                        "args": [trigger_id],
                        "ext_id": controller.ext_id,
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
