from __future__ import annotations

from typing import Any, Dict, List, Union

from ulauncher.internals.query import Query
from ulauncher.utils.basedataclass import BaseDataClass

"""
ActionMetadata describes the action to be performed by the Ulauncher app.
It can be a dict with any value that can be serialized to JSON.
"""
ActionMetadata = Union[List["Result"], Dict[str, Any], bool, str]


class Result(BaseDataClass):
    """
    Use this class to define a result item to be displayed in response to a query or other event.
    Return `list[Result]` from the `on_input` or `on_item_enter` methods of the `Extension` subclass.

    :param on_enter: The action to be performed when the result is activated.
                     Should be a return value of the `ExtensionCustomAction` function.
    :param on_alt_enter: The action to be performed when the result is activated with the Alt key pressed.
    """

    compact = False  #: If True, the result will be displayed in a single line without a title
    highlightable = False  #: If True, a substring matching the query will be highlighted
    searchable = False
    name = ""  #: The name of the result item
    description = ""  #: The description of the result item. Used only if `compact` is False
    keyword = ""
    icon = (
        ""  #: An icon path relative to the extension root. If not set, the default icon of the extension will be used
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def __setitem__(self, key: str, value: Any) -> None:
        if key in ["on_enter", "on_alt_enter"] and not isinstance(value, (bool, dict, str)):
            msg = f"Invalid {key} argument. Expected bool, dict or string"
            raise KeyError(msg)

        super().__setitem__(key, value)

    def get_keyword(self) -> str:
        return self.keyword

    def get_name(self) -> str:
        return self.name

    def get_icon(self) -> str | None:
        return self.icon

    def get_highlightable_input(self, query: Query) -> str | None:
        if not self.keyword or self.keyword == query.keyword:
            return query.argument
        return str(query)

    def get_searchable_fields(self) -> list[tuple[str, float]]:
        return [(self.name, 1.0), (self.description, 0.8)]

    def search_score(self, query_str: str) -> float:
        if not self.searchable:
            return 0
        from ulauncher.utils.fuzzy_search import get_score

        return max(get_score(query_str, field) * weight for field, weight in self.get_searchable_fields() if field)
