from __future__ import annotations

import logging
from typing import Any

from gi.repository import Gio

from ulauncher.api.result import Result
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.singleton import Singleton
from ulauncher.utils.timer import TimerContext, timer

logger = logging.getLogger()
events = EventBus()


class DeferredResultRenderer(metaclass=Singleton):
    """
    Handles asynchronous render for extensions
    """

    LOADING_DELAY = 0.3  # delay in sec before Loading... is rendered

    def __init__(self) -> None:
        self.loading: TimerContext | None = None
        self.active_event: dict[str, Any] | None = None
        self.active_controller: Any | None = None
        app = Gio.Application.get_default()
        assert app
        self.app = app

    def get_active_controller(
        self,
    ) -> Any | None:
        return self.active_controller

    def handle_event(self, event: dict[str, Any], controller: Any) -> bool:
        """
        Schedules "Loading..." message
        """
        icon = controller.data_controller.get_normalized_icon_path()
        loading_message = Result(name="Loading...", icon=icon)

        self._cancel_loading()
        self.loading = timer(self.LOADING_DELAY, lambda: events.emit("window:show_results", [loading_message]))
        self.active_event = event
        self.active_controller = controller

        return True

    def handle_response(self, response: dict[str, Any], controller: Any) -> None:
        """
        Calls :func:`response.action.run`
        """
        if self.active_controller != controller or self.active_event != response.get("event"):
            return

        self._cancel_loading()
        events.emit("window:handle_event", response.get("action"))

    def on_query_change(self) -> None:
        """
        Cancel "Loading...", reset active_event and active_controller
        """
        self._cancel_loading()
        self.active_event = None
        self.active_controller = None

    def _cancel_loading(self) -> None:
        if self.loading:
            self.loading.cancel()
            self.loading = None
