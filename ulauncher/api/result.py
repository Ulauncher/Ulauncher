import os

from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.query import Query
from ulauncher.utils.fuzzy_search import get_score


class Result(dict):
    compact = False
    highlightable = False
    searchable = False
    name = ""
    description = ""
    keyword = ""
    icon = ""

    def __init__(self, **kwargs):
        super().__init__()
        # add defaults from parent classes in inheritance order
        for cls in reversed(self.__class__.__mro__):
            if cls in dict.__mro__:
                continue
            defaults = {
                k: v for k, v in vars(cls).items() if (not k.startswith("__") and not callable(getattr(cls, k)))
            }
            self.update(defaults)

        # set values
        self.update(**kwargs)

        # This part only runs when initialized from an extensions
        ext_path = os.environ.get("EXTENSION_PATH")
        if ext_path:
            if not self.icon:
                self.icon = os.environ.get("EXTENSION_ICON")
            if self.icon and os.path.isfile(f"{ext_path}/{self.icon}"):
                self.icon = f"{ext_path}/{self.icon}"

    def __delattr__(self, name):
        del self[name]

    def __dir__(self):  # For IDE autocompletion
        return dir(type(self)) + list(self.keys())

    def __getattribute__(self, key):
        try:
            return self[key]
        except KeyError:
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __setitem__(self, key, value):
        if hasattr(self.__class__, key):
            if key.startswith("__"):
                msg = f'Invalid property "{key}". Must not override class property.'
                raise KeyError(msg)

            class_val = getattr(self.__class__, key)
            if callable(class_val):
                msg = f'Invalid property "{key}". Must not override class method.'
                raise KeyError(msg)
            if not isinstance(value, type(class_val)):
                msg = f'"{key}" must be of type {type(class_val).__name__}, {type(value).__name__} given.'
                raise KeyError(msg)
        if key in ["on_enter", "on_alt_enter"] and not isinstance(value, (bool, str, BaseAction)):
            msg = f"Invalid {key} argument. Expected bool, string or BaseAction"
            raise KeyError(msg)

        super().__setitem__(key, value)

    # Make sure everything flows through __setitem__
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def get_highlightable_input(self, query: Query):
        if self.keyword and self.keyword == query.keyword:
            return query.argument
        return str(query)

    # pylint: disable=unused-argument
    def get_description(self, _query: Query) -> str:
        return self.description

    def on_activation(self, query: Query, alt=False):
        """
        Handle the main action
        """
        handler = self.on_alt_enter if alt else self.on_enter
        if isinstance(handler, (bool, str, BaseAction)):  # For extensions
            return handler
        return handler(query) if callable(handler) else None

    def get_searchable_fields(self):
        return [(self.name, 1), (self.description, 0.8)]

    def search_score(self, query):
        if not self.searchable:
            return 0
        return max(get_score(query, field) * weight for field, weight in self.get_searchable_fields() if field)
