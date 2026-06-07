from __future__ import annotations

from typing import Any, Callable

from ulauncher.gi import GLib


class Context:
    """
    Handle for a scheduled GLib source.

    Cancel it with .cancel(), which is idempotent: GLib.Source.destroy() is safe to call
    repeatedly and after the source has already fired, unlike GLib.source_remove().
    """

    source: GLib.Source | None

    def __init__(
        self, source: GLib.Source, func: Callable[..., Any], repeat: bool, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> None:
        self.source = source
        self._func = func
        self._repeat = repeat
        self._args = args
        self._kwargs = kwargs
        source.set_callback(self._trigger)
        source.attach(None)

    def cancel(self) -> None:
        if self.source:
            self.source.destroy()
            self.source = None

    def _trigger(self, *_args: Any) -> bool:
        if not self.source:
            return False
        keep_alive = False
        try:
            self._func(*self._args, **self._kwargs)
            keep_alive = self._repeat and self.source is not None
        finally:
            if not keep_alive:
                self.source = None
        return keep_alive


def timer(delay_sec: float, func: Callable[..., Any], *args: Any, repeat: bool = False, **kwargs: Any) -> Context:
    """
    Runs func after delay_sec seconds, in the GLib main thread. Repeats every delay_sec if
    repeat is True.

    func is called with the provided positional and keyword arguments. For example:
        timer(0.5, myfunc, arg1, arg2, kw=val)

    Returns a Context with a .cancel() method.
    """
    return Context(GLib.timeout_source_new(int(delay_sec * 1000)), func, repeat, args, kwargs)
