from __future__ import annotations

import logging
from typing import Callable, Iterator

from ulauncher.internals import effects
from ulauncher.internals.query import Query
from ulauncher.internals.result import KeywordTrigger, Result
from ulauncher.modes.mode import Mode
from ulauncher.modes.shortcuts import results
from ulauncher.modes.shortcuts.run_shortcut import run_shortcut
from ulauncher.modes.shortcuts.shortcuts_db import Shortcut, ShortcutsDb

logger = logging.getLogger()


def get_description(shortcut: Shortcut, query: Query | None = None) -> str:
    description = "" if shortcut.cmd.startswith("#!") else shortcut.cmd
    if query and query.keyword == shortcut.keyword:
        if not query.argument:
            return "Type in your query and press Enter..."
        return description.replace("%s", query.argument)
    return description.replace("%s", str(query) if query else "...")


def convert_to_result(shortcut: Shortcut, query: Query | None = None) -> results.ShortcutResult:
    description = get_description(shortcut, query)
    return (
        results.StaticShortcutResult(**shortcut, description=description)
        if shortcut.run_without_argument
        else results.ShortcutResult(**shortcut, description=description)
    )


class ShortcutMode(Mode):
    shortcuts_db: dict[str, Shortcut]

    def __init__(self) -> None:
        self.shortcuts_db = ShortcutsDb.load()

    def _get_active_shortcut(self, query: Query) -> Shortcut | None:
        for s in self.shortcuts_db.values():
            if query.keyword == s.keyword and (query.is_active or s.run_without_argument):
                return s

        return None

    def handle_query(self, query: Query, callback: Callable[[effects.EffectMessage | list[Result]], None]) -> None:
        shortcut = self._get_active_shortcut(query)
        if not shortcut:
            msg = "Query doesn't match any shortcut"
            raise RuntimeError(msg)

        callback([convert_to_result(shortcut, query)])

    def get_fallback_results(self, query_str: str) -> list[results.ShortcutResult]:
        query = Query(None, query_str)
        return [convert_to_result(s, query) for s in self.shortcuts_db.values() if s["is_default_search"]]

    def get_triggers(self) -> Iterator[Result]:
        for shortcut in self.shortcuts_db.values():
            yield (
                results.ShortcutStaticTrigger(**shortcut, description=get_description(shortcut))
                if shortcut.run_without_argument
                else KeywordTrigger(**shortcut, description=get_description(shortcut))
            )

    def activate_result(
        self,
        action_id: str,
        result: Result,
        query: Query,
        callback: Callable[[effects.EffectMessage | list[Result]], None],
    ) -> None:
        if action_id == "run_static":
            callback(run_shortcut(result.cmd))
        elif action_id == "run":
            # for fallback results (no keyword match) then the full query is the argument
            argument = query.argument or "" if query.keyword == result.keyword else str(query)
            if argument:
                callback(run_shortcut(result.cmd, argument))
            else:
                callback(effects.do_nothing())
        else:
            logger.error("Unexpected action '%s' for Shortcut mode result '%s'", action_id, result)
            callback(effects.do_nothing())
