from __future__ import annotations

from typing import Iterable

from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result

DEFAULT_ACTION = True  #  keep window open and do nothing


class BaseMode:
    def matches_query_str(self, _query_str: str) -> bool:
        """
        Return if the input should be handled by the mode
        """
        return False

    def handle_backspace(self, _query_str: str) -> Query | None:
        """
        Return string to override default backspace and set the query to that string
        """
        return None

    def handle_query(self, _query: Query) -> Iterable[Result] | None:
        """
        Return the new results for the given query, or None to keep the current results (for asynchronous handling)
        """
        return []

    def get_triggers(self) -> Iterable[Result]:
        return []

    def get_initial_results(self, _limit: int) -> Iterable[Result]:
        """
        Called if the query is empty (on startup or when you delete the query)
        We only actually use this for AppMode, so it should not be implemented for other modes.
        """
        return []

    def get_fallback_results(self, _query_str: str) -> Iterable[Result]:
        """
        Called if nothing matches the user input
        """
        return []

    def activate_result(self, result: Result, query: Query, alt: bool) -> ActionMetadata:
        """
        Called when a result is activated.
        Override this method to handle the activation of a result.
        """
        error_msg = (
            f"{self.__class__.__name__}.activate_result() is not implemented. "
            "You should override this method to handle result activation."
        )
        raise NotImplementedError(error_msg)
