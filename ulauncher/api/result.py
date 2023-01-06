import os
from typing import Callable, Optional
from ulauncher.utils.fuzzy_search import get_score
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.query import Query

OnEnterCallback = Optional[Callable[[Query], Optional[BaseAction]]]


# pylint: disable=too-many-instance-attributes
class Result:
    compact = False
    highlightable = False
    searchable = False
    name: str = ""
    description: str = ""
    keyword: str = ""
    icon: Optional[str] = None
    _on_enter: Optional[OnEnterCallback] = None
    _on_alt_enter: Optional[OnEnterCallback] = None

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        name: str = "",
        description: str = "",
        keyword: str = "",
        icon: str = "",
        highlightable: bool = False,
        on_enter: OnEnterCallback = None,
        on_alt_enter: OnEnterCallback = None,
        searchable: Optional[bool] = None,
        compact: Optional[bool] = None,
    ):
        if not isinstance(name, str):
            raise TypeError(f'"name" must be of type "str", "{type(name).__name__}" given.')
        if not isinstance(description, str):
            raise TypeError(f'"description" must be of type "str", "{type(description).__name__}" given.')
        if not isinstance(keyword, str):
            raise TypeError(f'"keyword" must be of type "str", "{type(keyword).__name__}" given.')
        self.name = name
        self.description = description
        self.keyword = keyword
        self.icon = icon
        if compact is not None:
            self.compact = compact
        if searchable is not None:
            self.searchable = searchable
        if highlightable is not None:
            self.highlightable = highlightable
        self._on_enter = on_enter
        self._on_alt_enter = on_alt_enter

        # This part only runs when initialized from an extensions
        ext_path = os.environ.get("EXTENSION_PATH")
        if ext_path:
            if not self.icon:
                self.icon = os.environ.get("EXTENSION_ICON")
            if self.icon and os.path.isfile(f"{ext_path}/{self.icon}"):
                self.icon = f"{ext_path}/{self.icon}"

            if self._on_enter and not isinstance(self._on_enter, BaseAction):
                raise Exception("Invalid on_enter argument. Expected BaseAction")

    def get_keyword(self) -> str:
        return self.keyword

    def get_name(self) -> str:
        return self.name

    def get_icon(self) -> Optional[str]:
        return self.icon

    def get_highlightable_input(self, query: Query):
        if self.keyword and self.keyword == query.keyword:
            return query.argument
        return str(query)

    # pylint: disable=unused-argument
    def get_description(self, query: Query) -> str:
        return self.description

    def on_enter(self, query: Query) -> Optional[BaseAction]:
        """
        Handle the main action
        """
        if isinstance(self._on_enter, BaseAction):  # For extensions
            return self._on_enter
        return self._on_enter(query) if callable(self._on_enter) else None

    def on_alt_enter(self, query: Query) -> Optional[BaseAction]:
        """
        Handle the optional secondary action (alt+enter)
        """
        if isinstance(self._on_alt_enter, BaseAction):  # For extensions
            return self._on_alt_enter
        return self._on_alt_enter(query) if callable(self._on_alt_enter) else None

    def get_searchable_fields(self):
        return [(self.name, 1), (self.description, 0.8)]

    def search_score(self, query):
        if not self.searchable:
            return 0
        return max(get_score(query, field) * weight for field, weight in self.get_searchable_fields() if field)
