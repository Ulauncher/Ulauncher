import logging
from functools import partial
from threading import Timer
import gi
gi.require_version('GLib', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import GLib

from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.utils.decorator.singleton import singleton

logger = logging.getLogger('DeferredResultRenderer')


class DeferredResultRenderer:
    """
    Handles asynchronous render for extensions
    """

    LOADING_DELAY = 0.3  # delay in sec before Loading... is rendered

    @classmethod
    @singleton
    def get_instance(cls) -> 'DeferredResultRenderer':
        """
        Returns singleton instance
        """
        return cls()

    def __init__(self):
        self.loading = None
        self.active_event = None
        self.active_controller = None

    def get_active_controller(self):
        return self.active_controller

    def handle_event(self, event, controller):
        """
        Schedules "Loading..." message

        :rtype: :class:`~ulauncher.api.shared.action.DoNothingAction.DoNothingAction`
        """
        self._cancel_loading()
        self.loading = Timer(self.LOADING_DELAY,
                             partial(self._render_loading,
                                     controller.get_manifest().load_icon(ResultItem.get_icon_size())))
        self.loading.start()
        self.active_event = event
        self.active_controller = controller

        return DoNothingAction()

    def handle_response(self, response, controller):
        """
        Calls :func:`response.action.run`
        """
        if self.active_controller != controller or self.active_event != response.event:
            return

        self._cancel_loading()
        response.action.run()
        if not response.action.keep_app_open():
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

    def _render_loading(self, icon):
        loading_item = ResultItem(name='Loading...',
                                  icon=icon,
                                  highlightable=False)
        RenderResultListAction([loading_item]).run()

    def _hide_window(self):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow

        window = UlauncherWindow.get_instance()
        if window.is_visible():
            # update UI in the main thread to avoid race conditions
            GLib.idle_add(window.hide_and_clear_input)
