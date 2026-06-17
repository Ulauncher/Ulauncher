from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ulauncher.gi import GLib

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")


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


def timer(delay_sec: float, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> Context:
    """
    Runs func once after delay_sec seconds, in the GLib main thread.

    func is called with the provided positional and keyword arguments. For example:
        timer(0.5, myfunc, arg1, arg2, kw=val)

    Returns a Context with a .cancel() method.
    """
    return Context(GLib.timeout_source_new(int(delay_sec * 1000)), func, False, args, kwargs)


def interval(delay_sec: float, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> Context:
    """
    Runs func every delay_sec seconds, in the GLib main thread.

    func is called with the provided positional and keyword arguments. For example:
        interval(0.5, myfunc, arg1, arg2, kw=val)

    Returns a Context with a .cancel() method.
    """
    return Context(GLib.timeout_source_new(int(delay_sec * 1000)), func, True, args, kwargs)


def run_when_idle(func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> Context:
    """
    Runs func when the GLib main loop is idle, in the GLib main thread.

    func is called with the provided positional and keyword arguments. For example:
        run_when_idle(myfunc, arg1, arg2, kw=val)

    Returns a Context with a .cancel() method.
    """
    return Context(GLib.idle_source_new(), func, False, args, kwargs)
