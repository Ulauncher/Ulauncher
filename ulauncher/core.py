from __future__ import annotations

import itertools
import logging
from collections import defaultdict
from functools import lru_cache
from typing import Callable, Iterable
from weakref import WeakKeyDictionary

from ulauncher.internals.actions import ActionMessage
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.timer import TimerContext, timer

_events = EventBus()
logger = logging.getLogger()

PLACEHOLDER_DELAY = 0.3  # delay in sec before Loading... is rendered


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
    _keyword_cache: defaultdict[BaseMode, dict[str, Result]] = defaultdict(dict)
    _trigger_cache: defaultdict[BaseMode, list[Result]] = defaultdict(list)
    _mode_map: WeakKeyDictionary[Result, BaseMode] = WeakKeyDictionary()
    query: Query = Query(None, "")
    _placeholder_timer: TimerContext | None = None

    def load_triggers(self, force: bool = False) -> None:
        """Load or refresh triggers from modes that have changes."""
        claimed_keywords: dict[str, Result] = {}
        outdated_modes: set[BaseMode] = set()

        # load claimed keywords and modes that need to be refreshed
        for mode in get_modes():
            if force or mode.has_trigger_changes():
                outdated_modes.add(mode)
            else:
                claimed_keywords.update(self._keyword_cache[mode])

        for mode in outdated_modes:
            triggers = self._trigger_cache[mode]
            keywords = self._keyword_cache[mode]
            triggers.clear()
            keywords.clear()

            for trigger in mode.get_triggers():
                triggers.append(trigger)
                self._mode_map[trigger] = mode
                if trigger.keyword:
                    if trigger.keyword not in claimed_keywords:
                        keywords[trigger.keyword] = trigger
                        claimed_keywords[trigger.keyword] = trigger
                    else:
                        current_trigger = claimed_keywords[trigger.keyword]
                        logger.warning(
                            'Cannot register keyword "%s" for "%s" (%s). It is already used by "%s" (%s).',
                            trigger.keyword,
                            trigger.name,
                            trigger.__class__.__name__,
                            current_trigger.name,
                            current_trigger.__class__.__name__,
                        )

    def update(self, query_str: str, callback: Callable[[Iterable[Result]], None]) -> None:
        """Parse the query string and update the mode and query."""
        if not query_str and not str(self.query):
            # prevent loading modes until the app has rendered initially when the query is empty
            # otherwise it will load all the slow stuff before the app is shown
            return

        self._mode = None
        self.query = Query(None, query_str)

        # keyword match
        keyword, argument = query_str.split(" ", 1) if " " in query_str else (query_str, None)

        for mode, keywords in self._keyword_cache.items():
            if keyword in keywords and argument is not None:
                self._mode = mode
                self.query = Query(keyword, argument)
                break

        # non-keyword match
        if not self._mode:
            for mode in get_modes():
                if mode.matches_query_str(query_str):
                    self._mode = mode
                    self.query = Query(None, query_str)
                    break

        self.handle_change(callback)

    def search_triggers(self, min_score: int = 50, limit: int = 50) -> list[Result]:
        self.load_triggers()
        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        query_str = self.query.argument
        if not query_str:
            return []

        flattened_ = itertools.chain.from_iterable(self._trigger_cache.values())
        sorted_ = sorted(flattened_, key=lambda i: i.search_score(query_str), reverse=True)[:limit]
        return list(filter(lambda searchable: searchable.search_score(query_str) > min_score, sorted_))

    def get_initial_results(self, limit: int) -> Iterable[Result]:
        """Called if the query is empty (on startup or when you delete the query)"""
        app_mode = get_app_mode()
        for app_result in app_mode.get_initial_results(limit):
            self._mode_map[app_result] = app_mode
            yield app_result

    def _show_results(self, results: Iterable[Result], callback: Callable[[Iterable[Result]], None]) -> None:
        self._clear_placeholder_timer()
        callback(results)

    def _show_placeholder(self, callback: Callable[[Iterable[Result]], None]) -> None:
        placeholder = Result(name="Loading...", icon=self._mode.get_placeholder_icon() if self._mode else None)
        self._show_results([placeholder], callback)

    def _clear_placeholder_timer(self) -> None:
        if self._placeholder_timer:
            self._placeholder_timer.cancel()
            self._placeholder_timer = None

    def handle_change(self, callback: Callable[[Iterable[Result]], None]) -> None:
        self._clear_placeholder_timer()

        mode = self._mode

        def results_callback(results: list[Result]) -> None:
            # Ensure the mode hasn't changed
            if self._mode == mode:
                self._show_results(results, callback)

        if self._mode:
            try:
                self._placeholder_timer = timer(PLACEHOLDER_DELAY, lambda: self._show_placeholder(callback))

                self._mode.handle_query(self.query, results_callback)
            except Exception:
                # Mode handlers can raise any exception - catch broadly to prevent crashes
                logger.exception("Mode '%s' triggered an error while handling query '%s'", self._mode, self.query)
                self._clear_placeholder_timer()
            return

        # No mode selected, which means search
        results = self.search_triggers()
        # If the search result is empty, add the default items for all other modes (only shortcuts currently)
        if not results and str(self.query):
            for mode in get_modes():
                for fallback_result in mode.get_fallback_results(str(self.query)):
                    results.append(fallback_result)
                    self._mode_map[fallback_result] = mode

        result_objects = [res if isinstance(res, Result) else Result(**res) for res in results]
        callback(result_objects)

    def handle_backspace(self, query_str: str) -> bool:
        if self._mode:
            new_query = self._mode.handle_backspace(query_str)
            if new_query is not None:
                self.query = new_query
                _events.emit("app:set_query", str(new_query))
                return True
        return False

    def activate_result(self, result: Result, callback: Callable[[Iterable[Result]], None], alt: bool = False) -> None:
        mode = self._mode_map.get(result, self._mode)
        if not mode:
            logger.warning("Cannot activate result '%s' because no mode is set", result)
            return

        from ulauncher.modes.mode_handler import handle_action

        def mode_callback(action_msg: ActionMessage | list[Result]) -> None:
            if isinstance(action_msg, list):
                self._show_results(action_msg, callback)
                return

            handle_action(action_msg)

        mode.activate_result(result, self.query, alt, mode_callback)
