from __future__ import annotations

import os
from typing import Any

from ulauncher.api.shared.query import Query
from ulauncher.utils.basedataclass import BaseDataClass
from ulauncher.utils.fuzzy_search import get_score

DEFAULT_ACTION = True  #  keep window open and do nothing


class Result(BaseDataClass):
    compact = False
    highlightable = False
    searchable = False
    name = ""
    description = ""
    keyword = ""
    icon = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # This part only runs when initialized from an extensions
        ext_path = os.environ.get("EXTENSION_PATH")
        env_icon = os.environ.get("EXTENSION_ICON")
        if ext_path:
            if not self.icon and env_icon:
                self.icon = env_icon
            if self.icon and os.path.isfile(f"{ext_path}/{self.icon}"):
                self.icon = f"{ext_path}/{self.icon}"

    def __setitem__(self, key, value):
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
        if self.keyword and self.keyword == query.keyword:
            return query.argument
        return str(query)

    def get_description(self, _query: Query) -> str:
        return self.description

    def on_activation(self, query: Query, alt: bool = False) -> Any:
        """
        Handle the main action
        """
        handler = getattr(self, "on_alt_enter" if alt else "on_enter", DEFAULT_ACTION)
        return handler(query) if callable(handler) else handler

    def get_searchable_fields(self):
        return [(self.name, 1), (self.description, 0.8)]

    def search_score(self, query):
        if not self.searchable:
            return 0
        return max(get_score(query, field) * weight for field, weight in self.get_searchable_fields() if field)
