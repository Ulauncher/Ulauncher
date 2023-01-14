import logging
from functools import lru_cache

from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.apps.AppMode import AppMode
from ulauncher.modes.shortcuts.ShortcutMode import ShortcutMode
from ulauncher.modes.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.modes.calc.CalcMode import CalcMode

logger = logging.getLogger()


class ModeHandler:
    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls):
        return cls([FileBrowserMode(), CalcMode(), ShortcutMode(), ExtensionMode(), AppMode()])

    def __init__(self, modes):
        self.modes = modes

    def on_query_change(self, query):
        """
        Iterate over all search modes and run first enabled.
        """
        for mode in self.modes:
            mode.on_query_change(query)

        mode = self.get_mode_from_query(query)
        if mode:
            action = mode.handle_query(query)
            if not isinstance(action, BaseAction):
                action = RenderResultListAction(action)
            action.run()
        else:
            # No mode selected, which means search
            results = self.search(query)
            # If the search result is empty, add the default items for all other modes (only shortcuts currently)
            if not results and query:
                for mode in self.modes:
                    results.extend(mode.get_fallback_results())
            RenderResultListAction(results).run()

    def on_key_press_event(self, widget, event, query):
        # This is used for FileBrowserMode to make backspace delete the entire "word"
        mode = self.get_mode_from_query(query)
        if mode:
            mode.handle_key_press_event(widget, event, query).run()

    def get_mode_from_query(self, query):
        for mode in self.modes:
            if mode.is_enabled(query):
                return mode
        return None

    def search(self, query, min_score=50, limit=50):
        searchables = []
        for mode in self.modes:
            searchables.extend(list(mode.get_triggers()))

        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        sorted_ = sorted(searchables, key=lambda i: i.search_score(query), reverse=True)[:limit]
        return list(filter(lambda searchable: searchable.search_score(query) > min_score, sorted_))
