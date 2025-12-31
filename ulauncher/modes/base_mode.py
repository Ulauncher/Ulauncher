from __future__ import annotations

from typing import Callable, Iterable

from ulauncher.internals.actions import ActionMessage
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result

DEFAULT_ACTION = True  #  keep window open and do nothing


class BaseMode:
    def matches_query_str(self, _query_str: str) -> bool:
        """
        Returns if the input should be handled by the mode.
        """
        return False

    def handle_backspace(self, _query_str: str) -> Query | None:
        """
        Returns a query if it should override default backspace behavior.
        """
        return None

    def handle_query(self, _query: Query, callback: Callable[[ActionMessage | list[Result]], None]) -> None:
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
        Returns True if this mode's triggers may need to be reloaded.
        Note that all triggers are reloaded when the Ulauncher window is shown,
        so this is mainly for modes that load trigger asynchronously and won't be ready initially.
        """
        return False

    def get_initial_results(self, _limit: int) -> Iterable[Result]:
        """
        Get results to show when there is no query input (on startup or when you delete the query)
        Only implemented for AppMode.
        """
        return []

    def get_fallback_results(self, _query_str: str) -> Iterable[Result]:
        return []

    def activate_result(
        self,
        result: Result,
        query: Query,
        alt: bool,
        callback: Callable[[ActionMessage | list[Result]], None],
    ) -> None:
        error_msg = (
            f"{self.__class__.__name__}.activate_result() is not implemented. "
            "You should override this method to handle result activation."
        )
        raise NotImplementedError(error_msg)
