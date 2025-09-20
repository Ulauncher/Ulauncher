from __future__ import annotations

import threading
from typing import Callable


class TimerContext:
    """A utility class to hold the context for the timer() function."""

    _timer: threading.Timer | None
    func: Callable[[], None]

    def __init__(self, delay_sec: float, func: Callable[[], None]) -> None:
        self.func = func
        self._timer = threading.Timer(delay_sec, self.func)
        self._timer.start()

    def cancel(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None


def timer(delay_sec: float, func: Callable[[], None]) -> TimerContext:
    """
    Executes the given function after a delay given in seconds.
    The function is executed in a separate thread.

    func is not called with any arguments, so to call with custom arguments use functools.partial,
    such as `timer(0.5, partial(myfunc, myarg1, myarg2))`.

    To cancel the timer, call `.cancel()` on the returned object.

    """
    return TimerContext(delay_sec, func)
