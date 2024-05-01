from functools import wraps
from threading import Thread
from typing import Any, Callable


def run_async(func: Callable[..., Any]) -> Callable[..., Thread]:
    """
    Function decorator, intended to make a callable run in a separate thread (asynchronously).
    We still need this because asyncio is absolutely garbage when you want to know
    something will run to completion, but don't want to await it from the main thread

    Example:

    >>> @run_async
    >>> def task():
    >>>     do_something
    >>>
    >>> t = task()
    >>> ...
    >>> t.join()  # (await)
    """

    @wraps(func)
    def async_func(*args: Any, **kwargs: Any) -> Thread:
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return async_func
