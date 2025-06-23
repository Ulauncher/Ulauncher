from __future__ import annotations

import logging

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.utils.eventbus import EventBus

_events = EventBus("query")
logger = logging.getLogger()


class QueryHandler:
    mode: BaseMode | None = None
    query: Query = Query(None, "")
    triggers: list[Result] = []
    trigger_mode_map: dict[int, BaseMode] = {}

    def __init__(self) -> None:
        self.reload_triggers()

    def reload_triggers(self) -> None:
        from ulauncher.modes.mode_handler import get_modes

        self.triggers.clear()
        self.trigger_mode_map.clear()
        for mode in get_modes():
            for trigger in mode.get_triggers():
                self.triggers.append(trigger)
                self.trigger_mode_map[id(trigger)] = mode

    def parse(self, query_str: str) -> None:
        self.mode = None
        self.query = Query(None, query_str)

        from ulauncher.modes.mode_handler import get_modes

        for mode in get_modes():
            query = mode.parse_query_str(query_str)
            if query:
                self.mode = mode
                self.query = query

    def search_triggers(self, min_score: int = 50, limit: int = 50) -> list[Result]:
        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        query_str = self.query.argument
        if not query_str:
            return []
        sorted_ = sorted(self.triggers, key=lambda i: i.search_score(query_str), reverse=True)[:limit]
        return list(filter(lambda searchable: searchable.search_score(query_str) > min_score, sorted_))

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
        if not results and self.query:
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
