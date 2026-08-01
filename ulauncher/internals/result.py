from __future__ import annotations

from typing import Literal

from ulauncher.data import BaseDataClass


class Result(BaseDataClass):
    """
    Use this class to define a result item to be displayed in response to a query or other event.
    Return `list[Result]` from the `on_input` or `on_item_enter` methods of the `Extension` subclass.

    :param actions: Optional dict of actions for this result.
                    Format: {"action_id": {"name": "Display Name", "icon": "optional-icon-name"}}
    """

    compact: bool = False  #: If True, the result will be displayed in a single line without a title
    wrap: bool = False  #: If True, name and description wrap over multiple lines instead of being ellipsized
    highlightable: bool = False  #: If True, a substring matching the query will be highlighted
    searchable: bool = False
    name: str = ""  #: The name of the result item
    description: str = ""  #: The description of the result item. Used only if `compact` is False
    keyword: str = ""
    #: An icon path relative to the extension root. If not set, the default icon of the extension will be used
    icon: str = ""
    actions: dict[str, dict[Literal["name", "icon"], str]] = {}  #: dict of actions with display names and icons

    def get_highlightable_input(self, query_str: str) -> str:
        return query_str

    def get_searchable_fields(self) -> list[tuple[str, float]]:
        return [(self.name, 1.0), (self.description, 0.8)]

    def search_score(self, query_str: str) -> float:
        if not self.searchable:
            return 0
        from ulauncher.utils.fuzzy_search import get_score

        return max(get_score(query_str, field) * weight for field, weight in self.get_searchable_fields() if field)


class ActionResult(Result):
    """
    Represents an action that can be performed on a parent result.
    Used internally when a Result has multiple actions defined.
    """

    action_id: str = ""  # The action ID from the parent result's actions dict
    parent_result: Result | None = None  # Reference to the parent result


class KeywordTrigger(Result):
    searchable: bool = True
