import contextlib
from typing import Any, Callable
from functools import wraps

from ulauncher.utils.timer import timer


def debounce(wait: float) -> Callable[..., Callable[..., None]]:
    """Decorator that will postpone a function
    execution until after wait seconds
    have elapsed since the last time it was invoked."""

    def decorator(fn: Callable[..., None]) -> Callable[..., None]:
        @wraps(fn)
        def debounced(*args: Any, **kwargs: Any) -> None:
            def call_it() -> None:
                fn(*args, **kwargs)

            with contextlib.suppress(AttributeError):
                debounced.t.cancel()  # type: ignore[attr-defined]

            debounced.t = timer(wait, call_it)  # type: ignore[attr-defined]

        return debounced

    return decorator

