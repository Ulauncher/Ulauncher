from __future__ import annotations

from abc import ABCMeta
from typing import Any

# Store singleton instances with proper type tracking to prevent type confusion
_instances: dict[type, Any] = {}


def get_instance(supercls: Any, cls: Any, *args: Any, **kwargs: Any) -> Any:
    # Only create instance if it doesn't exist to ensure true singleton behavior
    if cls not in _instances:
        _instances[cls] = supercls.__call__(*args, **kwargs)
    return _instances[cls]


# Use with metaclass=Singleton (not possible when inheriting from Gtk classes for example)
class Singleton(ABCMeta):
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        return get_instance(super(), cls, *args, **kwargs)
