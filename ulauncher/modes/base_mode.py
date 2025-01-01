from __future__ import annotations

from typing import Iterable

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class BaseMode:
    def is_enabled(self, _query: Query) -> bool:
        """
        Return True if mode should be enabled for a query
        """
        return False

    def on_query_backspace(self, _query: Query) -> str | None:
        """
        Return string to override default backspace and set the query to that string
        """
        return None

    def handle_query(self, _query: Query) -> Iterable[Result]:
        return []

    def get_triggers(self) -> Iterable[Result]:
        return []

    def get_fallback_results(self) -> Iterable[Result]:
        """
        If nothing matches the user input
        """
        return []
