import logging
from functools import partial
from threading import Timer

from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.util.decorator.singleton import singleton

logger = logging.getLogger(__name__)


class DeferredResultRenderer(object):
    """
    Handles asynchronous render for extensions
    """

    LOADING_DELAY = 0.5  # delay in sec before Loading... is rendered

    @classmethod
    @singleton
    def get_instance(cls):
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
        Schedules "Loading..." message and returns :class:`~ulauncher.api.shared.action.DoNothingAction.DoNothingAction`
        """
        self._cancel_loading()
        self.loading = Timer(self.LOADING_DELAY,
                             partial(self._render_loading,
                                     controller.get_manifest().load_icon(ResultItem.ICON_SIZE)))
        self.loading.start()
        self.active_event = event
        self.active_controller = controller

        return DoNothingAction()

    def handle_response(self, response, controller):
        """
        Calls `response.action.run()`
        """
        if self.active_controller != controller or self.active_event != response.event:
            return

        self._cancel_loading()
        response.action.run()

    def on_query_change(self):
        """
        Cancels "Loading..."
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
