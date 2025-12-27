from __future__ import annotations

from typing import Callable, Iterable

from ulauncher.internals.actions import ActionMessage
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result

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

    def handle_query(self, _query: Query, callback: Callable[[list[Result]], None]) -> None:
        """
        Handle a query and provide the result list via callback.
        """
        callback([])

    def get_placeholder_icon(self) -> str | None:
        """
        Returns icon for the placeholder result to show while waiting for async results.
        """
        return None

    def get_triggers(self) -> Iterable[Result]:
        return []

    def has_trigger_changes(self) -> bool:
        """
        Return True if this mode's triggers may need to be reloaded.
        Note that all triggers are reloaded when the Ulauncher window is shown,
        so this is mainly for modes that load trigger asynchronously and won't be ready initially.
        """
        return False

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

    def activate_result(
        self,
        result: Result,
        query: Query,
        alt: bool,
        callback: Callable[[ActionMessage | list[Result]], None],
    ) -> None:
        """
        Called when a result is activated.
        Override this method to handle the activation of a result.
        """
        error_msg = (
            f"{self.__class__.__name__}.activate_result() is not implemented. "
            "You should override this method to handle result activation."
        )
        raise NotImplementedError(error_msg)
