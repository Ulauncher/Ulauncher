import logging
from functools import partial
from threading import Timer
from ulauncher.helpers import singleton
from ulauncher.result_list.result_item.ResultItem import ResultItem
from ulauncher.result_list.item_action.RenderResultListAction import RenderResultListAction
from ulauncher.result_list.item_action.DoNothingAction import DoNothingAction
from ulauncher.extension.shared.event import KeywordQueryEvent, ItemEnterEvent

logger = logging.getLogger(__name__)


class DeferredResultRenderer(object):

    LOADING_DELAY = 0.5  # delay in sec before Loading... is rendered

    @classmethod
    @singleton
    def get_instance(cls):
        return cls()

    def __init__(self):
        self.loading = None
        self.active_event = None
        self.active_controller = None

    def get_active_controller(self):
        return self.active_controller

    def handle_event(self, event, controller):
        self._cancelLoading()
        self.loading = Timer(self.LOADING_DELAY,
                             partial(self._renderLoading,
                                     controller.get_manifest().load_icon(ResultItem.ICON_SIZE)))
        self.loading.start()
        self.active_event = event
        self.active_controller = controller

        return DoNothingAction()

    def handle_response(self, response, controller):
        if self.active_controller != controller or self.active_event != response.event:
            return

        self._cancelLoading()
        response.action.run()

    def on_query_change(self):
        self._cancelLoading()
        self.active_event = None
        self.active_controller = None

    def _cancelLoading(self):
        if self.loading:
            self.loading.cancel()
            self.loading = None

    def _renderLoading(self, icon):
        loading_item = ResultItem(name='Loading...',
                                  icon=icon,
                                  highlightable=False)
        RenderResultListAction([loading_item]).run()
