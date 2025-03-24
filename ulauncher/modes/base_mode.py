from __future__ import annotations

from typing import Iterable

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class BaseMode:
    def parse_query_str(self, _query_str: str) -> Query | None:
        """return a Query if the input should be handled by the mode, else None"""
        return None

    def handle_backspace(self, _query_str: str) -> str | None:
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
