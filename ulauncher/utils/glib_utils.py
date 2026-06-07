from __future__ import annotations

from typing import Any, Callable, Literal

from ulauncher.data.base_data_class import BaseDataClass
from ulauncher.gi import GLib


def _run_once(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Callable[[], bool]:
    """GLib scheduler helper to force single invocation"""

    def run() -> Literal[False]:
        func(*args, **kwargs)
        return False

    return run


class SchedulerContext(BaseDataClass):
    """GLib scheduler source handle, providing an idempotent cancel method."""

    source_id: int | None = None

    def __init__(self, source_id: int) -> None:
        super().__init__()
        self.source_id = source_id

    def cancel(self) -> None:
        if self.source_id is not None:
            GLib.source_remove(self.source_id)
            self.source_id = None


def timer(delay_sec: float, func: Callable[..., Any], *args: Any, **kwargs: Any) -> SchedulerContext:
    """
    Runs func once after delay_sec seconds, in the GLib main thread.

    func is called with the provided positional and keyword arguments. For example:
        timer(0.5, myfunc, arg1, arg2, kw=val)

    Returns a SchedulerContext with a .cancel() method.
    """
    source_id = GLib.timeout_add(round(delay_sec * 1000), _run_once(func, *args, **kwargs))
    return SchedulerContext(source_id)


def run_when_idle(func: Callable[..., Any], *args: Any, **kwargs: Any) -> SchedulerContext:
    """
    Runs func once when the GLib main loop is idle, in the GLib main thread.

    func is called with the provided positional and keyword arguments. For example:
        run_when_idle(myfunc, arg1, arg2, kw=val)

    Returns a SchedulerContext with a .cancel() method.
    """
    source_id = GLib.idle_add(_run_once(func, *args, **kwargs))
    return SchedulerContext(source_id)
