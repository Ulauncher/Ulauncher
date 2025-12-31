from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ulauncher.internals.action_input import convert_to_action_message
from ulauncher.internals.actions import ActionMessage
from ulauncher.utils.basedataclass import BaseDataClass

if TYPE_CHECKING:
    from ulauncher.internals.action_input import ActionMessageInput


class Result(BaseDataClass):
    """
    Use this class to define a result item to be displayed in response to a query or other event.
    Return `list[Result]` from the `on_input` or `on_item_enter` methods of the `Extension` subclass.

    :param actions: Optional dict of actions for this result. When provided, on_enter/on_alt_enter are ignored.
                    Format: {"action_id": {"name": "Display Name", "icon": "optional-icon-name"}}
    :param on_enter: The action to be performed when the result is activated (legacy: please use `actions` instead).
                     Should be a return value of the `ExtensionCustomAction` function.
    :param on_alt_enter: The action to be performed when the result is activated with the Alt key pressed
                         (legacy: please use `actions` instead).
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
    actions: dict[str, dict[Literal["name", "icon"], str]] = {}  #: dict of actions with display names and icons
    on_enter: ActionMessage | list[Result] | None = None
    on_alt_enter: ActionMessage | list[Result] | None = None

    def __init__(
        self,
        *,
        compact: bool | None = None,
        highlightable: bool | None = None,
        searchable: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        keyword: str | None = None,
        icon: str | None = None,
        actions: dict[str, dict[Literal["name", "icon"], str]] | None = None,
        on_enter: ActionMessageInput | None = None,
        on_alt_enter: ActionMessageInput | None = None,
        **kwargs: Any,
    ) -> None:
        # Build kwargs dict with all provided arguments
        # We have to do this until we can use typing.Unpack (py3.11)
        init_kwargs: dict[str, Any] = {}
        if compact is not None:
            init_kwargs["compact"] = compact
        if highlightable is not None:
            init_kwargs["highlightable"] = highlightable
        if searchable is not None:
            init_kwargs["searchable"] = searchable
        if name is not None:
            init_kwargs["name"] = name
        if description is not None:
            init_kwargs["description"] = description
        if keyword is not None:
            init_kwargs["keyword"] = keyword
        if icon is not None:
            init_kwargs["icon"] = icon
        if actions is not None:
            init_kwargs["actions"] = actions
        if on_enter is not None:
            init_kwargs["on_enter"] = on_enter
        if on_alt_enter is not None:
            init_kwargs["on_alt_enter"] = on_alt_enter
        # Add any additional kwargs
        init_kwargs.update(kwargs)
        super().__init__(**init_kwargs)

    def __setitem__(self, key: str, value: Any) -> None:
        if key in ["on_enter", "on_alt_enter"] and value is not None:
            value = convert_to_action_message(value)

        super().__setitem__(key, value)

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

    action_id = ""  # The action ID from the parent result's actions dict
    parent_result: Result | None = None  # Reference to the parent result


class KeywordTrigger(Result):
    searchable = True
