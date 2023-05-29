import logging
from functools import lru_cache

from gi.repository import Gio, GLib

from ulauncher.api.result import Result
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.utils.timer import timer

logger = logging.getLogger()


class DeferredResultRenderer:
    """
    Handles asynchronous render for extensions
    """

    LOADING_DELAY = 0.3  # delay in sec before Loading... is rendered

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls) -> "DeferredResultRenderer":
        """
        Returns singleton instance
        """
        return cls()

    def __init__(self):
        self.loading = None
        self.active_event = None
        self.active_controller = None
        self.app = Gio.Application.get_default()

    def get_active_controller(self):
        return self.active_controller

    def handle_event(self, event, controller):
        """
        Schedules "Loading..." message
        """
        icon = controller.get_normalized_icon_path()
        loading_message = Result(name="Loading...", icon=icon)

        self._cancel_loading()
        self.loading = timer(self.LOADING_DELAY, GLib.idle_add(self.app.window.show_results, [loading_message]))
        self.active_event = event
        self.active_controller = controller

        return True

    def handle_response(self, response, controller):
        """
        Calls :func:`response.action.run`
        """
        if self.active_controller != controller or self.active_event != response.event:
            return

        self._cancel_loading()
        action = response.action
        if isinstance(action, BaseAction):
            action.run()
            if not action.keep_app_open:
                self._hide_window()
        if isinstance(action, list):
            GLib.idle_add(self.app.window.show_results, action)
        if isinstance(action, str):
            self.app.query = action
        if str is False:
            self._hide_window()

    def on_query_change(self):
        """
        Cancel "Loading...", reset active_event and active_controller
        """
        self._cancel_loading()
        self.active_event = None
        self.active_controller = None

    def _cancel_loading(self):
        if self.loading:
            self.loading.cancel()
            self.loading = None

    def _hide_window(self):
        if self.app and hasattr(self.app, "window") and self.app.window.is_visible():
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(self.app.window.hide_and_clear_input)
