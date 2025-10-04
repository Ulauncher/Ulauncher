from __future__ import annotations

from threading import Timer
from typing import Callable


def timer(delay_sec: float, func: Callable[[], None]) -> Timer:
    """
    Executes the given function after a delay given in seconds.
    The function is executed in a separate thread.

    func is not called with any arguments, so to call with custom arguments use functools.partial,
    such as `timer(0.5, partial(myfunc, myarg1, myarg2))`.

    To cancel the timer, call `.cancel()` on the returned object.

    """
    timer = Timer(delay_sec, func)
    timer.start()
    return timer
