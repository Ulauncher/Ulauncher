from __future__ import annotations

import math
from typing import Any, Callable

from gi.repository import GLib


class TimerContext:
    """A utility class to hold the context for the timer() function."""

    source: GLib.Source | None
    repeat: bool
    func: Callable[[], None]

    def __init__(self, source: GLib.Source, func: Callable[[], None], repeat: bool = False) -> None:
        self.source = source
        self.repeat = repeat
        self.func = func
        self.source.set_callback(self.trigger)
        self.source.attach(None)

    def cancel(self) -> None:
        if self.source:
            self.source.destroy()
            self.source = None

    def trigger(self, *_args: Any) -> bool:
        self.func()
        return self.repeat


def timer(delay_sec: float, func: Callable[[], None], repeat: bool = False) -> TimerContext:
    """
    Executes the given function after a delay given in seconds. Repeats every delay_sec if
    repeat==True. The function is executed in the context of the GLib MainContext thread.

    func is not called with any arguments, so to call with custom arguments use functools.partial,
    such as `timer(0.5, partial(myfunc, myarg1, myarg2))`.

    To cancel the timer, call `.cancel()` on the returned object.

    """
    frac, _ = math.modf(delay_sec)
    source = (
        GLib.timeout_source_new_seconds(int(delay_sec))
        if frac == 0
        else GLib.timeout_source_new(int(delay_sec * 1000.0))
    )

    return TimerContext(source, func, repeat)
