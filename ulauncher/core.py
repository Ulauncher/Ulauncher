from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable
from weakref import WeakKeyDictionary

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.utils.eventbus import EventBus

_events = EventBus()
logger = logging.getLogger()


@lru_cache(maxsize=None)
def get_app_mode() -> BaseMode:
    from ulauncher.modes.apps.app_mode import AppMode

    return AppMode()


@lru_cache(maxsize=None)
def get_modes() -> list[BaseMode]:
    from ulauncher.modes.calc.calc_mode import CalcMode
    from ulauncher.modes.extensions.extension_mode import ExtensionMode
    from ulauncher.modes.file_browser.file_browser_mode import FileBrowserMode
    from ulauncher.modes.shortcuts.shortcut_mode import ShortcutMode

    return [FileBrowserMode(), CalcMode(), ShortcutMode(), ExtensionMode(), get_app_mode()]


class UlauncherCore:
    """Core application logic to handle the query events and delegate them to the modes."""

    _mode: BaseMode | None = None
    _triggers: list[Result] = []
    _mode_map: WeakKeyDictionary[Result, BaseMode] = WeakKeyDictionary()
    _triggers_loaded: bool = False
    query: Query = Query(None, "")

    def load_triggers(self, force: bool = False) -> None:
        if self._triggers_loaded and not force:
            return

        self._triggers.clear()
        for mode in get_modes():
            for trigger in mode.get_triggers():
                self._triggers.append(trigger)
                self._mode_map[trigger] = mode
        self._triggers_loaded = True

    def update(self, query_str: str) -> None:
        """Parse the query string and update the mode and query."""
        if not query_str and not str(self.query):
            # prevent loading modes until the app has rendered initially when the query is empty
            # otherwise it will load all the slow stuff before the app is shown
            return

        self._mode = None
        self.query = Query(None, query_str)

        for mode in get_modes():
            if query := mode.parse_query_str(query_str):
                self._mode = mode
                self.query = query
                break

        self.handle_change()

    def search_triggers(self, min_score: int = 50, limit: int = 50) -> list[Result]:
        self.load_triggers()
        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        query_str = self.query.argument
        if not query_str:
            return []
        sorted_ = sorted(self._triggers, key=lambda i: i.search_score(query_str), reverse=True)[:limit]
        return list(filter(lambda searchable: searchable.search_score(query_str) > min_score, sorted_))

    def get_initial_results(self, limit: int) -> Iterable[Result]:
        """Called if the query is empty (on startup or when you delete the query)"""
        app_mode = get_app_mode()
        for app_result in app_mode.get_initial_results(limit):
            self._mode_map[app_result] = app_mode
            yield app_result

    def handle_change(self) -> None:
        from ulauncher.modes.mode_handler import handle_action

        if self._mode:
            try:
                handle_action(self._mode.handle_query(self.query))
            except Exception:
                logger.exception("Mode '%s' triggered an error while handling query '%s'", self._mode, self.query)
            return

        # No mode selected, which means search
        results = self.search_triggers()
        # If the search result is empty, add the default items for all other modes (only shortcuts currently)
        if not results and str(self.query):
            for mode in get_modes():
                for fallback_result in mode.get_fallback_results(str(self.query)):
                    results.append(fallback_result)
                    self._mode_map[fallback_result] = mode
        handle_action(results)

    def handle_backspace(self, query_str: str) -> bool:
        if self._mode:
            new_query = self._mode.handle_backspace(query_str)
            if new_query is not None:
                self.query = new_query
                _events.emit("app:set_query", str(new_query))
                return True
        return False

    def activate_result(self, result: Result, alt: bool = False) -> None:
        mode = self._mode_map.get(result, self._mode)
        if not mode:
            logger.warning("Cannot activate result '%s' because no mode is set", result)
            return

        from ulauncher.modes.mode_handler import handle_action

        handle_action(mode.activate_result(result, self.query, alt))
