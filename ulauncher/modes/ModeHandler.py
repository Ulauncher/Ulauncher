from __future__ import annotations

import logging

from ulauncher.api.result import Result
from ulauncher.api.shared.query import Query
from ulauncher.modes.apps.AppMode import AppMode
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.calc.CalcMode import CalcMode
from ulauncher.modes.extensions.ExtensionMode import ExtensionMode
from ulauncher.modes.file_browser.FileBrowserMode import FileBrowserMode
from ulauncher.modes.shortcuts.ShortcutMode import ShortcutMode
from ulauncher.utils.singleton import Singleton

logger = logging.getLogger()


class ModeHandler(metaclass=Singleton):
    modes: list[BaseMode]

    def __init__(self):
        self.modes = [FileBrowserMode(), CalcMode(), ShortcutMode(), ExtensionMode(), AppMode()]

    def on_query_change(self, query: Query) -> bool | list[Result]:
        """
        Iterate over all search modes and run first enabled.
        """
        for _mode in self.modes:
            _mode.on_query_change(query)

        mode = self.get_mode_from_query(query)
        result = mode and mode.handle_query(query)
        # TODO(friday): Get rid of this (only used in DeferredResultRenderer.handle_event)
        if isinstance(result, bool):
            return result
        if result:
            return [*result]
        # No mode selected, which means search
        results = self.search(query)
        # If the search result is empty, add the default items for all other modes (only shortcuts currently)
        if not results and query:
            for mode in self.modes:
                results.extend(mode.get_fallback_results())
        return results

    def on_query_backspace(self, query: Query) -> str | None:
        mode = self.get_mode_from_query(query)
        if not mode:
            return None
        return mode.on_query_backspace(query)

    def get_mode_from_query(self, query: Query) -> BaseMode | None:
        for mode in self.modes:
            if mode.is_enabled(query):
                return mode
        return None

    def search(self, query: Query, min_score: int = 50, limit: int = 50) -> list[Result]:
        searchables: list[Result] = []
        for mode in self.modes:
            searchables.extend([*mode.get_triggers()])

        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        sorted_ = sorted(searchables, key=lambda i: i.search_score(query), reverse=True)[:limit]
        return list(filter(lambda searchable: searchable.search_score(query) > min_score, sorted_))
