from __future__ import annotations

from collections import defaultdict
from functools import wraps
from typing import Any, Callable

_listeners: dict[str, set[Callable[..., Any]]] = defaultdict(set)


class EventBus:
    namespace: str | None = None
    self_arg: Any = None

    def __init__(self, namespace: str | None = None) -> None:
        # namespace is only used for on
        self.namespace = namespace

    def set_self(self, self_arg: Any) -> None:
        self.self_arg = self_arg

    def _full_event_name(self, event_name: str) -> str:
        return ":".join(filter(None, (self.namespace, event_name)))

    def on(self, listener: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(listener)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            if self.self_arg:
                args = (self.self_arg, *args)
            listener(*args, **kwargs)

        _listeners[self._full_event_name(listener.__name__)].add(wrapper)
        # return the original listener so the class method works as normal
        return listener

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        for listener in _listeners[event_name]:
            listener(*args, **kwargs)
