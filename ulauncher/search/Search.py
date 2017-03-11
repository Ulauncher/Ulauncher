import logging
from ulauncher.helpers import singleton
from ulauncher.search.apps.AppSearchMode import AppSearchMode
from ulauncher.search.shortcuts.ShortcutSearchMode import ShortcutSearchMode
from ulauncher.search.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.search.calc.CalcMode import CalcMode
from ulauncher.extension.server.ExtensionSearchMode import ExtensionSearchMode

logger = logging.getLogger(__name__)


class Search(object):

    @classmethod
    @singleton
    def get_instance(cls):
        fileBrowserMode = FileBrowserMode()
        calcMode = CalcMode()
        shortcutSearchMode = ShortcutSearchMode()
        extensionSearchMode = ExtensionSearchMode()
        appSearchMode = AppSearchMode([shortcutSearchMode, extensionSearchMode])
        return cls([fileBrowserMode,
                    calcMode,
                    shortcutSearchMode,
                    extensionSearchMode,
                    appSearchMode])

    def __init__(self, search_modes):
        self.search_modes = search_modes

    def on_query_change(self, query):
        """
        Iterate over all search modes and run first enabled.
        AppSearchMode is always enabled
        """
        logger.warning('query changed to "%s"' % query)
        for mode in self.search_modes:
            mode.on_query_change(query)

        self._choose_search_mode(query).handle_query(query).run()

    def on_key_press_event(self, widget, event, query):
        self._choose_search_mode(query).handle_key_press_event(widget, event, query).run()

    def _choose_search_mode(self, query):
        for mode in self.search_modes:
            if mode.is_enabled(query):
                return mode

        raise Exception('This line should not be entered')
