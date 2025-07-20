from __future__ import annotations

import logging
from typing import Sequence

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.apps.app_mode import AppMode
from ulauncher.modes.base_mode import BaseMode
from ulauncher.utils.eventbus import EventBus

logger = logging.getLogger()
_events = EventBus("query")
logger = logging.getLogger()


class QueryHandler:
    mode: BaseMode | None = None
    query: Query = Query(None, "")
    triggers: list[Result] = []
    trigger_mode_map: dict[int, BaseMode] = {}
    triggers_loaded: bool = False

    def load_triggers(self, force: bool = False) -> None:
        if self.triggers_loaded and not force:
            return

        from ulauncher.modes.mode_handler import get_modes

        self.triggers.clear()
        self.trigger_mode_map.clear()
        for mode in get_modes():
            for trigger in mode.get_triggers():
                self.triggers.append(trigger)
                self.trigger_mode_map[id(trigger)] = mode
        self.triggers_loaded = True

    def update(self, query_str: str) -> None:
        """Parse the query string and update the mode and query."""
        if not query_str and not str(self.query):
            # prevent loading modes until the app has rendered initially when the query is empty
            # otherwise it will load all the slow stuff before the app is shown
            return

        self.mode = None
        self.query = Query(None, query_str)

        from ulauncher.modes.mode_handler import get_modes

        for mode in get_modes():
            if query := mode.parse_query_str(query_str):
                self.mode = mode
                self.query = query

        self.handle_change()

    def search_triggers(self, min_score: int = 50, limit: int = 50) -> list[Result]:
        self.load_triggers()
        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        query_str = self.query.argument
        if not query_str:
            return []
        sorted_ = sorted(self.triggers, key=lambda i: i.search_score(query_str), reverse=True)[:limit]
        return list(filter(lambda searchable: searchable.search_score(query_str) > min_score, sorted_))

    def get_most_frequent_apps(self, limit: int) -> Sequence[Result]:
        """Called if the query is empty (on startup or when you delete the query)"""
        app_mode = AppMode()
        top_apps = AppMode.get_most_frequent(limit)
        for app in top_apps:
            self.trigger_mode_map[id(app)] = app_mode

        return top_apps

    def handle_change(self) -> None:
        from ulauncher.modes.mode_handler import get_modes, handle_action

        if self.mode:
            try:
                handle_action(self.mode.handle_query(self.query))
            except Exception:
                logger.exception("Mode '%s' triggered an error while handling query '%s'", self.mode, self.query)
            return

        # No mode selected, which means search
        results = self.search_triggers()
        # If the search result is empty, add the default items for all other modes (only shortcuts currently)
        if not results and str(self.query):
            for mode in get_modes():
                res = mode.get_fallback_results()
                results.extend(res)
        handle_action(results)

    def handle_backspace(self, query_str: str) -> bool:
        if self.mode:
            new_query = self.mode.handle_backspace(query_str)
            if new_query is not None:
                self.query = new_query
                _events.emit("app:set_query", str(new_query))
                return True
        return False

    def activate_result(self, result: Result, alt: bool = False) -> None:
        mode = self.trigger_mode_map.get(id(result), self.mode)
        if not mode:
            logger.warning("Cannot activate result '%s' because no mode is set", result)
            return

        from ulauncher.modes.mode_handler import handle_action

        handle_action(mode.activate_result(result, self.query, alt))
